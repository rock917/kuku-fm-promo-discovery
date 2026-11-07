# Kuku FM — Promo Discovery System

> **AI Generalist Assignment — Problem 1: Find the Promos**  
> Automated identification of the best 20–60 second promotional moments from a 50-episode microdrama screenplay.

---

## Quick Start

```bash
# 1. Clone / navigate to the project
cd Kuku_FM_CASE_STUDY

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure an LLM key for real AI analysis
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Run the pipeline (mock mode — no API key needed)
python src/pipeline.py --provider mock --top-n 20

# 5. Launch the Streamlit UI
streamlit run src/app.py
```

---

## Project Structure

```
Kuku_FM_CASE_STUDY/
├── data/
│   └── scripts/
│       └── I Married a Broken Soldier. He was a Duke/   # 50 episode .txt files (READ-ONLY)
├── src/
│   ├── parser.py        # Screenplay parser — extracts episodes, scenes, events, timestamps
│   ├── validator.py     # Deterministic validation (duration, timestamps, hallucination check)
│   ├── llm_client.py    # LLM abstraction (Mock / Gemini / OpenAI) + file-based cache
│   ├── analyzer.py      # Candidate window generation + LLM narrative analysis
│   ├── scorer.py        # 5-dimension weighted scoring + ranking
│   ├── reporter.py      # JSON / CSV / quality report / failure analysis writer
│   ├── pipeline.py      # End-to-end orchestration (CLI entry point)
│   └── app.py           # Streamlit UI
├── config/
│   └── config.yaml      # All paths, scoring weights, validation thresholds
├── tests/
│   └── test_parser.py   # Parser deep-verification test (all 50 episodes)
├── outputs/
│   ├── promos.json          # Ranked promo recommendations
│   ├── promos.csv           # Same data in tabular format
│   ├── quality_report.json  # Candidate counts, failure types, duplicate pairs
│   └── failure_analysis.json # System limitations + individual failure details
├── requirements.txt
├── .env.example
└── README.md
```

---

## Pipeline Architecture

```
Raw .txt screenplays (50 episodes)
        │
        ▼
  [parser.py]  ──── Extracts episodes, scenes, events (CAMERA/DIALOGUE/ACTION/SOUND_FX)
                     Preserves scene-relative timestamps (each scene resets to 00:00.00)
        │
        ▼
  [analyzer.py] ─── Generates candidate windows (full-scene, first-45s, last-45s, SFX-anchor)
                     Sends each window to LLM for narrative scoring
        │
        ▼
  [llm_client.py] ─ Mock / Gemini / OpenAI — file-based response cache
        │
        ▼
  [validator.py] ── Deterministic Python checks (no LLM):
                     • Duration: 20–60 seconds
                     • Timestamps exist in source (±0.5s)
                     • No hallucinated verbatim dialogue
                     • No cross-scene timestamp contamination
                     • Duplicate/overlap detection (60% threshold)
        │
        ▼
  [scorer.py] ───── 5-dimension weighted score:
                     hook(25%) + cliffhanger(30%) + standalone(20%) + emotional(15%) + duration(10%)
                     AI scores labelled ⚡ | Programmatic scores labelled 🔒
        │
        ▼
  [reporter.py] ─── Writes promos.json, promos.csv, quality_report.json, failure_analysis.json
```

---

## CLI Reference

```bash
python src/pipeline.py [OPTIONS]

Options:
  --provider   {mock,gemini,openai}   LLM provider (default: mock)
  --model      MODEL_NAME             Override model (default from config)
  --top-n      N                      Number of promos to rank (default: 20)
  --episodes   EP [EP ...]            Only process these episodes (default: all 50)
  --verbose                           Extra logging
```

**Examples:**

```bash
# Fast mock run (no API key)
python src/pipeline.py --provider mock --top-n 20

# Real Gemini run (requires GEMINI_API_KEY in .env)
python src/pipeline.py --provider gemini --top-n 20

# Process only episodes 1–5 for testing
python src/pipeline.py --provider mock --episodes 1 2 3 4 5

# Run tests
python tests/test_parser.py
```

---

## LLM Provider Configuration

| Provider | Key needed | Cost | Speed |
|---|---|---|---|
| `mock` | None | Free | Instant |
| `gemini` | `GEMINI_API_KEY` | Free tier available | ~2–3s/call |
| `openai` | `OPENAI_API_KEY` | Paid | ~1–2s/call |

Set your key in `.env` (copy from `.env.example`). Never commit `.env` to version control.

---

## Scoring Weights

| Dimension | Weight | Computed by |
|---|---|---|
| Hook Strength | 25% | ⚡ LLM (AI-generated) |
| Cliffhanger Strength | 30% | ⚡ LLM (AI-generated) |
| Standalone Clarity | 20% | ⚡ LLM (AI-generated) |
| Emotional Impact | 15% | ⚡ LLM (AI-generated) |
| Duration Quality | 10% | 🔒 Programmatic |

**Cliffhanger note:** Sound-FX lines containing words like "cliffhanger" or "ominous" are **supporting signals only**. The LLM must assess the actual narrative tension from dialogue and actions.

---

## Timestamp Convention

All timestamps in the output are **scene-relative** — each scene heading resets the clock to `00:00.00`. Never treat timestamps from different scenes as a continuous timeline.

Format: `MM:SS.ss` (minutes : seconds . centiseconds)

Each promo segment explicitly records its `episode_number` and `scene_number` so every recommendation is fully traceable to its source location.

---

## Running on a New Show

This system is config-driven. To analyse a different microdrama:

1. Place screenplay `.txt` files in a new folder inside `data/scripts/`.
2. Update `config/config.yaml` → `data.scripts_dir` to point to the new folder.
3. Run `python src/pipeline.py --provider mock`.

No source code changes are required.

---

## Known Limitations

See `outputs/failure_analysis.json` for the full documented failure analysis. Key limitations:

1. **Mock scores are heuristic** — the mock LLM assigns scores without real understanding.
2. **Duplicate window overlap** — adjacent windows from the same scene share content.
3. **Short scenes produce no candidates** — scenes under 20 seconds are skipped.
4. **Multi-scene promos** — combining segments from different scenes is structurally possible but timestamp display requires careful interpretation.
5. **SFX label ambiguity** — "CLIFFHANGER SFX" labels in source indicate producer intent but are not sufficient alone.
6. **Hallucination detection scope** — only verbatim quoted dialogue (`"..."`) is checked; descriptive paraphrases are trusted.

---

## Tests

```bash
python tests/test_parser.py    # Parser: all 50 episodes, 0 failures expected
python src/validator.py        # Validator: 6 unit tests
python src/scorer.py           # Scorer: 2 unit tests
python src/reporter.py         # Reporter: output file structure test
```

---

## Outputs

| File | Description |
|---|---|
| `outputs/promos.json` | Ranked promo list with full score breakdown and segment traceability |
| `outputs/promos.csv` | Same data in tabular format for spreadsheet review |
| `outputs/quality_report.json` | Candidate counts, failure types, duplicate pairs |
| `outputs/failure_analysis.json` | System limitations + individual invalid candidate details |
| `outputs/cache/` | Cached LLM responses (keyed by content hash) |

---

## Assignment

**Show:** *I Married a Broken Soldier. He was a Duke* (50 episodes)  
**Problem:** Kuku FM AI Generalist Assignment — Problem 1: Find the Promos  
**Requirement:** Identify the best 20–60 second promotional clips with timestamps, scoring, and narrative justification.

