# =============================================================================
# scorer.py — Five-Dimensional Weighted Scoring and Ranking
#
# Scoring dimensions (per assignment requirements):
#   hook_strength      : 25%  (AI-generated, 1-10)
#   cliffhanger_strength: 30%  (AI-generated, 1-10)
#   standalone_clarity : 20%  (AI-generated, 1-10)
#   emotional_impact   : 15%  (AI-generated, 1-10)
#   duration_quality   : 10%  (programmatic rule, 1-10)
#
# Design:
#   - AI scores are CLEARLY LABELLED as AI-generated
#   - duration_quality is CLEARLY LABELLED as programmatically computed
#   - Final score = weighted average of all five dimensions (0–10 scale)
#   - SFX cliffhanger signal adds a small bonus (not a primary driver)
#   - Only valid candidates are ranked; invalid ones get score = 0
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Score weights (must sum to 1.0)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "hook_strength":        0.25,
    "cliffhanger_strength": 0.30,
    "standalone_clarity":   0.20,
    "emotional_impact":     0.15,
    "duration_quality":     0.10,
}

# ---------------------------------------------------------------------------
# Duration quality scoring (programmatic — deterministic)
# ---------------------------------------------------------------------------

def _score_duration(
    duration_sec: float,
    ideal_min: float = 25.0,
    ideal_max: float = 45.0,
    hard_min: float = 20.0,
    hard_max: float = 60.0,
) -> float:
    """
    Programmatic duration quality score (1–10).
    
    Scoring:
      In ideal range [25–45s]  → 10
      Near ideal boundaries    → linear decay to 7
      Hard limits [20s, 60s]   → 5 at exact boundary
      Outside hard limits      → 1 (should have been filtered by validator)
    
    This score is PROGRAMMATICALLY COMPUTED — not AI-generated.
    """
    d = duration_sec

    # Outside hard limits (shouldn't reach here after validation)
    if d < hard_min or d > hard_max:
        return 1.0

    # Perfect range
    if ideal_min <= d <= ideal_max:
        return 10.0

    # Below ideal (between hard_min and ideal_min)
    if d < ideal_min:
        # Linear: hard_min → 5.0, ideal_min → 10.0
        ratio = (d - hard_min) / (ideal_min - hard_min)
        return round(5.0 + ratio * 5.0, 2)

    # Above ideal (between ideal_max and hard_max)
    # Linear: ideal_max → 10.0, hard_max → 5.0
    ratio = (d - ideal_max) / (hard_max - ideal_max)
    return round(10.0 - ratio * 5.0, 2)


# ---------------------------------------------------------------------------
# Score breakdown dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoreBreakdown:
    """
    Complete scoring breakdown for one promo candidate.
    Clearly separates AI-generated scores from programmatic scores.
    """
    candidate_id: str

    # --- AI-GENERATED SCORES (from LLM) ---
    ai_hook_strength: float           # 1–10
    ai_cliffhanger_strength: float    # 1–10
    ai_standalone_clarity: float      # 1–10
    ai_emotional_impact: float        # 1–10

    # --- PROGRAMMATICALLY COMPUTED SCORES (Python rule) ---
    prog_duration_quality: float      # 1–10 (deterministic)

    # --- SUPPORTING SIGNALS (not in final score calculation) ---
    has_cliffhanger_sfx: bool         # SFX marker present — supporting signal only
    total_duration_sec: float

    # --- WEIGHTS APPLIED ---
    weights: dict

    # --- FINAL SCORE ---
    final_score: float                # Weighted average, 0–10 scale
    score_confidence: str             # "high" | "medium" | "low" | "mock"

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "scores": {
                "AI-generated": {
                    "hook_strength":        {"score": self.ai_hook_strength,        "weight": self.weights["hook_strength"]},
                    "cliffhanger_strength": {"score": self.ai_cliffhanger_strength, "weight": self.weights["cliffhanger_strength"]},
                    "standalone_clarity":   {"score": self.ai_standalone_clarity,   "weight": self.weights["standalone_clarity"]},
                    "emotional_impact":     {"score": self.ai_emotional_impact,     "weight": self.weights["emotional_impact"]},
                },
                "programmatic": {
                    "duration_quality": {
                        "score": self.prog_duration_quality,
                        "weight": self.weights["duration_quality"],
                        "duration_sec": self.total_duration_sec,
                        "note": "Deterministic Python rule — not AI-generated",
                    }
                },
                "supporting_signals": {
                    "cliffhanger_sfx_marker": {
                        "present": self.has_cliffhanger_sfx,
                        "note": "SOUND FX marker — supporting signal only, not in score calculation",
                    }
                },
            },
            "final_score": self.final_score,
            "score_confidence": self.score_confidence,
        }


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_candidate(
    candidate,  # PromoCandidate
    weights: Optional[dict] = None,
    ideal_min: float = 25.0,
    ideal_max: float = 45.0,
    hard_min: float = 20.0,
    hard_max: float = 60.0,
) -> ScoreBreakdown:
    """
    Compute the five-dimensional weighted score for a PromoCandidate.

    Missing AI scores (None) are filled with neutral value 5.0 and
    confidence is lowered accordingly. This prevents the system from
    silently ignoring LLM failures.
    """
    w = weights or DEFAULT_WEIGHTS

    # Validate weights sum to ~1.0
    total_w = sum(w.values())
    if abs(total_w - 1.0) > 0.01:
        logger.warning(f"Scoring weights sum to {total_w:.3f}, not 1.0")

    # --- Resolve AI scores (with fallback + confidence tracking) ---
    missing_scores = []

    def resolve(val: Optional[float], name: str) -> float:
        if val is None:
            missing_scores.append(name)
            return 5.0  # neutral fallback
        return max(1.0, min(10.0, float(val)))

    ai_hook       = resolve(candidate.ai_hook_strength,       "hook_strength")
    ai_cliff      = resolve(candidate.ai_cliffhanger_strength, "cliffhanger_strength")
    ai_standalone = resolve(candidate.ai_standalone_clarity,   "standalone_clarity")
    ai_emotional  = resolve(candidate.ai_emotional_impact,     "emotional_impact")

    # --- Programmatic score ---
    prog_duration = _score_duration(
        candidate.total_duration_sec,
        ideal_min=ideal_min,
        ideal_max=ideal_max,
        hard_min=hard_min,
        hard_max=hard_max,
    )

    # --- Weighted final score ---
    final = (
        ai_hook       * w["hook_strength"]        +
        ai_cliff      * w["cliffhanger_strength"] +
        ai_standalone * w["standalone_clarity"]   +
        ai_emotional  * w["emotional_impact"]     +
        prog_duration * w["duration_quality"]
    )
    final = round(final, 4)

    # --- Confidence assessment ---
    is_mock = (
        candidate.ai_explanation and "MOCK" in (candidate.ai_explanation or "")
    ) or (
        candidate.ai_hook_strength is not None and
        candidate.ai_cliffhanger_strength is not None and
        candidate.ai_hook_strength == candidate.ai_cliffhanger_strength
        and candidate.ai_standalone_clarity == candidate.ai_emotional_impact
    )

    if is_mock:
        confidence = "mock"
    elif len(missing_scores) == 0:
        confidence = "high"
    elif len(missing_scores) <= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return ScoreBreakdown(
        candidate_id=candidate.candidate_id,
        ai_hook_strength=ai_hook,
        ai_cliffhanger_strength=ai_cliff,
        ai_standalone_clarity=ai_standalone,
        ai_emotional_impact=ai_emotional,
        prog_duration_quality=prog_duration,
        has_cliffhanger_sfx=candidate.has_cliffhanger_sfx,
        total_duration_sec=candidate.total_duration_sec,
        weights=w,
        final_score=final,
        score_confidence=confidence,
    )


def score_and_rank(
    candidates: list,
    weights: Optional[dict] = None,
    ideal_min: float = 25.0,
    ideal_max: float = 45.0,
    hard_min: float = 20.0,
    hard_max: float = 60.0,
    top_n: Optional[int] = 20,
) -> tuple[list, list[ScoreBreakdown]]:
    """
    Score all valid candidates, rank them, assign rank numbers.
    Returns (ranked_candidates, score_breakdowns).
    
    Invalid candidates are excluded from ranking but their
    score breakdowns are still computed for the quality report.
    """
    breakdowns = []
    for c in candidates:
        sb = score_candidate(c, weights, ideal_min, ideal_max, hard_min, hard_max)
        c.final_score = sb.final_score
        breakdowns.append(sb)

    # Rank only valid candidates by final_score descending
    valid = [c for c in candidates if c.is_valid]
    valid.sort(key=lambda c: c.final_score or 0, reverse=True)

    for rank, c in enumerate(valid, start=1):
        c.rank = rank

    # Apply top_n limit
    if top_n:
        ranked = valid[:top_n]
    else:
        ranked = valid

    return ranked, breakdowns


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from validator import PromoCandidate, PromoSegment

    print("=" * 60)
    print("SCORER UNIT TESTS")
    print("=" * 60)

    # Test 1: Duration scoring
    print("\n--- Duration quality scores (programmatic) ---")
    test_durations = [19.0, 20.0, 22.0, 25.0, 30.0, 35.0, 45.0, 50.0, 55.0, 60.0, 61.0]
    for d in test_durations:
        score = _score_duration(d)
        in_ideal = "✓ ideal" if 25 <= d <= 45 else ""
        print(f"  {d:>5.1f}s → score={score:>5.2f}  {in_ideal}")

    # Test 2: Full candidate scoring
    print("\n--- Full candidate scoring ---")

    def make_test_candidate(cid, hook, cliff, standalone, emotional, duration, is_mock=False):
        c = PromoCandidate(
            candidate_id=cid,
            segments=[PromoSegment(1, 1, "TEST SCENE", "00:00.00", "00:30.00", 0.0, 30.0)],
            opening_hook_text="Hook text",
            closing_cliffhanger_text="Cliff text",
            narrative_context="Some context",
            has_cliffhanger_sfx=False,
            ai_hook_strength=hook,
            ai_cliffhanger_strength=cliff,
            ai_standalone_clarity=standalone,
            ai_emotional_impact=emotional,
            ai_explanation=f"{'MOCK ' if is_mock else ''}Analysis",
        )
        c.total_duration_sec = duration
        c.is_valid = True
        return c

    candidates = [
        make_test_candidate("HIGH_QUALITY",  9.0, 9.5, 8.5, 9.0, 32.0),
        make_test_candidate("MEDIUM_QUALITY", 6.0, 7.0, 6.5, 6.0, 40.0),
        make_test_candidate("WEAK_QUALITY",   4.0, 3.5, 5.0, 4.0, 25.0),
        make_test_candidate("PERFECT_DUR",    8.0, 8.0, 7.0, 8.0, 35.0),
        make_test_candidate("LONG_BUT_VALID", 7.5, 8.5, 7.0, 7.5, 58.0),
    ]
    # Mark last two as valid for ranking test
    for c in candidates:
        c.validation_failures = []

    ranked, breakdowns = score_and_rank(candidates, top_n=10)

    print(f"\n  Rank | ID               | Final Score | Confidence | Duration")
    print(f"  " + "-" * 65)
    for c in ranked:
        sb = next(b for b in breakdowns if b.candidate_id == c.candidate_id)
        print(f"  #{c.rank:<4} | {c.candidate_id:<16} | {c.final_score:>7.4f}     | {sb.score_confidence:<10} | {c.total_duration_sec:.1f}s")

    # Test 3: Missing AI scores
    print("\n--- Missing AI score handling ---")
    partial = make_test_candidate("PARTIAL_SCORES", None, 8.0, None, 7.0, 30.0)
    partial.ai_hook_strength = None
    partial.ai_standalone_clarity = None
    partial.total_duration_sec = 30.0
    partial.is_valid = True
    partial.validation_failures = []
    sb = score_candidate(partial)
    print(f"  Partial scores → final={sb.final_score:.4f}, confidence={sb.score_confidence}")
    print(f"  (hook=None→5.0, standalone=None→5.0)")

    # Test 4: Score breakdown dict structure
    print("\n--- Score breakdown dict structure ---")
    sb_dict = breakdowns[0].to_dict()
    print(f"  Keys: {list(sb_dict.keys())}")
    print(f"  Score sections: {list(sb_dict['scores'].keys())}")
    print(f"  AI scores: {list(sb_dict['scores']['AI-generated'].keys())}")
    print(f"  Programmatic: {list(sb_dict['scores']['programmatic'].keys())}")
    print(f"  Supporting signals: {list(sb_dict['scores']['supporting_signals'].keys())}")

    print(f"\n✓ Scorer unit tests complete.")

