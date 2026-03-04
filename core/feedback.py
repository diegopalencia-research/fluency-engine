"""
core/feedback.py
Finishing School protocol corrective feedback via Groq.

The Finishing School (FS) protocol delivers corrections at four levels:
  L1 — Phonetic / word-level correction
  L2 — Grammar correction (targeted to error memory)
  L3 — Discourse connector gap report
  L4 — Narrative coaching paragraph (holistic)

All corrections are explicit — the learner sees original → corrected → repeat prompt.
Grounded in Long (1996) Interaction Hypothesis and Schmidt (1990) Noticing Hypothesis.
"""

import json
import re


# ── System prompt ─────────────────────────────────────────────────────────────
_FS_SYSTEM = """You are an expert English language coach delivering corrections in the
Finishing School protocol format. You give precise, respectful, constructive feedback.

Rules:
- Never be harsh or discouraging.
- Always show: [original] → [corrected] → repeat prompt.
- Focus on the 3–6 most important errors, not every mistake.
- Grammar corrections must name the rule briefly (e.g. "third-person -s").
- Connector feedback must name the missing type and give one example.
- Narrative coaching must be 2–3 sentences: overall impression + one key strength + one priority to improve.
- Return ONLY valid JSON, no preamble, no markdown fences."""


def _build_correction_prompt(
    transcript: str,
    scenario: dict,
    analysis: dict,
    level: str,
    error_memory: dict
) -> str:
    # Summarise what the analysis found
    wpm         = analysis.get("wpm", 0)
    filler_data = analysis.get("filler_data", {})
    filler_by_type = filler_data.get("by_type", {})
    filler_summary = ", ".join(
        f'"{v["label"]}" ×{v["count"]}' for v in filler_by_type.values()
    ) or "none detected"

    connector_data = analysis.get("connector_data", {})
    used_types   = list(connector_data.get("found", {}).keys())
    missing_types = connector_data.get("missing_types", [])

    # Priority grammar patterns from error memory
    known_errors = error_memory.get("grammar_errors", {})
    top_known    = sorted(known_errors.items(), key=lambda x: -x[1])[:3] if known_errors else []
    known_str    = ", ".join(e[0] for e in top_known) if top_known else "none recorded"

    evaluation_focus = scenario.get("evaluation_focus", "general accuracy and fluency")
    target_structure = scenario.get("target_structure", "")
    scenario_prompt  = scenario.get("prompt", "")

    return f"""CEFR LEVEL: {level}
SCENARIO: {scenario_prompt}
TARGET STRUCTURE: {target_structure}
EVALUATION FOCUS: {evaluation_focus}

TRANSCRIPT:
\"\"\"{transcript}\"\"\"

ACOUSTIC DATA:
- WPM: {wpm}
- Fillers detected: {filler_summary}
- Connector types used: {', '.join(used_types) or 'none'}
- Connector types missing: {', '.join(missing_types[:4]) or 'none'}

KNOWN ERROR PATTERNS (from learner history):
- {known_str}

Return ONLY this JSON:
{{
  "sentence_corrections": [
    {{
      "original": "exact phrase from transcript that contains the error",
      "corrected": "the improved version",
      "rule": "brief rule name (e.g. past simple irregular, third-person -s)",
      "repeat_prompt": "Please say: [corrected version]"
    }}
  ],
  "connector_feedback": {{
    "types_used": {json.dumps(used_types)},
    "strongest_missing": "the most important missing connector type for this level",
    "example_sentence": "A sentence the learner could have used with that connector"
  }},
  "filler_feedback": {{
    "worst_offender": "the most frequent filler word or phrase, or empty string if none",
    "replacement_tip": "a concrete alternative phrase or technique to replace it"
  }},
  "narrative_coaching": "2–3 sentence holistic coaching paragraph. Include: overall impression, one key strength, one specific priority.",
  "grammar_patterns_found": ["list", "of", "grammar", "error", "pattern", "names"],
  "task_relevance": "brief assessment of whether the response addressed the scenario (1 sentence)"
}}"""


# ── Main entry ─────────────────────────────────────────────────────────────────
def generate_corrections(
    transcript: str,
    scenario: dict,
    analysis: dict,
    level: str,
    groq_api_key: str,
    error_memory: dict = None
) -> dict:
    """
    Run the Finishing School protocol via Groq.

    Returns:
        sentence_corrections:  list of {original, corrected, rule, repeat_prompt}
        connector_feedback:    dict
        filler_feedback:       dict
        narrative_coaching:    str
        grammar_patterns_found: list[str]
        task_relevance:        str
        error:                 str | None
    """
    from groq import Groq

    error_memory = error_memory or {}

    # Add connector data to analysis if not present
    if "connector_data" not in analysis and transcript:
        from core.score import detect_connectors
        analysis["connector_data"] = detect_connectors(transcript)

    empty = {
        "sentence_corrections":   [],
        "connector_feedback":     {},
        "filler_feedback":        {},
        "narrative_coaching":     "",
        "grammar_patterns_found": [],
        "task_relevance":         "",
        "error":                  None
    }

    if not transcript.strip():
        empty["error"] = "No transcript to analyse."
        return empty

    prompt = _build_correction_prompt(transcript, scenario, analysis, level, error_memory)

    try:
        client   = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _FS_SYSTEM},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = raw.rstrip("`").strip()

        result = json.loads(raw)

        # Ensure all keys exist
        result.setdefault("sentence_corrections",   [])
        result.setdefault("connector_feedback",     {})
        result.setdefault("filler_feedback",        {})
        result.setdefault("narrative_coaching",     "")
        result.setdefault("grammar_patterns_found", [])
        result.setdefault("task_relevance",         "")
        result["error"] = None

        return result

    except json.JSONDecodeError as e:
        empty["error"] = f"Groq returned invalid JSON: {e}"
        return empty
    except Exception as e:
        empty["error"] = str(e)
        return empty
