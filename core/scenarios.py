"""
core/scenarios.py
CEFR-calibrated scenario generation via Groq (Llama-3.3-70b).

Every scenario is personalised using the learner's error memory.
Output is always a validated JSON dict — never raw prose.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# ── Scenario catalogue ────────────────────────────────────────────────────────
SCENARIO_TYPES = {
    "free_response":      {"label": "Free Response",         "min_level": "A1", "seconds": 30},
    "narrative":          {"label": "Narrative",             "min_level": "A2", "seconds": 60},
    "retell":             {"label": "Retell",                "min_level": "A2", "seconds": 60},
    "opinion":            {"label": "Opinion",               "min_level": "B1", "seconds": 60},
    "problem_solve":      {"label": "Problem Solving",       "min_level": "B1", "seconds": 60},
    "comparison":         {"label": "Comparison",            "min_level": "B2", "seconds": 75},
    "instruction_follow": {"label": "Instruction Following", "min_level": "A2", "seconds": 45},
    "debate_opener":      {"label": "Debate Opener",         "min_level": "B2", "seconds": 60},
}

TOPIC_DOMAINS = [
    "Daily Routines & Habits",
    "Work & Professional Communication",
    "Technology & Social Media",
    "Health & Lifestyle",
    "Travel & Culture",
    "Problem Solving & Decision Making",
    "Education & Learning",
    "Environment & Society",
    "Identity & Personal Values",
    "Abstract Ideas & Philosophy",  # C1/C2 only
]

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _available_types(level: str) -> list:
    """Return scenario types available at or below the given CEFR level."""
    idx = LEVEL_ORDER.index(level) if level in LEVEL_ORDER else 2
    return [k for k, v in SCENARIO_TYPES.items()
            if LEVEL_ORDER.index(v["min_level"]) <= idx]


def _available_topics(level: str) -> list:
    """Filter out abstract topics for lower levels."""
    topics = TOPIC_DOMAINS.copy()
    if level in ("A1", "A2", "B1"):
        topics = [t for t in topics if "Abstract" not in t]
    return topics


def _build_system_prompt() -> str:
    return (
        "You are a scenario generator for an adaptive English fluency training platform. "
        "You generate practice scenarios for non-native English speakers. "
        "Always output ONLY a valid JSON object — no markdown, no preamble, no explanation. "
        "The JSON must exactly match the requested schema."
    )


def _build_user_prompt(level: str, scenario_type: str, topic: str,
                       grammar_focus: str, connector_focus: str,
                       duration_seconds: int, error_memory: dict) -> str:
    weaknesses = ""
    if error_memory:
        grammar_errors = error_memory.get("grammar_errors", {})
        missing_conn   = error_memory.get("missing_connectors", [])
        habitual_fill  = error_memory.get("habitual_fillers", {})
        wpm_trend      = error_memory.get("wpm_trend", "stable")

        parts = []
        if grammar_errors:
            top_errors = sorted(grammar_errors.items(), key=lambda x: -x[1])[:3]
            parts.append(f"Grammar errors to target: {', '.join(e[0] for e in top_errors)}")
        if missing_conn:
            parts.append(f"Missing connector types: {', '.join(missing_conn[:3])}")
        if habitual_fill:
            top_fill = sorted(habitual_fill.items(), key=lambda x: -x[1])[:2]
            parts.append(f"Habitual fillers to reduce: {', '.join(f[0] for f in top_fill)}")
        if wpm_trend == "declining":
            parts.append("WPM is declining — generate a scenario that encourages fluid narrative speech.")

        if parts:
            weaknesses = "\n\nLEARNER WEAKNESSES (personalise the scenario to target these):\n" + "\n".join(f"- {p}" for p in parts)

    return f"""Generate one English speaking practice scenario.

LEARNER LEVEL: {level} (CEFR)
SCENARIO TYPE: {scenario_type}
TOPIC DOMAIN: {topic}
PRIMARY GRAMMAR FOCUS: {grammar_focus}
CONNECTOR FOCUS: {connector_focus}
DURATION TARGET: {duration_seconds} seconds of spoken response{weaknesses}

Return ONLY this JSON object (no other text):
{{
  "prompt": "The exact question or instruction shown to the learner (1–3 sentences, clear and engaging)",
  "context": "Brief situational context if helpful (1–2 sentences, or empty string)",
  "target_structure": "The specific grammar or discourse feature being practised",
  "example_opener": "A strong first sentence the learner could use to begin their response",
  "vocabulary_hints": ["word_or_phrase_1", "word_or_phrase_2", "word_or_phrase_3"],
  "evaluation_focus": "What the AI corrector should prioritise when giving feedback",
  "scenario_type": "{scenario_type}",
  "level": "{level}",
  "duration_seconds": {duration_seconds}
}}"""


def generate_scenario(
    level: str,
    groq_api_key: str,
    error_memory: dict = None,
    force_type: str = None
) -> dict:
    """
    Generate a CEFR-calibrated practice scenario via Groq.

    Args:
        level:         CEFR level string (A1–C2)
        groq_api_key:  Groq API key
        error_memory:  Dict from storage.get_error_memory()
        force_type:    Override scenario type selection

    Returns:
        Validated scenario dict, or error dict with "error" key.
    """
    from groq import Groq

    error_memory = error_memory or {}

    # Select scenario type
    available = _available_types(level)
    if force_type and force_type in available:
        stype = force_type
    else:
        stype = random.choice(available)

    topic    = random.choice(_available_topics(level))
    duration = SCENARIO_TYPES[stype]["seconds"]

    # Determine grammar and connector focus
    thresholds = json.loads((DATA_DIR / "cefr_thresholds.json").read_text())
    grammar_targets = thresholds["levels"][level].get("grammar_targets", [])
    grammar_focus   = random.choice(grammar_targets) if grammar_targets else "general accuracy"

    connectors_data = json.loads((DATA_DIR / "connector_taxonomy.json").read_text())
    # Pick a connector type appropriate for this level
    suitable_conn = [
        k for k, v in connectors_data["types"].items()
        if LEVEL_ORDER.index(v["cefr_introduced"]) <= LEVEL_ORDER.index(level)
    ]
    # Prioritise missing connector types from error memory
    missing_conn = error_memory.get("missing_connectors", [])
    priority_conn = [c for c in missing_conn if c in suitable_conn]
    connector_focus = priority_conn[0] if priority_conn else (
        random.choice(suitable_conn) if suitable_conn else "general connectors"
    )

    system_prompt = _build_system_prompt()
    user_prompt   = _build_user_prompt(
        level, stype, topic, grammar_focus, connector_focus, duration, error_memory
    )

    try:
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=0.85,
            max_tokens=600,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
            raw = raw.rstrip("`").strip()

        scenario = json.loads(raw)

        # Validate required keys
        required = ["prompt", "context", "target_structure", "example_opener",
                    "vocabulary_hints", "evaluation_focus"]
        for key in required:
            if key not in scenario:
                scenario[key] = ""

        # Ensure metadata
        scenario.setdefault("scenario_type",     stype)
        scenario.setdefault("scenario_type_label", SCENARIO_TYPES[stype]["label"])
        scenario.setdefault("level",             level)
        scenario.setdefault("duration_seconds",  duration)
        scenario.setdefault("topic",             topic)
        scenario.setdefault("grammar_focus",     grammar_focus)
        scenario.setdefault("connector_focus",   connector_focus)

        return scenario

    except json.JSONDecodeError as e:
        return {"error": f"Groq returned invalid JSON: {e}", "raw": raw}
    except Exception as e:
        return {"error": str(e)}


import re  # needed for markdown fence stripping
