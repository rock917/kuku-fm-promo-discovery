# =============================================================================
# parser.py — Episode Parser for Kuku FM Promo Discovery System
#
# Responsibilities:
#   - Load and parse all .txt screenplay files from the configured directory
#   - Handle both standard (title-case) and Episode-6-style (ALL-CAPS) formats
#   - Extract: episode metadata, scenes, timestamps, dialogue, actions, SFX
#   - Track scene-level timestamps independently (scenes reset to 00:00.00)
#   - Return structured Python objects; never modify original files
# =============================================================================

from __future__ import annotations

import os
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TimestampedEvent:
    """A single timed element within a scene: CAMERA, ACTION, DIALOGUE, SOUND FX."""
    event_type: str          # "CAMERA" | "ACTION" | "DIALOGUE" | "SOUND_FX"
    speaker: Optional[str]   # Character name (DIALOGUE only); None otherwise
    emotion: Optional[str]   # Emotional direction, e.g. "Cold, Callous"
    start_ts: str            # Original timestamp string "MM:SS.ss"
    end_ts: str
    start_sec: float         # Decimal seconds (scene-relative)
    end_sec: float
    text: str                # Camera direction / action description / dialogue line / SFX description
    is_cliffhanger_sfx: bool = False   # True if SFX description contains cliffhanger keywords


@dataclass
class Scene:
    """A single scene within an episode."""
    scene_number: int
    heading: str             # e.g. "INT. CATHEDRAL – DAY"
    start_ts: str            # Scene-level start timestamp string
    end_ts: str              # Scene-level end timestamp string
    start_sec: float         # Decimal seconds (scene-relative — always starts near 0)
    end_sec: float
    duration_sec: float
    events: list[TimestampedEvent] = field(default_factory=list)

    # Derived convenience properties
    @property
    def dialogue_lines(self) -> list[TimestampedEvent]:
        return [e for e in self.events if e.event_type == "DIALOGUE"]

    @property
    def sound_fx_events(self) -> list[TimestampedEvent]:
        return [e for e in self.events if e.event_type == "SOUND_FX"]

    @property
    def has_cliffhanger_sfx(self) -> bool:
        return any(e.is_cliffhanger_sfx for e in self.events)


@dataclass
class Episode:
    """A complete parsed episode."""
    episode_number: int
    episode_id: str          # e.g. "1671703" from filename
    filename: str
    logline: str
    continuity_notes: str
    scenes: list[Scene] = field(default_factory=list)
    parse_warnings: list[str] = field(default_factory=list)

    @property
    def total_duration_sec(self) -> float:
        return sum(s.duration_sec for s in self.scenes)

    @property
    def all_events(self) -> list[tuple[int, TimestampedEvent]]:
        """Returns (scene_number, event) pairs for all events across all scenes."""
        result = []
        for scene in self.scenes:
            for event in scene.events:
                result.append((scene.scene_number, event))
        return result

    @property
    def all_dialogue(self) -> list[tuple[int, TimestampedEvent]]:
        return [(sn, e) for sn, e in self.all_events if e.event_type == "DIALOGUE"]

    @property
    def has_multiple_scenes(self) -> bool:
        return len(self.scenes) > 1


# ---------------------------------------------------------------------------
# Timestamp utilities
# ---------------------------------------------------------------------------

_TS_PATTERN = re.compile(r'^(\d+):(\d{2})\.(\d{2})$')


def parse_timestamp(ts_str: str) -> Optional[float]:
    """
    Convert "MM:SS.ss" to decimal seconds.
    Returns None if the format is invalid.
    """
    ts_str = ts_str.strip()
    m = _TS_PATTERN.match(ts_str)
    if not m:
        return None
    minutes, seconds, hundredths = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return minutes * 60 + seconds + hundredths / 100.0


def seconds_to_ts(sec: float) -> str:
    """Convert decimal seconds back to 'MM:SS.ss' string."""
    minutes = int(sec // 60)
    remaining = sec - minutes * 60
    secs = int(remaining)
    hundredths = round((remaining - secs) * 100)
    if hundredths == 100:
        secs += 1
        hundredths = 0
    return f"{minutes:02d}:{secs:02d}.{hundredths:02d}"


# ---------------------------------------------------------------------------
# Episode parser
# ---------------------------------------------------------------------------

# SFX keywords that act as SUPPORTING SIGNALS for cliffhanger detection
# (not sufficient alone — must be corroborated by narrative analysis)
_CLIFFHANGER_SFX_KEYWORDS = {
    "cliffhanger", "ominous", "suspense", "suspenseful", "tension", "tense",
    "dramatic sting", "thunderous", "dread", "foreboding"
}

# Regex patterns — standard (title-case) format
_RE_SCENE_NUM_STD     = re.compile(r'^SCENE\s+(\d+)\s*$', re.MULTILINE)
_RE_SCENE_HEADING_STD = re.compile(r'^Scene heading:\s*(.+)$', re.MULTILINE | re.IGNORECASE)
_RE_SCENE_START_STD   = re.compile(r'^Scene start:\s*(\S+)', re.MULTILINE | re.IGNORECASE)
_RE_SCENE_END_STD     = re.compile(r'^Scene end:\s*(\S+)', re.MULTILINE | re.IGNORECASE)

# Regex patterns — Episode-6 ALL-CAPS format
_RE_SCENE_NUM_CAPS    = re.compile(r'^SCENE\s+(\d+)\s*$', re.MULTILINE)
_RE_SCENE_HEADING_CAPS = re.compile(r'^SCENE HEADING:\s*(.+)$', re.MULTILINE)
_RE_SCENE_START_CAPS  = re.compile(r'^SCENE START:\s*(\S+)', re.MULTILINE)
_RE_SCENE_END_CAPS    = re.compile(r'^SCENE END:\s*(\S+)', re.MULTILINE)

# Event block pattern: **TYPE:**  or  **CHARACTER (emotion):**
# Each block starts with **HEADER:** then Start/End timestamps, then body text.
# The body ends at the next ** block or end of string.
# We use a non-greedy match stopping at the next \n** to avoid cross-block capture.
_RE_EVENT_BLOCK = re.compile(
    r'\*\*(?P<header>[^*\n]+)\*\*\s*\n'
    r'Start:\s*\((?P<start>[^)]+)\)\s*\|\s*End:\s*\((?P<end>[^)]+)\)\s*\n'
    r'(?P<body>.*?)(?=\n\*\*[^*]|\Z)',
    re.DOTALL
)

# Character dialogue header: "CHARACTER NAME (emotion, state):"
_RE_CHAR_HEADER = re.compile(
    r'^(?P<name>[A-Z][A-Z\s\'\-\.]+?)(?:\s*\(O\.S\.\))?\s*(?:\((?P<emotion>[^)]+)\))?:?\s*$'
)

_KNOWN_NON_CHAR_TYPES = {"CAMERA", "ACTION", "SOUND FX", "SOUND FX (CONT'D)", "V.O.", "O.S."}


def _classify_header(header: str) -> tuple[str, Optional[str], Optional[str]]:
    """
    Given a **header** string, return (event_type, speaker, emotion).
    event_type: CAMERA | ACTION | SOUND_FX | DIALOGUE

    The header comes from between ** markers, e.g.:
      **CAMERA:**              → CAMERA
      **ACTION:**              → ACTION
      **SOUND FX:**            → SOUND_FX
      **LADY JULIANA (Trembling):**  → DIALOGUE, speaker="LADY JULIANA", emotion="Trembling"
      **THE FORMER GROOM (Cold):**   → DIALOGUE, speaker="THE FORMER GROOM", emotion="Cold"
    """
    h = header.strip().rstrip(':').strip()

    # --- Check non-dialogue types first (exact or prefix match, case-insensitive) ---
    h_upper = h.upper()

    if h_upper in ("CAMERA", "CAMERA (CONT'D)", "CAMERA CONT'D"):
        return "CAMERA", None, None
    if h_upper in ("ACTION", "ACTION (CONT'D)", "ACTION CONT'D"):
        return "ACTION", None, None
    if re.match(r'^SOUND\s*FX', h, re.IGNORECASE):
        return "SOUND_FX", None, None

    # --- Extract character name and emotion ---
    # Handle patterns like:
    #   LADY JULIANA (Trembling, Pleading)
    #   THE FORMER GROOM (Off-screen) (Dismissive)
    #   JULIANA (V.O.) (Reflective, Vulnerable)
    #   MATRIARCH (O.S.) (Firm)

    h_work = h

    # Remove trailing O.S. / V.O. modifiers (they don't affect event type)
    h_work = re.sub(r'\s*\(O\.S\.\)', '', h_work, flags=re.IGNORECASE).strip()
    h_work = re.sub(r'\s*\(V\.O\.\)', '', h_work, flags=re.IGNORECASE).strip()
    h_work = re.sub(r"\s*\(CONT'D\)", '', h_work, flags=re.IGNORECASE).strip()

    # Extract last parenthetical as emotion/direction
    emotion = None
    em_match = re.search(r'\(([^)]+)\)\s*$', h_work)
    if em_match:
        emotion = em_match.group(1).strip()
        h_work = h_work[:em_match.start()].strip()

    # What remains is the speaker name
    speaker = h_work.strip() if h_work.strip() else None

    # Reject known non-dialogue types that might slip through
    if speaker and speaker.upper() in ("CAMERA", "ACTION", "SOUND FX", "SOUND FX (CONT'D)"):
        if speaker.upper() == "CAMERA":
            return "CAMERA", None, None
        if speaker.upper() == "ACTION":
            return "ACTION", None, None
        return "SOUND_FX", None, None

    if speaker:
        return "DIALOGUE", speaker, emotion

    # Fallback — treat as ACTION
    return "ACTION", None, None


def _is_cliffhanger_sfx(text: str) -> bool:
    """Check if a SOUND FX description contains cliffhanger supporting keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _CLIFFHANGER_SFX_KEYWORDS)


def _parse_scene_block(scene_num: int, block_text: str, is_caps_format: bool) -> tuple[Scene, list[str]]:
    """Parse a single scene block and return (Scene, warnings)."""
    warnings = []

    # --- Extract scene heading ---
    if is_caps_format:
        h_match = re.search(r'^SCENE HEADING:\s*(.+)$', block_text, re.MULTILINE)
        s_match = re.search(r'^SCENE START:\s*(\S+)', block_text, re.MULTILINE)
        e_match = re.search(r'^SCENE END:\s*(\S+)', block_text, re.MULTILINE)
    else:
        h_match = re.search(r'^Scene heading:\s*(.+)$', block_text, re.MULTILINE | re.IGNORECASE)
        s_match = re.search(r'^Scene start:\s*(\S+)', block_text, re.MULTILINE | re.IGNORECASE)
        e_match = re.search(r'^Scene end:\s*(\S+)', block_text, re.MULTILINE | re.IGNORECASE)

    heading = h_match.group(1).strip() if h_match else "UNKNOWN LOCATION"
    start_ts_str = s_match.group(1).strip() if s_match else None
    end_ts_str   = e_match.group(1).strip() if e_match else None

    # --- Parse event blocks ---
    events: list[TimestampedEvent] = []
    all_starts = []

    for em in _RE_EVENT_BLOCK.finditer(block_text):
        header = em.group('header').strip()
        raw_start = em.group('start').strip()
        raw_end   = em.group('end').strip()
        body      = em.group('body').strip()

        start_sec = parse_timestamp(raw_start)
        end_sec   = parse_timestamp(raw_end)

        if start_sec is None:
            warnings.append(f"Scene {scene_num}: malformed start timestamp '{raw_start}' in block '{header}'")
            continue
        if end_sec is None:
            warnings.append(f"Scene {scene_num}: malformed end timestamp '{raw_end}' in block '{header}'")
            continue

        all_starts.append(start_sec)

        event_type, speaker, emotion = _classify_header(header)

        is_cfhgr = False
        if event_type == "SOUND_FX":
            is_cfhgr = _is_cliffhanger_sfx(body)

        # Clean up body text — remove surrounding quotes from dialogue
        if event_type == "DIALOGUE":
            body = body.strip().strip('"').strip()

        evt = TimestampedEvent(
            event_type=event_type,
            speaker=speaker,
            emotion=emotion,
            start_ts=raw_start,
            end_ts=raw_end,
            start_sec=start_sec,
            end_sec=end_sec,
            text=body,
            is_cliffhanger_sfx=is_cfhgr,
        )
        events.append(evt)

    # --- Resolve scene start/end seconds ---
    start_sec_scene = parse_timestamp(start_ts_str) if start_ts_str else None
    end_sec_scene   = parse_timestamp(end_ts_str) if end_ts_str else None

    # Fallback: infer from first/last event timestamps
    if start_sec_scene is None:
        if all_starts:
            start_sec_scene = min(all_starts)
            warnings.append(
                f"Scene {scene_num}: missing 'Scene start' — inferred from first event: {seconds_to_ts(start_sec_scene)}"
            )
        else:
            start_sec_scene = 0.0
            warnings.append(f"Scene {scene_num}: no timestamps found; defaulting start to 0.0")

    if end_sec_scene is None:
        all_ends = [e.end_sec for e in events]
        if all_ends:
            end_sec_scene = max(all_ends)
            warnings.append(
                f"Scene {scene_num}: missing 'Scene end' — inferred from last event: {seconds_to_ts(end_sec_scene)}"
            )
        else:
            end_sec_scene = start_sec_scene
            warnings.append(f"Scene {scene_num}: no end timestamp found; duration will be 0.0")

    duration = round(end_sec_scene - start_sec_scene, 2)
    if duration < 0:
        warnings.append(f"Scene {scene_num}: negative duration ({duration:.2f}s) — start={start_ts_str}, end={end_ts_str}")
        duration = 0.0

    scene = Scene(
        scene_number=scene_num,
        heading=heading,
        start_ts=start_ts_str or seconds_to_ts(start_sec_scene),
        end_ts=end_ts_str or seconds_to_ts(end_sec_scene),
        start_sec=start_sec_scene,
        end_sec=end_sec_scene,
        duration_sec=duration,
        events=events,
    )
    return scene, warnings


def parse_episode_text(raw: str, episode_id: str = "custom", filename: str = "custom_script.txt") -> Episode:
    """
    Parse a raw screenplay string into a structured Episode object.
    Handles both standard and Episode-6 ALL-CAPS format automatically.
    """
    warnings: list[str] = []

    # --- Extract header metadata ---
    ep_num_match  = re.search(r'EPISODE NUMBER:\s*Episode\s+(\d+)', raw, re.IGNORECASE)
    logline_match = re.search(r'EPISODE LOGLINE:\s*(.+)', raw)
    cont_match    = re.search(r'CONTINUITY NOTES:\s*(.+)', raw)

    if not ep_num_match:
        warnings.append("Could not parse EPISODE NUMBER from file header (using 1)")
    episode_number = int(ep_num_match.group(1)) if ep_num_match else 1
    logline        = logline_match.group(1).strip() if logline_match else "Custom Screenplay"
    continuity     = cont_match.group(1).strip() if cont_match else ""

    # --- Detect format variant ---
    is_caps_format = bool(re.search(r'^SCENE HEADING:', raw, re.MULTILINE))

    # --- Extract script body ---
    script_match = re.search(r'--- SCRIPT START ---(.+?)(?:--- SCRIPT END ---|$)', raw, re.DOTALL)
    if not script_match:
        warnings.append("Could not locate --- SCRIPT START --- marker — analyzing full text")
        script_body = raw
    else:
        script_body = script_match.group(1)

    # --- Split into scene blocks ---
    scene_markers = list(re.finditer(r'^SCENE\s+(\d+)\s*$', script_body, re.MULTILINE))

    if not scene_markers:
        warnings.append("No SCENE markers found — treating entire script as one scene")
        scene_markers_data = [(1, script_body)]
    else:
        scene_markers_data = []
        for i, m in enumerate(scene_markers):
            scene_num = int(m.group(1))
            block_start = m.start()
            block_end = scene_markers[i + 1].start() if i + 1 < len(scene_markers) else len(script_body)
            block_text = script_body[block_start:block_end]
            scene_markers_data.append((scene_num, block_text))

    # --- Parse each scene ---
    scenes: list[Scene] = []
    for scene_num, block_text in scene_markers_data:
        scene, scene_warnings = _parse_scene_block(scene_num, block_text, is_caps_format)
        warnings.extend(scene_warnings)
        scenes.append(scene)

    return Episode(
        episode_number=episode_number,
        episode_id=episode_id,
        filename=filename,
        logline=logline,
        continuity_notes=continuity,
        scenes=scenes,
        parse_warnings=warnings,
    )


def parse_episode(filepath: Path) -> Episode:
    """
    Parse a single episode .txt file into an Episode object.
    Handles both standard and Episode-6 ALL-CAPS format automatically.
    Never modifies the original file.
    """
    raw = filepath.read_text(encoding='utf-8', errors='replace')
    fname = filepath.name
    ep_id_match = re.search(r'Episode (\d+)\.txt$', fname)
    episode_id = ep_id_match.group(1) if ep_id_match else "unknown"
    return parse_episode_text(raw, episode_id=episode_id, filename=fname)


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_all_episodes(scripts_dir: Path) -> tuple[list[Episode], dict]:
    """
    Load and parse all .txt episode files from the given directory.
    Returns (episodes_sorted_by_number, parse_report).
    """
    txt_files = sorted(scripts_dir.glob("episode-*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No episode-*.txt files found in {scripts_dir}")

    episodes: list[Episode] = []
    parse_report = {
        "total_files": len(txt_files),
        "parsed_ok": 0,
        "parsed_with_warnings": 0,
        "parse_errors": [],
        "warnings_by_episode": {},
        "format_variants": {},
    }

    for fpath in txt_files:
        try:
            ep = parse_episode(fpath)
            episodes.append(ep)
            if ep.parse_warnings:
                parse_report["parsed_with_warnings"] += 1
                parse_report["warnings_by_episode"][ep.episode_number] = ep.parse_warnings
            else:
                parse_report["parsed_ok"] += 1
            # Track format variant
            is_caps = bool(re.search(r'^SCENE HEADING:', fpath.read_text(encoding='utf-8', errors='replace'), re.MULTILINE))
            parse_report["format_variants"][ep.episode_number] = "CAPS" if is_caps else "standard"
        except Exception as exc:
            parse_report["parse_errors"].append({
                "file": fpath.name,
                "error": str(exc),
            })
            logger.error(f"Failed to parse {fpath.name}: {exc}")

    episodes.sort(key=lambda e: e.episode_number)
    return episodes, parse_report


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def episode_to_dict(ep: Episode) -> dict:
    """Convert an Episode to a JSON-serializable dict."""
    return {
        "episode_number": ep.episode_number,
        "episode_id": ep.episode_id,
        "filename": ep.filename,
        "logline": ep.logline,
        "continuity_notes": ep.continuity_notes,
        "total_duration_sec": ep.total_duration_sec,
        "num_scenes": len(ep.scenes),
        "has_multiple_scenes": ep.has_multiple_scenes,
        "parse_warnings": ep.parse_warnings,
        "scenes": [
            {
                "scene_number": s.scene_number,
                "heading": s.heading,
                "start_ts": s.start_ts,
                "end_ts": s.end_ts,
                "start_sec": s.start_sec,
                "end_sec": s.end_sec,
                "duration_sec": s.duration_sec,
                "num_events": len(s.events),
                "num_dialogue": len(s.dialogue_lines),
                "has_cliffhanger_sfx": s.has_cliffhanger_sfx,
                "events": [
                    {
                        "event_type": e.event_type,
                        "speaker": e.speaker,
                        "emotion": e.emotion,
                        "start_ts": e.start_ts,
                        "end_ts": e.end_ts,
                        "start_sec": e.start_sec,
                        "end_sec": e.end_sec,
                        "text": e.text,
                        "is_cliffhanger_sfx": e.is_cliffhanger_sfx,
                    }
                    for e in s.events
                ],
            }
            for s in ep.scenes
        ],
    }


if __name__ == "__main__":
    # Quick standalone test
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    scripts_dir = Path(__file__).parent.parent / "data" / "scripts" / "I Married a Broken Soldier. He was a Duke"
    if not scripts_dir.exists():
        print(f"ERROR: scripts directory not found: {scripts_dir}")
        sys.exit(1)

    print(f"Loading episodes from: {scripts_dir}")
    episodes, report = load_all_episodes(scripts_dir)

    print(f"\n{'='*60}")
    print(f"PARSE REPORT")
    print(f"{'='*60}")
    print(f"Total files found   : {report['total_files']}")
    print(f"Parsed successfully : {report['parsed_ok']}")
    print(f"Parsed with warnings: {report['parsed_with_warnings']}")
    print(f"Parse errors        : {len(report['parse_errors'])}")

    if report['parse_errors']:
        print("\nPARSE ERRORS:")
        for err in report['parse_errors']:
            print(f"  {err['file']}: {err['error']}")

    if report['warnings_by_episode']:
        print("\nWARNINGS BY EPISODE:")
        for ep_num, warns in sorted(report['warnings_by_episode'].items()):
            print(f"  Ep {ep_num:>3}:")
            for w in warns:
                print(f"    - {w}")

    print(f"\n{'='*60}")
    print(f"EPISODE SUMMARY")
    print(f"{'='*60}")
    print(f"{'Ep':>4} {'Scenes':>6} {'Events':>7} {'Dialogue':>9} {'Duration':>9} {'CF_SFX':>7} {'Format':>9}")
    print("-" * 60)
    for ep in episodes:
        total_events   = sum(len(s.events) for s in ep.scenes)
        total_dialogue = sum(len(s.dialogue_lines) for s in ep.scenes)
        has_cfhgr      = any(s.has_cliffhanger_sfx for s in ep.scenes)
        fmt            = report['format_variants'].get(ep.episode_number, '?')
        dur            = f"{ep.total_duration_sec:.2f}s"
        print(f"{ep.episode_number:>4} {len(ep.scenes):>6} {total_events:>7} {total_dialogue:>9} {dur:>9} {str(has_cfhgr):>7} {fmt:>9}")

    # Spot-check Episode 6 (the ALL-CAPS format episode)
    ep6 = next((e for e in episodes if e.episode_number == 6), None)
    if ep6:
        print(f"\n{'='*60}")
        print(f"EPISODE 6 SPOT-CHECK (ALL-CAPS FORMAT)")
        print(f"{'='*60}")
        print(f"Format variant: {report['format_variants'].get(6, '?')}")
        print(f"Scenes: {len(ep6.scenes)}")
        for s in ep6.scenes:
            print(f"  Scene {s.scene_number}: heading='{s.heading}', "
                  f"start='{s.start_ts}', end='{s.end_ts}', "
                  f"duration={s.duration_sec:.2f}s, events={len(s.events)}")
        print(f"Warnings: {ep6.parse_warnings}")

    # Spot-check Episode 1 (standard — first few events)
    ep1 = next((e for e in episodes if e.episode_number == 1), None)
    if ep1:
        print(f"\n{'='*60}")
        print(f"EPISODE 1 SPOT-CHECK (first 5 events)")
        print(f"{'='*60}")
        for i, evt in enumerate(ep1.scenes[0].events[:5]):
            print(f"  [{i+1}] {evt.event_type:<10} start={evt.start_ts} end={evt.end_ts} "
                  f"speaker={evt.speaker or '-':20} text={evt.text[:60]!r}")

    print(f"\n✓ Parser test complete. {len(episodes)} episodes parsed.")
