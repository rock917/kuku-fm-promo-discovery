import json

with open('outputs/promos.json', encoding='utf-8') as f:
    d = json.load(f)
meta = d['metadata']
promos = d['ranked_promos']
print('=== METADATA ===')
for k, v in meta.items():
    print(f'  {k}: {v}')

print()
print('=== TOP 5 PROMOS ===')
for p in promos[:5]:
    seg = p['segments'][0]
    print(f"  #{p['rank']} Ep{p['episodes']} Sc{seg['scene_number']} {seg['start_ts']} to {seg['end_ts']} ({p['total_duration_sec']:.1f}s) score={p['final_score']:.3f}")
    ai = p['scoring']['scores']['AI-generated']
    prog = p['scoring']['scores']['programmatic']
    print(f"     AI: hook={ai['hook_strength']['score']} cliff={ai['cliffhanger_strength']['score']} standalone={ai['standalone_clarity']['score']} emotional={ai['emotional_impact']['score']}")
    print(f"     Prog: duration={prog['duration_quality']['score']}")
    print(f"     Hook: {p['opening_hook']['text'][:70]}")
    print(f"     Cliff: {p['closing_cliffhanger']['text'][:70]}")

print()
with open('outputs/quality_report.json', encoding='utf-8') as f:
    q = json.load(f)
counts = q.get('candidate_counts', {})
val = q.get('validation_summary', {})
print('=== QUALITY REPORT ===')
print(f"  Total generated: {counts.get('total_generated')}")
print(f"  Passed validation: {counts.get('passed_validation')}")
print(f"  Failed validation: {counts.get('failed_validation')}")
print(f"  Ranked output: {counts.get('ranked_output')}")
print(f"  Episodes with candidates: {counts.get('episodes_with_candidates')}/50")
print(f"  Duplicate pairs found: {val.get('duplicate_pairs_found')}")
print(f"  Failure types: {val.get('failure_type_counts')}")

with open('outputs/failure_analysis.json', encoding='utf-8') as f:
    fa = json.load(f)
print()
print('=== FAILURE ANALYSIS ===')
print(f"  Summary: {fa.get('summary', {})}")
lims = fa.get('known_system_limitations', [])
print(f"  Documented limitations count: {len(lims)}")
for i, lim in enumerate(lims, 1):
    print(f"    {i}. {lim.get('category')}: {lim.get('description')[:60]}...")
