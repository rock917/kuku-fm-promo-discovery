# Kuku FM — AI Promo Discovery System
## Solution Document · Problem 1: Find the Promos

---

### 1. Problem Selection & Reasoning

**Chosen Problem:** Problem 1 — Find the Promos

Promo discovery is the highest-leverage task in content distribution: a 30-second clip that lands on the right viewer converts cold traffic into paying subscribers. Getting it right requires genuine narrative understanding — not keyword matching — making it an ideal showcase for AI-augmented reasoning combined with deterministic safety checks.

---

### 2. Assumptions

| Assumption | Rationale |
|---|---|
| Timestamps are **scene-relative** (each scene resets to `00:00.00`) | Verified across all 50 episodes — multi-scene episodes all restart the clock |
| A single scene can be both a promo in its entirety or windowed (first-45s, last-45s, SFX-anchor) | Most scenes are 1–3 minutes; windowing extracts the strongest sub-segments |
| SFX labels like `CLIFFHANGER SFX` are **producer hints**, not narrative verdicts | The LLM must assess actual dialogue and situation before awarding cliffhanger score |
| Mock LLM scores are heuristic | Real Gemini/OpenAI scores are required for submission-quality recommendations |
| Verbatim quote hallucination check: only text in `"…"` with 10+ chars is verified against source | Descriptive paraphrases from the LLM cannot be substring-matched meaningfully |

---

### 3. Architecture & Workflow

```
Raw .txt screenplays (50 episodes)
   │
   ▼ parser.py        — extracts episodes, scenes, events, scene-relative timestamps
   │
   ▼ analyzer.py      — generates candidate windows (full-scene / first-45s / last-45s / SFX-anchor)
   │                    sends each to LLM with explicit rubric
   ▼ llm_client.py    — Mock | Gemini | OpenAI  +  file-based response cache
   │
   ▼ validator.py     — deterministic Python checks (no LLM):
   │                    duration 20–60s · timestamps exist in source · no hallucinated quotes
   │                    no cross-scene contamination · duplicate/overlap detection
   ▼ scorer.py        — 5-dimension weighted score (see below)
   │
   ▼ reporter.py      — promos.json · promos.csv · quality_report.json · failure_analysis.json
   │
   ▼ app.py           — Streamlit UI: browse, filter, trace, export, re-run
```

**LLM provider is fully swappable** via `config/config.yaml` — no source code changes needed to switch between Mock, Gemini, or OpenAI.

---

### 4. Scoring Mechanism (5 Dimensions, Explainable)

| Dimension | Weight | Source |
|---|---|---|
| Hook Strength — does the opening 3 seconds grab attention? | **25%** | ⚡ AI-generated |
| Cliffhanger Strength — does it end unresolved, creating desire to continue? | **30%** | ⚡ AI-generated |
| Standalone Clarity — can a new viewer understand the situation? | **20%** | ⚡ AI-generated |
| Emotional Impact — does it produce a visceral emotional response? | **15%** | ⚡ AI-generated |
| Duration Quality — is the length in the ideal 25–45s range? | **10%** | 🔒 Programmatic |

AI-generated scores are **clearly labelled** in both JSON output and the UI. Programmatic scores (duration) are computed entirely in Python with no LLM involvement. The distinction is preserved throughout the pipeline.

---

### 5. AI vs Rule-Based Code Breakdown

| Component | Approach |
|---|---|
| Screenplay parsing | Rule-based (regex + state machine) |
| Candidate window generation | Rule-based (scene duration + SFX anchors) |
| Narrative quality scoring (hook, cliffhanger, standalone, emotional) | LLM |
| Duration validation and scoring | Programmatic (Python) |
| Timestamp existence verification | Programmatic (±0.5s tolerance) |
| Hallucination detection | Programmatic (regex: quoted phrases only) |
| Duplicate/overlap detection | Programmatic (60% overlap threshold) |
| Resolved-ending detection | Programmatic (regex pattern list) |
| Output writing (JSON, CSV) | Programmatic |

**~65% of logic is deterministic Python. ~35% is LLM reasoning.**

---

### 6. Scalability to New Shows

**Zero source code changes required.** To run on a new microdrama:

1. Place `.txt` episode files in `data/scripts/<show-name>/`
2. Update `config/config.yaml` → `data.scripts_dir`
3. Run `python src/pipeline.py --provider gemini`

The parser auto-detects episode numbers, scene boundaries, event types, and timestamp formats.

---

### 7. Quality Evaluation Methodology

**Validation checks (programmatic — not AI):**
- Duration: 20–60s (hard disqualifier)
- Timestamps: start and end must exist in source screenplay ±0.5s
- Hallucination: quoted verbatim dialogue must appear in source
- Cross-scene contamination: segments from different scenes cannot share a timestamp range
- Duplicates: candidates with ≥60% temporal overlap are merged (keep higher score)

**Quality report** (`quality_report.json`) contains:
- Candidate counts at each pipeline stage
- Failure type breakdown with counts
- Full list of invalid candidates with reasons
- Duplicate pair details

---

### 8. Limitations & Failure Cases

> *Per assignment requirements, this section is intentionally honest.*

| Limitation | Impact | Mitigation |
|---|---|---|
| Mock LLM scores are heuristic (no real understanding) | All 20 ranked promos scored identically in mock mode | Use `--provider gemini` for real analysis |
| Short scenes (<20s) produce zero candidates | Episodes 39, 44 have short sub-scenes skipped | Acceptable; these rarely make good promos |
| Duplicate window generation | 133 of 218 candidates flagged as overlapping duplicates | Deduplication is automatic; unique candidates still represent all 50 episodes |
| SFX labels `CLIFFHANGER SFX` over-counted before fix | Early iterations gave full cliffhanger score to SFX lines | Fixed: LLM prompt explicitly deprioritises SFX labels; they are supporting signals only |
| Multi-scene timestamp display | Promos from multiple scenes have separate timestamp ranges per scene — cannot be expressed as a single `00:00.00–00:30.00` range | Each segment has its own `episode_number + scene_number + start_ts + end_ts` |

**Documented AI mistake:** During development, the hallucination validator initially checked whether the entire LLM-generated description text was a substring of the source screenplay. This incorrectly rejected every candidate (218/218) because the LLM writes descriptive paraphrases like *"Opening moment creates immediate tension"*, which are not literal screenplay text. Fix: only perform substring check when the LLM uses verbatim quoted dialogue (`"…"`).

---

### 9. AI Tools Used

- **Google Gemini** (via Antigravity/Gemini API) — primary LLM provider for screenplay analysis
- **OpenAI GPT-4o-mini** — optional fallback provider
- **Antigravity AI Assistant** — used throughout development for code generation, debugging, and architecture review

---

### 10. Deliverables Summary

| Deliverable | Location | Status |
|---|---|---|
| Solution document | `solution_document.md` (this file) | ✅ |
| Working prototype (source code) | `src/` | ✅ |
| Raw outputs — promos.json | `outputs/promos.json` | ✅ |
| Raw outputs — promos.csv | `outputs/promos.csv` | ✅ |
| Quality report | `outputs/quality_report.json` | ✅ |
| Failure analysis | `outputs/failure_analysis.json` | ✅ |
| Streamlit UI | `src/app.py` → `streamlit run src/app.py` | ✅ |
| README | `README.md` | ✅ |
| Real LLM run (Gemini) | Requires `GEMINI_API_KEY` | ⏳ Pending API key |
