"""Fill CANARY.md's tables from prefix_summary.json and partition_gap.json, and check the prose claims against the
numbers (every gap interval includes zero; no verbatim reproduction). Refuses to write if a claim is false.
usage: python3 canary/fill.py"""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
P = json.load(open(H / "prefix_summary.json")); G = json.load(open(H / "partition_gap.json"))
rows = []
for k, v in P.items():
    m, kind = k.rsplit(" ", 1)
    rows.append(f"| {m.replace('__', '/')} | {kind} | {v['orig_exact']} / {v['para_exact']} | {v['orig_mean_similarity']:.3f} / {v['para_mean_similarity']:.3f} | {v['paired_diff']:+.3f} [{v['diff_95ci'][0]:+.3f}, {v['diff_95ci'][1]:+.3f}] |")
    assert v["orig_exact"].startswith("0/") and v["para_exact"].startswith("0/"), f"verbatim claim false for {k}"
grows = []
for k, v in G.items():
    assert isinstance(v, dict), f"partition gap incomplete: {k}: {v}"
    grows.append(f"| {k} | {v['train_acc']:.3f} | {v['dev_acc']:.3f} | {v['gap']:+.3f} [{v['gap_95ci'][0]:+.3f}, {v['gap_95ci'][1]:+.3f}] | {v['n_train']} / {v['n_dev']} | {v['intents']} |")
    assert v["gap_95ci"][0] <= 0 <= v["gap_95ci"][1], f"'no gap resolves' is false for {k}"
s = open(H / "CANARY.md").read().replace("PREFIX_ROWS", "\n".join(rows)).replace("GAP_ROWS", "\n".join(grows))
open(H / "CANARY.md", "w").write(s); print("filled")
