# =============================================================================
# analyzer.py — Promo Candidate Generation
#
# Responsibilities:
#   - For each episode/scene, generate promo candidates using rule-based
#     pre-selection + LLM quality assessment
#   - Enforce: scene-relative timestamps, no cross-scene merging confusion
#   - Cliffhanger detection: narrative context FIRST; SFX as supporting signal
#   - Produce PromoCandidate objects ready for validation and scoring
#
# Design:
#   Rule-based pre-selection → candidate windows within hard duration bounds
#   → LLM analysis (hook, cliffhanger, standalone, emotional impact)
#   → PromoCandidate construction (timestamps from source, not LLM-invented)
# =============================================================================

from __future__ import annotations

import json
import logging
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Import sibling modules
# ---------------------------------------------------------------------------

import sys
sys.path.insert(0, str(Path(__file__).parent))

from parser import Episode, Scene, TimestampedEvent, parse_timestamp, seconds_to_ts
from validator import PromoSegment, PromoCandidate
from llm_client import LLMClient


# ---------------------------------------------------------------------------
# Rule-based candidate window generator
# ---------------------------------------------------------------------------

@dataclass
class CandidateWindow:
    """A time window within a single scene that could become a promo."""
    episode_number: int
    scene_number: int
    scene_heading: str
    start_sec: float
    end_sec: float
    start_ts: str
    end_ts: str
    duration_sec: float
    # Pre-selected content
    opening_events: list[TimestampedEvent] = field(default_factory=list)
    closing_events: list[TimestampedEvent] = field(default_factory=list)
    all_events: list[TimestampedEvent] = field(default_factory=list)
    has_cliffhanger_sfx: bool = False
    cliffhanger_sfx_text: str = ""
    # Rule-based signals
    has_early_hook: bool = False      # First event is dramatic (dialogue within 3s)
    dialogue_density: float = 0.0    # fraction of events that are DIALOGUE


HARD_MIN = 20.0
HARD_MAX = 60.0
IDEAL_MIN = 25.0
IDEAL_MAX = 45.0


def _find_candidate_windows(
    scene: Scene,
    episode_number: int,
    min_dur: float = HARD_MIN,
    max_dur: float = HARD_MAX,
) -> list[CandidateWindow]:
    """
    Generate candidate windows from a scene using sliding-window strategy.
    
    Strategy:
    1. Full-scene window (if duration fits)
    2. First 20–45s of scene (hook-focused)
    3. Last 20–45s of scene (cliffhanger-focused)
    4. Any SOUND_FX cliffhanger anchor: take 20–45s ending at that anchor
    
    IMPORTANT: All timestamps are SCENE-RELATIVE.
    """
    windows = []
    scene_dur = scene.duration_sec

    if scene_dur < min_dur:
        # Scene too short — can't make a valid promo from it alone
        return []

    def make_window(start_sec: float, end_sec: float, label: str = "") -> Optional[CandidateWindow]:
        dur = end_sec - start_sec
        if dur < min_dur or dur > max_dur:
            return None
        # Snap to actual event timestamps in scene
        all_ts = sorted({e.start_sec for e in scene.events} | {e.end_sec for e in scene.events}
                        | {scene.start_sec, scene.end_sec})
        
        # Find closest actual timestamps within scene
        actual_start = min(all_ts, key=lambda t: abs(t - start_sec))
        actual_end   = min(all_ts, key=lambda t: abs(t - end_sec))
        
        if actual_start >= actual_end:
            return None
        actual_dur = actual_end - actual_start
        if actual_dur < min_dur or actual_dur > max_dur:
            return None

        # Collect events within this window
        window_events = [
            e for e in scene.events
            if e.start_sec >= actual_start - 0.1 and e.end_sec <= actual_end + 0.5
        ]

        if not window_events:
            return None

        # Check for cliffhanger SFX near the end of the window
        end_zone_start = actual_end - 10.0
        cfhgr_sfx = [
            e for e in window_events
            if e.event_type == "SOUND_FX" and e.is_cliffhanger_sfx
            and e.start_sec >= end_zone_start
        ]

        # Early hook check: is there dialogue/action in first 3 seconds?
        early_events = [e for e in window_events if e.start_sec < actual_start + 3.0]
        has_early_hook = any(e.event_type == "DIALOGUE" for e in early_events)

        # Dialogue density
        num_dialogue = sum(1 for e in window_events if e.event_type == "DIALOGUE")
        density = num_dialogue / max(len(window_events), 1)

        return CandidateWindow(
            episode_number=episode_number,
            scene_number=scene.scene_number,
            scene_heading=scene.heading,
            start_sec=actual_start,
            end_sec=actual_end,
            start_ts=seconds_to_ts(actual_start),
            end_ts=seconds_to_ts(actual_end),
            duration_sec=actual_dur,
            opening_events=window_events[:min(4, len(window_events))],
            closing_events=window_events[max(0, len(window_events) - 4):],
            all_events=window_events,
            has_cliffhanger_sfx=bool(cfhgr_sfx),
            cliffhanger_sfx_text=cfhgr_sfx[0].text if cfhgr_sfx else "",
            has_early_hook=has_early_hook,
            dialogue_density=density,
        )

    # Strategy 1: Full scene
    w = make_window(scene.start_sec, scene.end_sec, "full_scene")
    if w:
        windows.append(w)

    # Strategy 2: First IDEAL_MAX seconds
    if scene_dur > IDEAL_MAX:
        w = make_window(scene.start_sec, scene.start_sec + IDEAL_MAX, "first_45s")
        if w:
            windows.append(w)

    # Strategy 3: Last 25–45s (cliffhanger ending)
    if scene_dur > IDEAL_MIN:
        w = make_window(max(scene.start_sec, scene.end_sec - IDEAL_MAX),
                        scene.end_sec, "last_45s")
        if w:
            windows.append(w)

    # Strategy 4: Anchor on cliffhanger SFX events
    for evt in scene.events:
        if evt.is_cliffhanger_sfx:
            # Window ending at this SFX event
            anchor_end = evt.end_sec
            for window_dur in [IDEAL_MAX, 35.0, IDEAL_MIN]:
                w = make_window(anchor_end - window_dur, anchor_end, f"sfx_anchor_{evt.start_ts}")
                if w:
                    windows.append(w)
                    break

    # Strategy 5: Beginning-focused window (hook-first, 20–35s)
    if scene_dur > 30.0:
        w = make_window(scene.start_sec, scene.start_sec + 32.0, "hook_first_32s")
        if w:
            windows.append(w)

    # Deduplicate by (start_ts, end_ts)
    seen = set()
    unique_windows = []
    for w in windows:
        key = (w.start_ts, w.end_ts)
        if key not in seen:
            seen.add(key)
            unique_windows.append(w)

    return unique_windows


# ---------------------------------------------------------------------------
# LLM prompt construction
# ---------------------------------------------------------------------------

def _build_analysis_prompt(window: CandidateWindow, episode: Episode) -> str:
    """
    Build the LLM analysis prompt for a candidate window.
    
    Design principles:
    - Give full scene context, not just the window, so LLM understands narrative
    - Instruct LLM to quote EXACT text from screenplay for hook/cliffhanger
    - Explicitly instruct: SFX "cliffhanger" labels are supporting signals only
    - Require structured JSON output
    - Provide scoring rubric for each dimension
    """
    # Build a text representation of the window's events
    event_lines = []
    for evt in window.all_events:
        if evt.event_type == "DIALOGUE":
            event_lines.append(
                f"[{evt.start_ts}–{evt.end_ts}] {evt.speaker}"
                f"{f' ({evt.emotion})' if evt.emotion else ''}: \"{evt.text}\""
            )
        elif evt.event_type in ("CAMERA", "ACTION"):
            event_lines.append(f"[{evt.start_ts}–{evt.end_ts}] {evt.event_type}: {evt.text}")
        elif evt.event_type == "SOUND_FX":
            cfhgr_flag = " ⚠ [SFX cliffhanger signal]" if evt.is_cliffhanger_sfx else ""
            event_lines.append(f"[{evt.start_ts}–{evt.end_ts}] SOUND FX: {evt.text}{cfhgr_flag}")

    window_text = "\n".join(event_lines)

    # Include episode context
    prompt = textwrap.dedent(f"""
    You are a promo editor for a streaming microdrama platform. Your task is to evaluate whether a specific screenplay segment makes an excellent promotional clip.

    ## SHOW CONTEXT
    Show: "I Married a Broken Soldier. He was a Duke"
    Genre: Romantic period drama microdrama
    
    Episode {window.episode_number} Logline: {episode.logline}
    Continuity: {episode.continuity_notes}
    
    ## CANDIDATE SEGMENT
    Scene {window.scene_number}: {window.scene_heading}
    Timestamps: {window.start_ts} → {window.end_ts} (scene-relative, {window.duration_sec:.1f}s)
    
    ## SEGMENT CONTENT
    {window_text}
    
    ## EVALUATION TASK
    Assess this segment as a 20–60 second promotional clip. Score each dimension 1–10.
    
    ### Scoring Rubric:
    
    **hook_strength (1–10):**
    Does the segment open with something that immediately grabs attention within the first 3 seconds?
    10 = visceral shock/betrayal/threat that demands continued watching
    1 = calm scene establishment with no immediate tension
    
    **cliffhanger_strength (1–10):**
    IMPORTANT: Do NOT score based solely on SOUND FX "cliffhanger" labels or ominous music descriptions.
    Analyse the NARRATIVE SITUATION at the ending: is the core conflict unresolved? Does the viewer need to know what happens next?
    10 = unresolved direct threat to protagonist with no path forward visible
    5 = scene ends in a moment of change, but the stakes are unclear
    1 = situation is resolved — viewer has closure
    
    **standalone_clarity (1–10):**
    Can a viewer who has NEVER seen the show understand who these people are, what they want, and why it matters — within this clip alone?
    10 = complete emotional context, no prior knowledge needed
    5 = interesting but requires some backstory
    1 = incomprehensible without watching previous episodes
    
    **emotional_impact (1–10):**
    How powerful is the emotional experience of this segment? Consider: betrayal, fear, longing, rage, desperation, triumph.
    10 = genuinely gut-punching, would make viewers feel something
    1 = flat, procedural, no emotional stakes
    
    ## RESPONSE FORMAT
    Respond ONLY with valid JSON. No commentary outside the JSON block.
    
    ```json
    {{
      "hook_strength": <1–10 float>,
      "hook_text": "<exact quote or description from segment that IS the hook>",
      "hook_reason": "<why this is or isn't a strong hook — 1–2 sentences>",
      "cliffhanger_strength": <1–10 float>,
      "cliffhanger_text": "<exact final moment or last significant line/action>",
      "cliffhanger_reason": "<explain the NARRATIVE SITUATION at the end — is it unresolved? why? — 1–2 sentences>",
      "standalone_clarity": <1–10 float>,
      "standalone_reason": "<can a first-time viewer follow this? — 1 sentence>",
      "emotional_impact": <1–10 float>,
      "emotional_reason": "<what emotion does this evoke and how strongly? — 1 sentence>",
      "explanation": "<overall assessment: why this segment does or does not work as a promo — 2–3 sentences>",
      "is_good_promo": <true|false>,
      "suggested_start_ts": "<MM:SS.ss or null — only suggest a different start if the current one is clearly wrong>",
      "suggested_end_ts": "<MM:SS.ss or null — only suggest a different end if the current one is clearly wrong>"
    }}
    ```
    """).strip()

    return prompt


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

class PromoAnalyzer:
    """
    Generates promo candidates by combining rule-based window selection
    with LLM quality assessment.
    """

    def __init__(self, llm_client: LLMClient, cfg: dict):
        self.llm = llm_client
        self.cfg = cfg
        self._candidate_counter = 0

    def _next_id(self, ep_num: int, scene_num: int) -> str:
        self._candidate_counter += 1
        return f"PROMO_EP{ep_num:02d}_SC{scene_num}_{self._candidate_counter:03d}"

    def analyze_episode(self, episode: Episode) -> list[PromoCandidate]:
        """
        Generate promo candidates from a single episode.
        Each scene is analyzed independently — timestamps are scene-relative.
        """
        candidates = []

        for scene in episode.scenes:
            windows = _find_candidate_windows(scene, episode.episode_number)

            if not windows:
                logger.debug(f"Ep{episode.episode_number} Sc{scene.scene_number}: no valid windows")
                continue

            logger.info(
                f"Ep{episode.episode_number} Sc{scene.scene_number}: "
                f"{len(windows)} candidate windows found"
            )

            for window in windows:
                candidate = self._analyze_window(window, episode)
                if candidate:
                    candidates.append(candidate)

        return candidates

    def _analyze_window(self, window: CandidateWindow, episode: Episode) -> Optional[PromoCandidate]:
        """
        Analyze a single window: call LLM, build PromoCandidate.
        Timestamps in the output come from the parsed source, never from LLM.
        """
        cid = self._next_id(window.episode_number, window.scene_number)
        prompt = _build_analysis_prompt(window, episode)

        logger.debug(f"Calling LLM for {cid}")
        response = self.llm.call(prompt, expect_json=True)

        if response.get("error"):
            logger.warning(f"{cid}: LLM error — {response['error']}")
            # Still create candidate with None scores (will be scored by rules only)
            parsed = {}
        else:
            parsed = response.get("parsed") or {}

        # --- Extract LLM-generated scores (clearly labelled as AI-generated) ---
        ai_hook       = self._safe_score(parsed.get("hook_strength"))
        ai_cliff      = self._safe_score(parsed.get("cliffhanger_strength"))
        ai_standalone = self._safe_score(parsed.get("standalone_clarity"))
        ai_emotional  = self._safe_score(parsed.get("emotional_impact"))
        ai_explanation = parsed.get("explanation", "")

        # --- Extract hook and cliffhanger text from LLM (verify against source) ---
        # We use LLM-provided text as the DESCRIPTION, but we validate it exists in source
        hook_text = parsed.get("hook_text", "")
        cliff_text = parsed.get("cliffhanger_text", "")
        is_good = parsed.get("is_good_promo", True)

        # If LLM says it's not a good promo and all scores are low, skip
        if not is_good and all(
            (s or 0) < 4.0 for s in [ai_hook, ai_cliff, ai_standalone, ai_emotional]
        ):
            logger.debug(f"{cid}: LLM marked as poor promo candidate — skipping")
            return None

        # --- Fallback text from rule-based selection if LLM gave nothing ---
        if not hook_text and window.opening_events:
            first_dlg = next((e for e in window.opening_events if e.event_type == "DIALOGUE"), None)
            first_act = window.opening_events[0] if window.opening_events else None
            hook_text = first_dlg.text if first_dlg else (first_act.text if first_act else "")

        if not cliff_text and window.closing_events:
            last_dlg = next(
                (e for e in reversed(window.closing_events) if e.event_type == "DIALOGUE"), None
            )
            last_sfx = next(
                (e for e in reversed(window.closing_events) if e.event_type == "SOUND_FX"), None
            )
            cliff_text = last_dlg.text if last_dlg else (last_sfx.text if last_sfx else "")

        # --- Build narrative context ---
        narrative = ai_explanation or (
            f"Ep{window.episode_number} Sc{window.scene_number}: "
            f"{window.scene_heading} — {window.duration_sec:.1f}s segment."
        )

        # --- Build the PromoSegment (timestamps from SOURCE, not LLM) ---
        segment = PromoSegment(
            episode_number=window.episode_number,
            scene_number=window.scene_number,
            scene_heading=window.scene_heading,
            start_ts=window.start_ts,
            end_ts=window.end_ts,
            start_sec=window.start_sec,
            end_sec=window.end_sec,
        )

        candidate = PromoCandidate(
            candidate_id=cid,
            segments=[segment],
            opening_hook_text=hook_text[:500],
            closing_cliffhanger_text=cliff_text[:500],
            narrative_context=narrative[:1000],
            has_cliffhanger_sfx=window.has_cliffhanger_sfx,
            ai_hook_strength=ai_hook,
            ai_cliffhanger_strength=ai_cliff,
            ai_standalone_clarity=ai_standalone,
            ai_emotional_impact=ai_emotional,
            ai_explanation=ai_explanation[:1000] if ai_explanation else None,
        )
        # Recalculate duration from segment
        candidate.total_duration_sec = round(window.duration_sec, 2)

        return candidate

    @staticmethod
    def _safe_score(val) -> Optional[float]:
        """Parse a score value safely, returning None if invalid."""
        try:
            f = float(val)
            return max(1.0, min(10.0, f))
        except (TypeError, ValueError):
            return None

    def analyze_all(
        self, episodes: list[Episode], progress_callback=None
    ) -> list[PromoCandidate]:
        """
        Analyze all episodes and return all candidates (before validation/scoring).
        """
        all_candidates = []
        total = len(episodes)

        for i, episode in enumerate(episodes):
            logger.info(
                f"Analyzing episode {episode.episode_number}/{total} "
                f"({episode.episode_number}): {episode.logline[:60]}"
            )
            candidates = self.analyze_episode(episode)
            all_candidates.extend(candidates)

            if progress_callback:
                progress_callback(i + 1, total, episode.episode_number, len(candidates))

        logger.info(
            f"Analysis complete: {len(all_candidates)} total candidates "
            f"from {total} episodes"
        )
        return all_candidates


# ---------------------------------------------------------------------------
# Standalone test (uses mock LLM)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from parser import load_all_episodes
    from llm_client import MockLLMClient, ResponseCache

    scripts_dir = Path(r"e:\Kuku_FM_CASE_STUDY\data\scripts\I Married a Broken Soldier. He was a Duke")
    cache_dir   = Path(r"e:\Kuku_FM_CASE_STUDY\outputs\cache")

    print("Loading episodes...")
    episodes, _ = load_all_episodes(scripts_dir)

    # Test with first 5 episodes to keep runtime short
    test_episodes = episodes[:5]
    print(f"Testing analyzer on {len(test_episodes)} episodes (Ep 1–5)...")

    mock_llm = MockLLMClient(
        cache=ResponseCache(cache_dir),
        request_delay=0.0,  # No delay for mock
    )

    cfg = {
        "hard_min_seconds": 20.0,
        "hard_max_seconds": 60.0,
    }

    analyzer = PromoAnalyzer(llm_client=mock_llm, cfg=cfg)
    candidates = analyzer.analyze_all(test_episodes)

    print(f"\n{'='*60}")
    print(f"ANALYZER TEST RESULTS (Ep 1–5)")
    print(f"{'='*60}")
    print(f"Total candidates generated: {len(candidates)}")

    for c in candidates:
        seg = c.segments[0]
        print(f"\n  {c.candidate_id}")
        print(f"    Ep{seg.episode_number} Sc{seg.scene_number}: {seg.start_ts}–{seg.end_ts} ({c.total_duration_sec:.1f}s)")
        print(f"    Hook score (AI):        {c.ai_hook_strength}")
        print(f"    Cliffhanger score (AI): {c.ai_cliffhanger_strength}")
        print(f"    Standalone (AI):        {c.ai_standalone_clarity}")
        print(f"    Emotional (AI):         {c.ai_emotional_impact}")
        print(f"    Hook text:    {c.opening_hook_text[:60]!r}")
        print(f"    Cliff text:   {c.closing_cliffhanger_text[:60]!r}")
        print(f"    CF SFX signal: {c.has_cliffhanger_sfx}")

    print(f"\n✓ Analyzer test complete.")

