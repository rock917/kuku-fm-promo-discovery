import zipfile, re

zf = zipfile.ZipFile(r'e:\Kuku_FM_CASE_STUDY\I Married a Broken Soldier. He was a Duke-scripts (2).zip')

stats = []
for info in zf.infolist():
    if info.filename.endswith('.txt'):
        content = zf.read(info.filename).decode('utf-8', errors='replace')
        ep_num = re.search(r'EPISODE NUMBER: Episode (\d+)', content)
        logline = re.search(r'EPISODE LOGLINE: (.+)', content)
        scenes = re.findall(r'^SCENE (\d+)', content, re.MULTILINE)
        timestamps = re.findall(r'Start: \((\d+:\d+\.\d+)\)', content)
        scene_starts = re.findall(r'Scene start: (\S+)', content)
        scene_ends = re.findall(r'Scene end: (\S+)', content)
        cont_notes = re.search(r'CONTINUITY NOTES: (.+)', content)
        
        # Check for anomalies
        malformed_ts = [t for t in timestamps if not re.match(r'^\d+:\d{2}\.\d{2}$', t)]
        
        ep_n = ep_num.group(1) if ep_num else '?'
        last_ts = scene_ends[-1] if scene_ends else '?'
        
        stats.append({
            'ep': ep_n,
            'filename': info.filename.split('/')[-1],
            'scenes': len(scenes),
            'ts_count': len(timestamps),
            'last_scene_end': last_ts,
            'size': info.file_size,
            'has_logline': bool(logline),
            'has_cont_notes': bool(cont_notes),
            'malformed_ts': malformed_ts,
            'logline': (logline.group(1)[:80] if logline else ''),
        })

print("=== EPISODE STRUCTURE ANALYSIS ===\n")
for s in stats:
    malformed = f" MALFORMED_TS:{s['malformed_ts']}" if s['malformed_ts'] else ""
    print(f"Ep{s['ep']:>3}: {s['scenes']} scenes, {s['ts_count']:>3} timestamps, last_end={s['last_scene_end']}, size={s['size']:>6}B{malformed}")

print(f"\nTotal episodes: {len(stats)}")
print(f"Min size: {min(s['size'] for s in stats)}B, Max size: {max(s['size'] for s in stats)}B")
scene_counts = [s['scenes'] for s in stats]
print(f"Scenes per episode: min={min(scene_counts)}, max={max(scene_counts)}, avg={sum(scene_counts)/len(scene_counts):.1f}")

# Check for episodes missing standard headers
missing_headers = [s['ep'] for s in stats if not s['has_logline'] or not s['has_cont_notes']]
if missing_headers:
    print(f"Episodes missing logline/cont_notes: {missing_headers}")

# All loglines
print("\n=== EPISODE LOGLINES ===")
for s in stats:
    print(f"Ep{s['ep']:>3}: {s['logline']}")

zf.close()

