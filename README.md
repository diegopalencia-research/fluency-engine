# 🎙️ FLUENCY ENGINE
### Adaptive Spoken English Training Platform
**Project 04 · Diego Jose Palencia Robles · Palencia Research Portfolio**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

---

> *"The ability to speak a language fluently is not a single skill — it is a system of sub-skills that can be isolated, measured, and trained independently."*  
> — Skehan (1996), adapted

---

## What It Does

Fluency Engine is an adaptive spoken English training platform that generates CEFR-calibrated practice scenarios using Groq AI, records and analyses spoken responses using the same acoustic pipeline as [Project 03 — Speech Fluency Analyzer](https://github.com/diegopalencia-research), delivers sentence-level corrective feedback in **Finishing School protocol** format, and learns from error patterns to personalise every session.

**Core loop:**
```
SCENARIO GENERATED (Groq AI, CEFR-calibrated, infinite variety)
        ↓
LEARNER RECORDS SPOKEN RESPONSE (30–90 seconds)
        ↓
ACOUSTIC ANALYSIS (Whisper + librosa)
        ↓
FINISHING SCHOOL CORRECTIONS (sentence-level, Groq AI)
        ↓
SESSION LOGGED → LEVEL RECALIBRATED → ERROR MEMORY UPDATED
        ↓
REPEAT (infinite, personalised)
```

---

## Research Foundation

Every design decision maps to a published research framework.

| Design Decision | Research Basis |
|---|---|
| Adaptive scenario difficulty | Krashen (1982) — Input Hypothesis (i+1) |
| Corrective feedback format | Long (1996) — Interaction Hypothesis |
| Explicit error marking | Schmidt (1990) — Noticing Hypothesis |
| Speaking-first practice | Swain (1985) — Output Hypothesis |
| CEFR level calibration | Council of Europe (2001) |
| Discourse connector training | Celce-Murcia et al. (2007) |
| Acoustic fluency metrics | Lennon (1990); Skehan (1996); Tavakoli & Skehan (2005) |
| Error spaced repetition | Ebbinghaus (1885) — Forgetting Curve |

**Research sub-question:**
> "Can an adaptive AI-generated scenario system produce measurable improvement in L2 English fluency metrics (WPM, pause rate, filler frequency, discourse connector use) across a series of sessions, calibrated to CEFR level progression?"

---

## CEFR Level System

| Level | Label | WPM Target | Filler Target | Connector Req. | Score |
|---|---|---|---|---|---|
| A1 | Beginner | 60–80 | ≤8/min | None | 30–40 |
| A2 | Elementary | 80–100 | ≤6/min | Sequencing | 40–52 |
| B1 | Intermediate | 100–130 | ≤4/min | + Contrast | 52–65 |
| B2 | Upper-Int. | 130–155 | ≤3/min | 3+ types | 65–76 |
| C1 | Advanced | 155–175 | ≤2/min | 4+ types | 76–88 |
| C2 | Mastery | 160–180 | ≤1.5/min | Full discourse | 88–100 |

Level progression is automatic: 3 consecutive sessions at/above threshold → advance.

---

## Fluency Score Formula

```
Fluency Score = 0.40 × WPM_component
              + 0.30 × Pause_component
              + 0.30 × Filler_component

Each component normalized 0–100 relative to CEFR level thresholds.
```

---

## Technical Stack

| Layer | Tool |
|---|---|
| Frontend | Streamlit |
| Audio recording | audio-recorder-streamlit |
| Transcription | OpenAI Whisper API / local whisper (tiny) |
| Acoustic analysis | librosa · numpy · scipy |
| Scenario generation | Groq / Llama-3.3-70b |
| Correction engine | Groq / Llama-3.3-70b (Finishing School protocol) |
| Session storage | JSON files (username-keyed) |
| PDF reports | reportlab |
| Deployment | Streamlit Cloud |

---

## Project Structure

```
fluency-engine/
├── app.py                        ← Streamlit entry point (5-step session flow)
├── core/
│   ├── analyze.py                ← Audio processing: WPM, pauses, fillers
│   ├── score.py                  ← Fluency formula, connector detection, CEFR assessment
│   ├── feedback.py               ← Finishing School corrections via Groq
│   ├── storage.py                ← Session storage + error memory persistence
│   ├── scenarios.py              ← CEFR-calibrated scenario generation via Groq
│   └── pdf_report.py             ← reportlab branded session PDF
├── data/
│   ├── cefr_thresholds.json      ← Level boundaries, WPM/filler targets, progression rules
│   ├── connector_taxonomy.json   ← 8 connector types with word lists
│   └── filler_patterns.json      ← Regex patterns for 12 filler word categories
├── sessions/                     ← {username}_sessions.json (gitignored)
├── memory/                       ← {username}_memory.json (gitignored)
├── .streamlit/config.toml        ← Theme: navy/blue palette
├── requirements.txt
└── packages.txt                  ← ffmpeg
```

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/diegopalencia-research/fluency-engine.git
cd fluency-engine

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

**API Keys required:**
- **Groq** (free): [console.groq.com](https://console.groq.com) — scenario generation + corrections
- **OpenAI** (optional): Faster Whisper API transcription. Falls back to local whisper if not provided.

Enter keys in the sidebar when the app loads. For permanent setup, create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your-groq-key"
OPENAI_API_KEY = "your-openai-key"  # optional
```

---

## Streamlit Cloud Deployment

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, set `app.py` as entry point
4. Add secrets in the Streamlit Cloud dashboard:
   - `GROQ_API_KEY`
   - `OPENAI_API_KEY` (optional)
5. Deploy

**Note on Streamlit Cloud:** The free tier filesystem is ephemeral — session data resets on redeploy. For persistent storage, replace `core/storage.py` with a database backend (SQLite, Supabase, or similar).

---

## Interview Narrative

> "Fluency Engine is the fourth project in my computational human performance series. Projects 01–03 established feature extraction in phonology, operations, and acoustic speech. Project 04 closes the loop: it wraps the same acoustic pipeline in an adaptive training system that generates infinite CEFR-calibrated scenarios using Groq AI, tracks error patterns across sessions, and delivers corrective feedback in the exact format validated by the Interaction Hypothesis (Long, 1996) and the Noticing Hypothesis (Schmidt, 1990). Every session generates longitudinal data feeding a preprint on L2 fluency development. This is not an app — it is a computational implementation of second-language acquisition theory."

---

## Research Citations

| Citation | Application |
|---|---|
| Krashen, S. (1982). *Principles and Practice in SLA* | Scenario difficulty calibration (i+1) |
| Long, M. (1996). The role of the linguistic environment | Corrective feedback format |
| Schmidt, R. (1990). The role of consciousness in SLA | Explicit error marking |
| Swain, M. (1985). Communicative competence | Speaking-first practice |
| Council of Europe (2001). *Common European Framework* | CEFR level system |
| Celce-Murcia, M. et al. (2007). *Teaching English as a Second Language* | Connector taxonomy |
| Lennon, P. (1990). Investigating fluency in EFL | WPM and pause norms |
| Skehan, P. (1996). A framework for task-based instruction | Fluency measurement framework |
| Ebbinghaus, H. (1885). *Über das Gedächtnis* | Error memory persistence logic |

---

## Part of the Palencia Research Portfolio

```
P01 — NLP Verb Engine          → Phonological feature extraction
P02 — Call Center Dashboard    → Operational feature extraction
P03 — Speech Fluency Analyzer  → Acoustic fluency measurement
P04 — FLUENCY ENGINE           → L2 training loop (closes the arc)
P05 — Circadian Predictor      → Chronobiological optimization
```

**Unified research question:** Can computational features extracted from phonological, operational, acoustic, and chronobiological data predict and improve human performance outcomes?

---

**Diego Jose Palencia Robles** · Independent Researcher  
`github.com/diegopalencia-research` · Guatemala City, Guatemala · 2025  
*Computational Feature Extraction for Human Performance Prediction*
