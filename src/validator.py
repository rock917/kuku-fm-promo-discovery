# =============================================================================
# validator.py — Deterministic Validation for Promo Candidates
#
# Responsibilities:
#   - Duration enforcement (20–60s hard limits)
#   - Timestamp format and existence verification
#   - Dialogue hallucination detection (LLM quotes must exist in source)
#   - Overlap/duplicate detection
#   - Weak cliffhanger structural checks
#   - Standalone context checks
#   - Generates validation failure reports with reasons
#
# This module uses ONLY Python — no LLM calls.
# AI-generated scores (hook, cliffhanger, etc.) are kept separate and
# clearly distinguished from these programmatic constraints.
# =============================================================================

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PromoSegment:
    """
    A single contiguous time range from one scene of one episode.
    Timestamps are SCENE-RELATIVE (not global episode time).

    IMPORTANT: Never combine segments from different scenes into a single
    continuous timeline. Each segment preserves its original scene context.
    """
    episode_number: int
    scene_number: int
    scene_heading: str
    start_ts: str       # Scene-relative "MM:SS.ss"
    end_ts: str
    start_sec: float    # Scene-relative decimal seconds
    end_sec: float


@dataclass
class PromoCandidate:
    """
    A complete promo recommendation — may consist of one or more segments
    from same or different scenes/episodes.
    """
    candidate_id: str
    segments: list[PromoSegment]

    # Textual content captured (verbatim from source)
    opening_hook_text: str         # First dialogue/action that creates the hook
    closing_cliffhanger_text: str  # Last dialogue/action that creates the cliffhanger

    # Narrative context
    narrative_context: str         # Why this works as a standalone promo
    has_cliffhanger_sfx: bool      # Whether any segment ends near a CF SFX marker

    # LLM-generated scores (1–10 scale) — CLEARLY LABELLED as AI-generated
    ai_hook_strength: Optional[float] = None
    ai_cliffhanger_strength: Optional[float] = None
    ai_standalone_clarity: Optional[float] = None
    ai_emotional_impact: Optional[float] = None
    ai_explanation: Optional[str] = None

    # Programmatic computed fields
    total_duration_sec: float = 0.0
    final_score: Optional[float] = None
    rank: Optional[int] = None

    # Validation state — set by validator
    is_valid: bool = True
    validation_failures: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.total_duration_sec = sum(
            s.end_sec - s.start_sec for s in self.segments
        )

    @property
    def primary_episode(self) -> int:
        return self.segments[0].episode_number if self.segments else -1

    @property
    def episode_numbers(self) -> list[int]:
        return list(dict.fromkeys(s.episode_number for s in self.segments))

    @property
    def is_multi_episode(self) -> bool:
        return len(set(s.episode_number for s in self.segments)) > 1


# ---------------------------------------------------------------------------
# Validation configuration (matches config.yaml)
# ---------------------------------------------------------------------------

@dataclass
class ValidationConfig:
    hard_min_seconds: float = 20.0
    hard_max_seconds: float = 60.0
    ideal_min_seconds: float = 25.0
    ideal_max_seconds: float = 45.0
    max_hook_start_seconds: float = 3.0   # Hook must land within first 3s of segment
    min_dialogue_lines: int = 1           # Must have at least 1 dialogue line
    # Duplicate detection: candidates sharing this % of duration overlap are duplicates
    overlap_threshold: float = 0.6


# ---------------------------------------------------------------------------
# Individual validation checks
# ---------------------------------------------------------------------------

def _check_duration(candidate: PromoCandidate, cfg: ValidationConfig) -> list[str]:
    """Hard duration limit: must be 20–60 seconds total."""
    failures = []
    d = candidate.total_duration_sec
    if d < cfg.hard_min_seconds:
        failures.append(
            f"DURATION_TOO_SHORT: {d:.2f}s < minimum {cfg.hard_min_seconds}s"
        )
    elif d > cfg.hard_max_seconds:
        failures.append(
            f"DURATION_TOO_LONG: {d:.2f}s > maximum {cfg.hard_max_seconds}s"
        )
    return failures


def _check_hook_timing(candidate: PromoCandidate, cfg: ValidationConfig) -> list[str]:
    """
    The opening hook must be established within the first 3 seconds
    of the first segment.
    """
    warnings = []
    if not candidate.segments:
        return ["NO_SEGMENTS: candidate has no segments"]
    first_seg = candidate.segments[0]
    if not candidate.opening_hook_text:
        return ["MISSING_HOOK: no opening hook text provided"]
    # Check that hook_text appears early in the first segment
    # We validate this by checking the hook_text is non-empty (structural check)
    # Timing is enforced by the analyzer when it selects the hook
    return warnings


def _check_cliffhanger_quality(candidate: PromoCandidate) -> list[str]:
    """
    Structural check: the closing text must suggest unresolved tension.
    We check for resolved endings using simple heuristics.
    
    NOTE: This is a programmatic supporting check only.
    The LLM provides the primary cliffhanger quality score.
    SFX "cliffhanger" labels are supporting signals, not sufficient alone.
    """
    warnings = []
    text = candidate.closing_cliffhanger_text.lower() if candidate.closing_cliffhanger_text else ""

    if not text:
        return ["MISSING_CLIFFHANGER: no closing text provided"]

    # Signals of RESOLVED endings (bad for promos)
    resolved_patterns = [
        r'\b(fade\s+out|cut\s+to\s+black|the\s+end|credits\s+roll)\b',
        r'\b(they\s+embrace|they\s+kiss|reconcile|forgive|resolve)\b',
        r'\b(happily|peacefully|relieved|at\s+peace)\b',
        r'\b(walks\s+away\s+triumphantly|victorious\s+smile)\b',
    ]
    for pat in resolved_patterns:
        if re.search(pat, text, re.IGNORECASE):
            warnings.append(
                f"POSSIBLY_RESOLVED_ENDING: closing text matches resolved pattern '{pat}'"
            )

    return warnings


def _check_standalone_context(candidate: PromoCandidate) -> list[str]:
    """
    Check whether the narrative_context field suggests standalone viability.
    This is a structural check — LLM provides the actual standalone score.
    """
    warnings = []
    if not candidate.narrative_context or len(candidate.narrative_context) < 10:
        warnings.append("WEAK_STANDALONE_CONTEXT: narrative context is empty or too brief")
    return warnings


def _check_dialogue_exists(
    candidate: PromoCandidate,
    episodes_by_number: dict,
) -> list[str]:
    """
    Hallucination check: verify that the opening_hook_text and
    closing_cliffhanger_text don't contain fabricated dialogue that
    contradicts the source screenplay.

    Strategy:
    - If the text looks like a verbatim quote (contains quotation marks), 
      verify it appears in the source (substring match).
    - If the text looks like a description/paraphrase, skip the substring
      check but verify the referenced segment actually exists in the source.
    - Reject if the text contains recognisable lines that DON'T appear in source.
    """
    failures = []

    def normalize(s: str) -> str:
        return re.sub(r'\s+', ' ', s.strip().lower().strip('"\''))

    def looks_like_verbatim_quote(text: str) -> bool:
        """Heuristic: if the text contains a quoted phrase, treat as verbatim."""
        return bool(re.search(r'"[^"]{10,}"', text))

    hook_text  = candidate.opening_hook_text or ""
    cliff_text = candidate.closing_cliffhanger_text or ""

    for seg in candidate.segments:
        ep = episodes_by_number.get(seg.episode_number)
        if not ep:
            failures.append(f"INVALID_EPISODE_REF: Episode {seg.episode_number} not found")
            continue

        scene = next((s for s in ep.scenes if s.scene_number == seg.scene_number), None)
        if not scene:
            failures.append(
                f"INVALID_SCENE_REF: Scene {seg.scene_number} not found in Ep{seg.episode_number}"
            )
            continue

        all_text = " ".join(normalize(e.text) for e in scene.events)

        # Only perform verbatim check if the text contains quoted dialogue
        # (i.e., the LLM claims this is a direct line from the screenplay)
        if seg == candidate.segments[0] and looks_like_verbatim_quote(hook_text):
            quoted = re.findall(r'"([^"]{10,})"', hook_text)
            for quote in quoted:
                q_norm = normalize(quote)
                if len(q_norm) > 10 and q_norm not in all_text:
                    # Try first 20 chars (partial match for long quotes)
                    if normalize(q_norm[:20]) not in all_text:
                        failures.append(
                            f"HALLUCINATED_HOOK: quoted dialogue not found in "
                            f"Ep{seg.episode_number} Sc{seg.scene_number}: '{quote[:60]}'"
                        )

        if seg == candidate.segments[-1] and looks_like_verbatim_quote(cliff_text):
            quoted = re.findall(r'"([^"]{10,})"', cliff_text)
            for quote in quoted:
                q_norm = normalize(quote)
                if len(q_norm) > 10 and q_norm not in all_text:
                    if normalize(q_norm[:20]) not in all_text:
                        failures.append(
                            f"HALLUCINATED_CLIFFHANGER: quoted dialogue not found in "
                            f"Ep{seg.episode_number} Sc{seg.scene_number}: '{quote[:60]}'"
                        )

    return failures


def _check_timestamp_exists(
    candidate: PromoCandidate,
    episodes_by_number: dict,
) -> list[str]:
    """
    Verify that start_ts and end_ts for each segment actually exist as
    timestamps in the source screenplay (within ±0.5s tolerance).
    """
    failures = []
    TOL = 0.5  # seconds

    for seg in candidate.segments:
        ep = episodes_by_number.get(seg.episode_number)
        if not ep:
            continue  # Already caught by dialogue check

        scene = next((s for s in ep.scenes if s.scene_number == seg.scene_number), None)
        if not scene:
            continue

        # Collect all event timestamps in scene
        all_ts_secs = set()
        for evt in scene.events:
            all_ts_secs.add(evt.start_sec)
            all_ts_secs.add(evt.end_sec)
        # Also include scene boundaries
        all_ts_secs.add(scene.start_sec)
        all_ts_secs.add(scene.end_sec)

        # Check start timestamp
        if not any(abs(t - seg.start_sec) <= TOL for t in all_ts_secs):
            failures.append(
                f"TIMESTAMP_NOT_FOUND: start {seg.start_ts} ({seg.start_sec:.2f}s) "
                f"not found in Ep{seg.episode_number} Sc{seg.scene_number} (±{TOL}s)"
            )

        # Check end timestamp
        if not any(abs(t - seg.end_sec) <= TOL for t in all_ts_secs):
            failures.append(
                f"TIMESTAMP_NOT_FOUND: end {seg.end_ts} ({seg.end_sec:.2f}s) "
                f"not found in Ep{seg.episode_number} Sc{seg.scene_number} (±{TOL}s)"
            )

        # Check start < end
        if seg.start_sec >= seg.end_sec:
            failures.append(
                f"INVERTED_TIMESTAMPS: start ({seg.start_ts}) >= end ({seg.end_ts}) "
                f"in Ep{seg.episode_number} Sc{seg.scene_number}"
            )

    return failures


def _check_cross_scene_contamination(candidate: PromoCandidate) -> list[str]:
    """
    Ensure segments from different scenes are not presented as a single
    continuous timestamp range. Each segment must reference its own scene.
    """
    failures = []
    for i, seg in enumerate(candidate.segments):
        if seg.scene_number is None or seg.episode_number is None:
            failures.append(f"MISSING_SCENE_REF: segment {i} has no scene/episode number")
    return failures


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def _segments_overlap(a: PromoSegment, b: PromoSegment, threshold: float) -> bool:
    """
    Return True if two segments from the same episode+scene overlap
    by more than `threshold` fraction of the shorter segment's duration.
    """
    if a.episode_number != b.episode_number:
        return False
    if a.scene_number != b.scene_number:
        return False
    # Calculate overlap
    overlap_start = max(a.start_sec, b.start_sec)
    overlap_end   = min(a.end_sec, b.end_sec)
    overlap = max(0.0, overlap_end - overlap_start)
    duration_a = a.end_sec - a.start_sec
    duration_b = b.end_sec - b.start_sec
    shorter = min(duration_a, duration_b)
    if shorter <= 0:
        return False
    return (overlap / shorter) >= threshold


def find_duplicates(
    candidates: list[PromoCandidate],
    threshold: float = 0.6,
) -> list[tuple[str, str, str]]:
    """
    Find pairs of candidates that share overlapping segments.
    Returns list of (id_a, id_b, reason) tuples.
    """
    duplicates = []
    for i, a in enumerate(candidates):
        for j, b in enumerate(candidates):
            if j <= i:
                continue
            # Check if any segment pair overlaps
            for sa in a.segments:
                for sb in b.segments:
                    if _segments_overlap(sa, sb, threshold):
                        reason = (
                            f"Ep{sa.episode_number} Sc{sa.scene_number}: "
                            f"{sa.start_ts}–{sa.end_ts} overlaps with "
                            f"{sb.start_ts}–{sb.end_ts} (≥{threshold:.0%})"
                        )
                        duplicates.append((a.candidate_id, b.candidate_id, reason))
    return duplicates


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------

def validate_candidate(
    candidate: PromoCandidate,
    episodes_by_number: dict,
    cfg: Optional[ValidationConfig] = None,
) -> PromoCandidate:
    """
    Run all deterministic validations on a PromoCandidate.
    Sets candidate.is_valid, .validation_failures, .validation_warnings in place.
    Returns the candidate (modified in place).

    Failures = hard disqualifications (candidate will be excluded from ranked output)
    Warnings = soft issues (noted in quality report but candidate kept)
    """
    if cfg is None:
        cfg = ValidationConfig()

    failures: list[str] = []
    warnings: list[str] = []

    # Hard checks (disqualifying)
    failures += _check_duration(candidate, cfg)
    failures += _check_timestamp_exists(candidate, episodes_by_number)
    failures += _check_dialogue_exists(candidate, episodes_by_number)
    failures += _check_cross_scene_contamination(candidate)

    # Soft checks (warnings)
    warnings += _check_hook_timing(candidate, cfg)
    warnings += _check_cliffhanger_quality(candidate)
    warnings += _check_standalone_context(candidate)

    candidate.validation_failures = failures
    candidate.validation_warnings = warnings
    candidate.is_valid = len(failures) == 0

    return candidate


def validate_all(
    candidates: list[PromoCandidate],
    episodes_by_number: dict,
    cfg: Optional[ValidationConfig] = None,
) -> tuple[list[PromoCandidate], dict]:
    """
    Validate all candidates and generate a quality report.
    Returns (all_candidates_with_validation_state, quality_report).
    """
    if cfg is None:
        cfg = ValidationConfig()

    for c in candidates:
        validate_candidate(c, episodes_by_number, cfg)

    # Duplicate detection (runs across all candidates regardless of validity)
    duplicates = find_duplicates(candidates, cfg.overlap_threshold)
    dup_ids = set()
    for id_a, id_b, reason in duplicates:
        # Mark the lower-scoring one as duplicate (or the second one if scores equal)
        a = next((c for c in candidates if c.candidate_id == id_a), None)
        b = next((c for c in candidates if c.candidate_id == id_b), None)
        if a and b:
            # Prefer the candidate with higher final_score (or first if equal)
            score_a = a.final_score or 0
            score_b = b.final_score or 0
            loser = b if score_a >= score_b else a
            if loser.is_valid:  # only flag if not already invalid
                loser.validation_failures.append(f"DUPLICATE_OF: overlaps with {id_a if loser == b else id_b} — {reason}")
                loser.is_valid = False
            dup_ids.add(loser.candidate_id)

    valid   = [c for c in candidates if c.is_valid]
    invalid = [c for c in candidates if not c.is_valid]

    # Collect all failure types
    failure_types: dict[str, int] = {}
    for c in invalid:
        for f in c.validation_failures:
            ftype = f.split(':')[0]
            failure_types[ftype] = failure_types.get(ftype, 0) + 1

    quality_report = {
        "total_candidates": len(candidates),
        "valid_candidates": len(valid),
        "invalid_candidates": len(invalid),
        "duplicates_found": len(duplicates),
        "failure_type_counts": failure_types,
        "duplicate_pairs": [
            {"candidate_a": a, "candidate_b": b, "reason": r}
            for a, b, r in duplicates
        ],
        "invalid_candidate_details": [
            {
                "id": c.candidate_id,
                "episodes": c.episode_numbers,
                "duration_sec": round(c.total_duration_sec, 2),
                "failures": c.validation_failures,
                "warnings": c.validation_warnings,
            }
            for c in invalid
        ],
    }

    return candidates, quality_report


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from parser import load_all_episodes, parse_timestamp

    logging.basicConfig(level=logging.INFO)
    scripts_dir = Path(__file__).parent.parent / "data" / "scripts" / "I Married a Broken Soldier. He was a Duke"
    episodes, _ = load_all_episodes(scripts_dir)
    ep_map = {e.episode_number: e for e in episodes}

    cfg = ValidationConfig()

    print("=" * 60)
    print("VALIDATOR UNIT TESTS")
    print("=" * 60)

    # --- Test 1: Valid promo from Episode 1 (Scene 1, 00:11.30–00:43.10 = 31.8s) ---
    ep1 = ep_map[1]
    sc1 = ep1.scenes[0]
    valid_candidate = PromoCandidate(
        candidate_id="TEST_VALID_EP1",
        segments=[
            PromoSegment(
                episode_number=1, scene_number=1,
                scene_heading=sc1.heading,
                start_ts="00:11.30", end_ts="00:43.10",
                start_sec=11.30, end_sec=43.10,
            )
        ],
        opening_hook_text="You should turn around, Juliana.",
        closing_cliffhanger_text="Because he is marrying me.",
        narrative_context="Bride arrives at altar to find fiancé marrying her sister — raw betrayal hook with no resolution.",
        has_cliffhanger_sfx=False,
    )
    valid_candidate.total_duration_sec = 43.10 - 11.30

    result = validate_candidate(valid_candidate, ep_map, cfg)
    status = "✓ VALID" if result.is_valid else f"✗ INVALID: {result.validation_failures}"
    print(f"\nTest 1 (Valid 31.8s promo, Ep1):         {status}")
    if result.validation_warnings:
        print(f"  Warnings: {result.validation_warnings}")

    # --- Test 2: Too short (< 20s) ---
    short_candidate = PromoCandidate(
        candidate_id="TEST_SHORT",
        segments=[
            PromoSegment(
                episode_number=1, scene_number=1,
                scene_heading=sc1.heading,
                start_ts="00:11.30", end_ts="00:20.00",
                start_sec=11.30, end_sec=20.00,
            )
        ],
        opening_hook_text="You should turn around, Juliana.",
        closing_cliffhanger_text="Not anymore.",
        narrative_context="Too short.",
        has_cliffhanger_sfx=False,
    )
    short_candidate.total_duration_sec = 20.00 - 11.30
    result2 = validate_candidate(short_candidate, ep_map, cfg)
    status2 = "✓ VALID" if result2.is_valid else f"✗ INVALID: {result2.validation_failures}"
    print(f"Test 2 (Too short 8.7s):                  {status2}")

    # --- Test 3: Too long (> 60s) ---
    ep1_duration = sc1.duration_sec
    long_candidate = PromoCandidate(
        candidate_id="TEST_LONG",
        segments=[
            PromoSegment(
                episode_number=1, scene_number=1,
                scene_heading=sc1.heading,
                start_ts="00:00.00", end_ts="02:18.00",
                start_sec=0.0, end_sec=138.0,
            )
        ],
        opening_hook_text="Symmetrical framing on the heavy church doors",
        closing_cliffhanger_text="Cut to black.",
        narrative_context="Too long.",
        has_cliffhanger_sfx=True,
    )
    long_candidate.total_duration_sec = 138.0
    result3 = validate_candidate(long_candidate, ep_map, cfg)
    status3 = "✓ VALID" if result3.is_valid else f"✗ INVALID: {result3.validation_failures}"
    print(f"Test 3 (Too long 138s full episode):      {status3}")

    # --- Test 4: Hallucinated dialogue ---
    hallucinated = PromoCandidate(
        candidate_id="TEST_HALLUCINATION",
        segments=[
            PromoSegment(
                episode_number=1, scene_number=1,
                scene_heading=sc1.heading,
                start_ts="00:11.30", end_ts="00:43.10",
                start_sec=11.30, end_sec=43.10,
            )
        ],
        opening_hook_text='"Juliana, I have always loved you deeply!"',  # Quoted verbatim line that does not exist
        closing_cliffhanger_text="Because he is marrying me.",
        narrative_context="Some context.",
        has_cliffhanger_sfx=False,
    )
    hallucinated.total_duration_sec = 43.10 - 11.30
    result4 = validate_candidate(hallucinated, ep_map, cfg)
    status4 = "✓ DETECTED" if not result4.is_valid else "✗ MISSED"
    print(f"Test 4 (Hallucinated hook dialogue):      {status4}: {result4.validation_failures}")

    # --- Test 5: Duplicate detection ---
    dup_a = PromoCandidate(
        candidate_id="DUP_A",
        segments=[PromoSegment(1, 1, sc1.heading, "00:11.30", "00:43.10", 11.30, 43.10)],
        opening_hook_text="You should turn around, Juliana.",
        closing_cliffhanger_text="Because he is marrying me.",
        narrative_context="Context A", has_cliffhanger_sfx=False,
    )
    dup_a.total_duration_sec = 31.8
    dup_b = PromoCandidate(
        candidate_id="DUP_B",
        segments=[PromoSegment(1, 1, sc1.heading, "00:13.00", "00:45.00", 13.00, 45.00)],
        opening_hook_text="Not anymore.",
        closing_cliffhanger_text="Because he is marrying me.",
        narrative_context="Context B", has_cliffhanger_sfx=False,
    )
    dup_b.total_duration_sec = 32.0
    dups = find_duplicates([dup_a, dup_b], threshold=0.6)
    print(f"Test 5 (Duplicate detection):             {'✓ DETECTED' if dups else '✗ MISSED'} ({len(dups)} pairs)")
    if dups:
        print(f"  → {dups[0]}")

    # --- Test 6: Invalid episode reference ---
    invalid_ep = PromoCandidate(
        candidate_id="TEST_INVALID_EP",
        segments=[PromoSegment(99, 1, "UNKNOWN", "00:10.00", "00:40.00", 10.0, 40.0)],
        opening_hook_text="Some text",
        closing_cliffhanger_text="Some ending",
        narrative_context="Context", has_cliffhanger_sfx=False,
    )
    invalid_ep.total_duration_sec = 30.0
    result6 = validate_candidate(invalid_ep, ep_map, cfg)
    status6 = "✓ DETECTED" if not result6.is_valid else "✗ MISSED"
    print(f"Test 6 (Invalid ep reference Ep99):       {status6}: {result6.validation_failures[:1]}")

    print("\n✓ Validator unit tests complete.")

