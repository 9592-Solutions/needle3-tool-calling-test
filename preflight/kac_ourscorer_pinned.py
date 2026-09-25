"""Known-answer control, second half: the same native outputs scored by OUR scorer (harness/score.py via
contracts/mapping.py, identity schema per vendor env), compared case by case with the vendor harness."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
import score
V = json.load(open(Path(__file__).parent / "vendor_harness_pinned.json"))
agree = n = ours = 0; bad = []
for e in V:
    N = {r["id"]: r for r in json.load(open(Path(__file__).parent / f"kac_native_pinned_{e["env"]}.json"))["results"]}
    for i, c in enumerate(e["cases"]):
        r = N[f"{e['env']}-{i:02d}"]
        gold = [[{"action": w["name"], "args": w.get("arguments", {})} for w in c["want"]]]
        s = score.score_item(gold, score.needle_calls(r["parsed"]), f"vendor-{e['env']}")
        ok = s["outcome"] in ("correct_action", "correct_nonaction")
        n += 1; ours += ok; agree += (ok == c["harness_ok"])
        if ok != c["harness_ok"]: bad.append((e["env"], i, c["query"], s["outcome"], c["harness_ok"]))
print(f"our scorer: {ours}/{n} correct; vendor harness: {sum(c['harness_ok'] for e in V for c in e['cases'])}/{n}; per-case agreement {agree}/{n}")
for b in bad: print("DISAGREE", b)
