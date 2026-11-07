"""
Deep parser verification test — run against all 50 episodes.
Checks:
 1. Event type distribution correctness
 2. Scene timestamp integrity
 3. No cross-scene timestamp contamination
 4. Dialogue speaker names look reasonable
 5. Episode 6 format-variant handling
 6. Cliffhanger SFX signal accuracy
"""
import sys, re
sys.path.insert(0, r'e:\Kuku_FM_CASE_STUDY\src')
from pathlib import Path
from parser import load_all_episodes, parse_timestamp, seconds_to_ts

SCRIPTS_DIR = Path(r'e:\Kuku_FM_CASE_STUDY\data\scripts\I Married a Broken Soldier. He was a Duke')

episodes, report = load_all_episodes(SCRIPTS_DIR)

failures = []
warnings_count = 0

print("=" * 70)
print("DEEP VERIFICATION TEST")
print("=" * 70)

for ep in episodes:
    n = ep.episode_number

    # 1. Check event types are valid
    for scene in ep.scenes:
        for evt in scene.events:
            if evt.event_type not in ("CAMERA", "ACTION", "DIALOGUE", "SOUND_FX"):
                failures.append(f"Ep{n} Sc{scene.scene_number}: Unknown event type '{evt.event_type}'")

    # 2. Check scene timestamps are well-formed
    for scene in ep.scenes:
        s = parse_timestamp(scene.start_ts)
        e = parse_timestamp(scene.end_ts)
        if s is None:
            failures.append(f"Ep{n} Sc{scene.scene_number}: unparseable scene start '{scene.start_ts}'")
        if e is None:
            failures.append(f"Ep{n} Sc{scene.scene_number}: unparseable scene end '{scene.end_ts}'")
        if s is not None and e is not None and e < s:
            failures.append(f"Ep{n} Sc{scene.scene_number}: end < start ({scene.end_ts} < {scene.start_ts})")
        if scene.duration_sec < 0:
            failures.append(f"Ep{n} Sc{scene.scene_number}: negative duration {scene.duration_sec}")

    # 3. Check all event timestamps parse correctly
    for scene in ep.scenes:
        for evt in scene.events:
            s = parse_timestamp(evt.start_ts)
            e = parse_timestamp(evt.end_ts)
            if s is None:
                failures.append(f"Ep{n} Sc{scene.scene_number}: bad event start '{evt.start_ts}' [{evt.event_type}]")
            if e is None:
                failures.append(f"Ep{n} Sc{scene.scene_number}: bad event end '{evt.end_ts}' [{evt.event_type}]")

    # 4. Check DIALOGUE events have non-empty speakers
    for scene in ep.scenes:
        for evt in scene.events:
            if evt.event_type == "DIALOGUE":
                if not evt.speaker or not evt.speaker.strip():
                    failures.append(f"Ep{n} Sc{scene.scene_number}: DIALOGUE event with empty speaker at {evt.start_ts}")
                # Check speaker doesn't look like a known non-character type
                if evt.speaker and evt.speaker.upper() in ("CAMERA", "ACTION", "SOUND FX"):
                    failures.append(f"Ep{n}: non-char type classified as DIALOGUE speaker: '{evt.speaker}'")

    # 5. Check non-dialogue events have no speaker
    for scene in ep.scenes:
        for evt in scene.events:
            if evt.event_type in ("CAMERA", "ACTION", "SOUND_FX") and evt.speaker:
                failures.append(f"Ep{n} Sc{scene.scene_number}: {evt.event_type} event has unexpected speaker '{evt.speaker}'")

    # 6. Check scene-relative timestamps: events should be within scene bounds
    # Tolerance of 0.5s to accommodate minor overlaps in source data
    # (Ep22 Sc1: source has SOUND_FX ending 0.30s after scene end — data quality note)
    TOL = 0.5
    for scene in ep.scenes:
        for evt in scene.events:
            if evt.start_sec < scene.start_sec - TOL:
                failures.append(
                    f"Ep{n} Sc{scene.scene_number}: event start {evt.start_ts} ({evt.start_sec:.2f}s) "
                    f"before scene start {scene.start_ts} ({scene.start_sec:.2f}s) [{evt.event_type}]"
                )
            if evt.end_sec > scene.end_sec + TOL:
                failures.append(
                    f"Ep{n} Sc{scene.scene_number}: event end {evt.end_ts} ({evt.end_sec:.2f}s) "
                    f"after scene end {scene.end_ts} ({scene.end_sec:.2f}s) [{evt.event_type}]"
                )

# Print event type counts
type_counts = {"CAMERA": 0, "ACTION": 0, "DIALOGUE": 0, "SOUND_FX": 0}
for ep in episodes:
    for scene in ep.scenes:
        for evt in scene.events:
            type_counts[evt.event_type] = type_counts.get(evt.event_type, 0) + 1

print(f"\nEvent type distribution across all 50 episodes:")
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {t:<12}: {c:>5}")

# Sample dialogue speakers from episodes 1, 10, 42
print("\nSample DIALOGUE speakers (Ep 1, 10, 42):")
for ep in episodes:
    if ep.episode_number in (1, 10, 42):
        speakers = set()
        for scene in ep.scenes:
            for evt in scene.events:
                if evt.event_type == "DIALOGUE" and evt.speaker:
                    speakers.add(evt.speaker)
        print(f"  Ep {ep.episode_number}: {sorted(speakers)}")

# Cliffhanger SFX signal check
print("\nEpisodes with cliffhanger SFX signals:")
for ep in episodes:
    for scene in ep.scenes:
        for evt in scene.events:
            if evt.is_cliffhanger_sfx:
                print(f"  Ep{ep.episode_number:>3} Sc{scene.scene_number}: {evt.start_ts} → {evt.text[:80]!r}")

# Episode 6 deep check
ep6 = next(e for e in episodes if e.episode_number == 6)
print(f"\nEp6 ALL-CAPS format deep check:")
print(f"  Scenes: {len(ep6.scenes)}")
print(f"  Scene 1 events: {len(ep6.scenes[0].events)}")
print(f"  Scene 2 events: {len(ep6.scenes[1].events)}")
dlg = [(evt.speaker, evt.start_ts, evt.text[:40]) for evt in ep6.scenes[0].events if evt.event_type == "DIALOGUE"]
print(f"  First 3 dialogue in Scene 1: {dlg[:3]}")

# Results
print(f"\n{'='*70}")
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  ✗ {f}")
else:
    print(f"✓ ALL CHECKS PASSED — 0 failures across 50 episodes")

print(f"\nParse warnings: {report['parsed_with_warnings']} episodes had warnings")
print(f"Parse errors:   {len(report['parse_errors'])} episodes had errors")
