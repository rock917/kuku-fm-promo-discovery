# =============================================================================
# reporter.py — Output Generation and Quality Reporting
#
# Generates:
#   promos.json          — Full structured output (ranked + scored candidates)
#   promos.csv           — Spreadsheet-friendly flat format
#   failure_analysis.json — Validation failures, weak candidates, data quality
#   quality_report.json  — Pipeline-level statistics
#
# Design:
#   - Every output links back to source episode + scene + scene-relative timestamps
#   - AI-generated scores clearly distinguished from programmatic scores
#   - Raw outputs are unedited pipeline outputs (required submission deliverable)
#   - Failure analysis is honest and comprehensive
# =============================================================================

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _candidate_to_dict(candidate, score_breakdown=None) -> dict:
    """Convert a PromoCandidate + ScoreBreakdown to full output dict."""
    segs = []
    for s in candidate.segments:
        segs.append({
            "episode_number": s.episode_number,
            "scene_number":   s.scene_number,
            "scene_heading":  s.scene_heading,
            "start_ts":       s.start_ts,
            "end_ts":         s.end_ts,
            "start_sec":      s.start_sec,
            "end_sec":        s.end_sec,
            "duration_sec":   round(s.end_sec - s.start_sec, 2),
            "timestamp_note": (
                "Scene-relative timestamps. "
                f"Ep{s.episode_number} Sc{s.scene_number} starts at 00:00.00."
            ),
        })

    result = {
        "rank":              candidate.rank,
        "candidate_id":      candidate.candidate_id,
        "final_score":       candidate.final_score,
        "is_valid":          candidate.is_valid,

        # Source traceability
        "episodes":          candidate.episode_numbers,
        "is_multi_episode":  candidate.is_multi_episode,
        "total_duration_sec": round(candidate.total_duration_sec, 2),
        "segments":          segs,

        # Promo content
        "opening_hook": {
            "text":   candidate.opening_hook_text,
            "source": "Verbatim or paraphrased from screenplay",
        },
        "closing_cliffhanger": {
            "text":   candidate.closing_cliffhanger_text,
            "source": "Verbatim or paraphrased from screenplay",
        },
        "narrative_context":    candidate.narrative_context,
        "has_cliffhanger_sfx":  candidate.has_cliffhanger_sfx,
        "cliffhanger_sfx_note": (
            "SOUND FX marker detected near segment end — supporting signal only. "
            "Cliffhanger strength scored on narrative analysis."
        ) if candidate.has_cliffhanger_sfx else None,

        # Validation state (programmatic constraints)
        "validation": {
            "note":     "These checks are PROGRAMMATICALLY ENFORCED — not AI-generated",
            "passed":   candidate.is_valid,
            "failures": candidate.validation_failures,
            "warnings": candidate.validation_warnings,
        },
    }

    # Score breakdown (clearly labelled)
    if score_breakdown:
        result["scoring"] = score_breakdown.to_dict()
    else:
        result["scoring"] = {
            "AI-generated": {
                "hook_strength":        candidate.ai_hook_strength,
                "cliffhanger_strength": candidate.ai_cliffhanger_strength,
                "standalone_clarity":   candidate.ai_standalone_clarity,
                "emotional_impact":     candidate.ai_emotional_impact,
            },
            "final_score": candidate.final_score,
            "note": "Full breakdown not available",
        }

    # AI explanation
    if candidate.ai_explanation:
        result["ai_analysis"] = {
            "explanation": candidate.ai_explanation,
            "note": "AI-generated assessment — verify against source text",
        }

    return result


def _candidate_to_csv_row(candidate, score_breakdown=None) -> dict:
    """Convert a PromoCandidate to a flat CSV row."""
    primary_seg = candidate.segments[0] if candidate.segments else None
    sb = score_breakdown

    return {
        "rank":                    candidate.rank or "",
        "candidate_id":            candidate.candidate_id,
        "final_score":             round(candidate.final_score or 0, 4),
        "is_valid":                candidate.is_valid,
        "primary_episode":         primary_seg.episode_number if primary_seg else "",
        "primary_scene":           primary_seg.scene_number if primary_seg else "",
        "scene_heading":           primary_seg.scene_heading if primary_seg else "",
        "start_ts":                primary_seg.start_ts if primary_seg else "",
        "end_ts":                  primary_seg.end_ts if primary_seg else "",
        "start_sec":               primary_seg.start_sec if primary_seg else "",
        "end_sec":                 primary_seg.end_sec if primary_seg else "",
        "total_duration_sec":      round(candidate.total_duration_sec, 2),
        "num_segments":            len(candidate.segments),
        "is_multi_episode":        candidate.is_multi_episode,
        # AI-generated scores (clearly labelled)
        "AI_hook_strength":        sb.ai_hook_strength if sb else candidate.ai_hook_strength,
        "AI_cliffhanger_strength": sb.ai_cliffhanger_strength if sb else candidate.ai_cliffhanger_strength,
        "AI_standalone_clarity":   sb.ai_standalone_clarity if sb else candidate.ai_standalone_clarity,
        "AI_emotional_impact":     sb.ai_emotional_impact if sb else candidate.ai_emotional_impact,
        # Programmatic score (clearly labelled)
        "PROG_duration_quality":   sb.prog_duration_quality if sb else "",
        "score_confidence":        sb.score_confidence if sb else "unknown",
        # Supporting signal
        "has_cliffhanger_sfx":     candidate.has_cliffhanger_sfx,
        # Content
        "opening_hook_text":       candidate.opening_hook_text[:200],
        "closing_cliffhanger_text": candidate.closing_cliffhanger_text[:200],
        "narrative_context":       candidate.narrative_context[:300],
        # Validation
        "validation_passed":       candidate.is_valid,
        "validation_failures":     "; ".join(candidate.validation_failures),
        "validation_warnings":     "; ".join(candidate.validation_warnings),
        "ai_explanation":          (candidate.ai_explanation or "")[:300],
    }


# ---------------------------------------------------------------------------
# Main report writers
# ---------------------------------------------------------------------------

def write_promos_json(
    ranked_candidates: list,
    all_candidates: list,
    score_breakdowns: list,
    output_path: Path,
    metadata: dict,
) -> None:
    """
    Write the main promos.json output file.
    Contains ranked valid candidates + full metadata.
    """
    sb_map = {sb.candidate_id: sb for sb in score_breakdowns}

    output = {
        "metadata": {
            **metadata,
            "generated_at": datetime.now().isoformat(),
            "total_candidates_generated": len(all_candidates),
            "valid_candidates": len([c for c in all_candidates if c.is_valid]),
            "invalid_candidates": len([c for c in all_candidates if not c.is_valid]),
            "ranked_output_count": len(ranked_candidates),
            "timestamp_format": "MM:SS.ss (scene-relative — resets to 00:00.00 per scene)",
            "score_note": (
                "Scores labelled 'AI-generated' come from LLM analysis. "
                "Scores labelled 'programmatic' are deterministic Python rules. "
                "AI scores should be treated as estimates, not ground truth."
            ),
        },
        "ranked_promos": [
            _candidate_to_dict(c, sb_map.get(c.candidate_id))
            for c in ranked_candidates
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    logger.info(f"Wrote {len(ranked_candidates)} ranked promos to {output_path}")


def write_promos_csv(
    ranked_candidates: list,
    score_breakdowns: list,
    output_path: Path,
) -> None:
    """Write ranked promos to CSV for spreadsheet inspection."""
    sb_map = {sb.candidate_id: sb for sb in score_breakdowns}

    rows = [
        _candidate_to_csv_row(c, sb_map.get(c.candidate_id))
        for c in ranked_candidates
    ]

    if not rows:
        logger.warning("No ranked candidates to write to CSV")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} rows to {output_path}")


def write_failure_analysis(
    all_candidates: list,
    validation_report: dict,
    score_breakdowns: list,
    output_path: Path,
    data_quality_notes: list,
) -> None:
    """
    Write failure_analysis.json — honest documentation of what went wrong.
    Required by assignment: 'limitations and failure cases'.
    """
    sb_map = {sb.candidate_id: sb for sb in score_breakdowns}
    invalid = [c for c in all_candidates if not c.is_valid]
    valid   = [c for c in all_candidates if c.is_valid]

    # Weak but valid candidates (scored in bottom 25%)
    if valid:
        sorted_valid = sorted(valid, key=lambda c: c.final_score or 0)
        weak_threshold = len(sorted_valid) // 4
        weak_candidates = sorted_valid[:weak_threshold]
    else:
        weak_candidates = []

    failure_doc = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_generated":        len(all_candidates),
            "passed_validation":      len(valid),
            "failed_validation":      len(invalid),
            "weak_valid_candidates":  len(weak_candidates),
            "failure_type_counts":    validation_report.get("failure_type_counts", {}),
            "duplicate_pairs":        validation_report.get("duplicates_found", 0),
        },

        "data_quality_notes": data_quality_notes,

        "validation_failures": [
            {
                "candidate_id":  c.candidate_id,
                "episodes":      c.episode_numbers,
                "duration_sec":  round(c.total_duration_sec, 2),
                "failures":      c.validation_failures,
                "warnings":      c.validation_warnings,
                "segments":      [
                    {
                        "ep": s.episode_number, "scene": s.scene_number,
                        "start": s.start_ts, "end": s.end_ts,
                    }
                    for s in c.segments
                ],
            }
            for c in invalid
        ],

        "weak_candidates": [
            {
                "candidate_id":          c.candidate_id,
                "rank":                  c.rank,
                "final_score":           c.final_score,
                "episodes":              c.episode_numbers,
                "ai_hook_strength":      c.ai_hook_strength,
                "ai_cliffhanger_strength": c.ai_cliffhanger_strength,
                "ai_standalone_clarity": c.ai_standalone_clarity,
                "ai_emotional_impact":   c.ai_emotional_impact,
                "explanation":           c.ai_explanation,
            }
            for c in weak_candidates
        ],

        "known_system_limitations": [
            {
                "category": "LLM hallucination risk",
                "description": (
                    "The LLM may describe hook/cliffhanger text that is paraphrased rather than verbatim. "
                    "The validator checks for approximate matches but cannot catch all paraphrasing."
                ),
                "mitigation": "Validator checks key phrases exist in source; full verbatim matching is impractical for natural-language descriptions.",
            },
            {
                "category": "Scene timestamp independence",
                "description": (
                    "Each scene resets timestamps to 00:00.00. Promos referencing Scene 2 of Episode 10 "
                    "cannot be compared directly to Scene 1 of Episode 10 on a shared timeline."
                ),
                "mitigation": "Every output includes scene_number and episode_number alongside timestamps.",
            },
            {
                "category": "Mock LLM scores",
                "description": (
                    "If run without a real API key (provider=mock), all AI-generated scores are "
                    "heuristic placeholders. Outputs are structurally valid but not meaningful for promo selection."
                ),
                "mitigation": "Set LLM_PROVIDER to gemini or openai with a real API key for production runs.",
            },
            {
                "category": "Cliffhanger SFX signal accuracy",
                "description": (
                    "SOUND FX markers containing words like 'cliffhanger' or 'ominous' are detected "
                    "programmatically, but the narrative situation (is it really unresolved?) is "
                    "assessed by LLM and may be wrong."
                ),
                "mitigation": "SFX signals are supporting evidence only. Cliffhanger score requires LLM narrative assessment.",
            },
            {
                "category": "Episode 6 format variant",
                "description": (
                    "Episode 6 uses ALL-CAPS field labels (SCENE HEADING, SCENE START, SCENE END) "
                    "instead of title-case. The parser handles this but it is the only non-standard episode."
                ),
                "mitigation": "Parser auto-detects format; Episode 6 parses correctly with zero warnings.",
            },
            {
                "category": "Episode 22 Scene 1 boundary overlap",
                "description": (
                    "Source data: SOUND FX event ends at 00:42.80 while Scene 1 ends at 00:42.50 "
                    "(0.30s overhang in original screenplay). Parser preserves source values exactly."
                ),
                "mitigation": "Validator uses ±0.5s tolerance for boundary checks.",
            },
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(failure_doc, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    logger.info(f"Wrote failure analysis to {output_path}")


def write_quality_report(
    all_candidates: list,
    ranked_candidates: list,
    validation_report: dict,
    score_breakdowns: list,
    output_path: Path,
    pipeline_metadata: dict,
) -> None:
    """Write a human-readable quality report covering all pipeline metrics."""
    valid   = [c for c in all_candidates if c.is_valid]
    invalid = [c for c in all_candidates if not c.is_valid]

    # Score distribution
    scores = sorted([c.final_score for c in valid if c.final_score is not None], reverse=True)
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    top_score = scores[0] if scores else 0
    min_score = scores[-1] if scores else 0

    # Confidence distribution
    conf_counts = {}
    for sb in score_breakdowns:
        conf_counts[sb.score_confidence] = conf_counts.get(sb.score_confidence, 0) + 1

    # Episodes covered
    ep_counts = {}
    for c in all_candidates:
        for ep in c.episode_numbers:
            ep_counts[ep] = ep_counts.get(ep, 0) + 1
    eps_with_candidates = sorted(ep_counts.keys())

    report = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_metadata": pipeline_metadata,

        "candidate_counts": {
            "total_generated":    len(all_candidates),
            "passed_validation":  len(valid),
            "failed_validation":  len(invalid),
            "ranked_output":      len(ranked_candidates),
            "episodes_processed": pipeline_metadata.get("episodes_processed", "?"),
            "episodes_with_candidates": len(eps_with_candidates),
        },

        "validation_summary": {
            "failure_type_counts":   validation_report.get("failure_type_counts", {}),
            "duplicate_pairs_found": validation_report.get("duplicates_found", 0),
            "timestamp_errors": len([
                c for c in invalid
                if any("TIMESTAMP" in f for f in c.validation_failures)
            ]),
            "hallucination_errors": len([
                c for c in invalid
                if any("HALLUCINATED" in f for f in c.validation_failures)
            ]),
            "duration_errors": len([
                c for c in invalid
                if any("DURATION" in f for f in c.validation_failures)
            ]),
        },

        "score_distribution": {
            "average": avg_score,
            "top":     round(top_score, 4),
            "minimum": round(min_score, 4),
            "count":   len(scores),
            "confidence_distribution": conf_counts,
            "top_10_scores": [round(s, 4) for s in scores[:10]],
        },

        "coverage": {
            "episodes_with_at_least_one_candidate": eps_with_candidates,
            "episodes_with_no_candidates": [
                ep for ep in range(1, 51) if ep not in ep_counts
            ],
        },

        "ai_vs_programmatic_note": (
            "Scores prefixed 'AI_' are LLM-generated estimates (hook, cliffhanger, "
            "standalone, emotional). Scores prefixed 'PROG_' are deterministic Python "
            "rules (duration_quality). Validation pass/fail is always programmatic."
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    logger.info(f"Wrote quality report to {output_path}")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from validator import PromoCandidate, PromoSegment
    from scorer import score_and_rank, ScoreBreakdown

    print("=" * 60)
    print("REPORTER UNIT TEST")
    print("=" * 60)

    out_dir = Path(r"e:\Kuku_FM_CASE_STUDY\outputs")

    def mk(cid, hook, cliff, sa, em, dur, valid=True, failures=None):
        c = PromoCandidate(
            candidate_id=cid,
            segments=[PromoSegment(1, 1, "INT. TEST", "00:10.00", "00:40.00", 10.0, 40.0)],
            opening_hook_text="Test hook text from screenplay.",
            closing_cliffhanger_text="Test cliffhanger text.",
            narrative_context="Test narrative context explaining the promo.",
            has_cliffhanger_sfx=False,
            ai_hook_strength=hook,
            ai_cliffhanger_strength=cliff,
            ai_standalone_clarity=sa,
            ai_emotional_impact=em,
            ai_explanation=f"Test explanation for {cid}.",
        )
        c.total_duration_sec = dur
        c.is_valid = valid
        c.validation_failures = failures or []
        c.validation_warnings = []
        return c

    test_candidates = [
        mk("PROMO_001", 9.0, 9.0, 8.0, 9.0, 32.0),
        mk("PROMO_002", 7.0, 8.0, 7.0, 7.0, 40.0),
        mk("PROMO_003", 5.0, 6.0, 5.0, 5.0, 28.0),
        mk("PROMO_BAD", 3.0, 2.0, 2.0, 2.0, 15.0, valid=False, failures=["DURATION_TOO_SHORT: 15.0s < 20.0s"]),
    ]

    ranked, breakdowns = score_and_rank(test_candidates, top_n=10)
    validation_report = {
        "total_candidates": 4,
        "valid_candidates": 3,
        "invalid_candidates": 1,
        "duplicates_found": 0,
        "failure_type_counts": {"DURATION_TOO_SHORT": 1},
        "duplicate_pairs": [],
        "invalid_candidate_details": [],
    }

    metadata = {
        "show": "Test Show",
        "episodes_processed": 50,
        "llm_provider": "mock",
        "llm_model": "mock",
    }

    # Write all outputs
    write_promos_json(ranked, test_candidates, breakdowns, out_dir / "promos.json", metadata)
    write_promos_csv(ranked, breakdowns, out_dir / "promos.csv")
    write_failure_analysis(test_candidates, validation_report, breakdowns, out_dir / "failure_analysis.json", [])
    write_quality_report(test_candidates, ranked, validation_report, breakdowns, out_dir / "quality_report.json", metadata)

    print(f"\nOutput files written:")
    for fname in ["promos.json", "promos.csv", "failure_analysis.json", "quality_report.json"]:
        p = out_dir / fname
        print(f"  {fname}: {p.stat().st_size} bytes ✓" if p.exists() else f"  {fname}: MISSING ✗")

    # Verify JSON structure
    promos = json.loads((out_dir / "promos.json").read_text())
    print(f"\npromos.json structure:")
    print(f"  Top-level keys: {list(promos.keys())}")
    print(f"  Ranked promos count: {len(promos['ranked_promos'])}")
    if promos['ranked_promos']:
        p = promos['ranked_promos'][0]
        print(f"  First promo keys: {list(p.keys())}")
        print(f"  Scoring sections: {list(p['scoring']['scores'].keys())}")

    print(f"\n✓ Reporter unit test complete.")

