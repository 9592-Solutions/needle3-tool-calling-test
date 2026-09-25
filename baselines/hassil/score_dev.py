# /// script
# requires-python = ">=3.11"
# dependencies = ["hassil==3.12.1", "PyYAML==6.0.3"]
# ///
"""Score the hassil arm (home app only) on a config partition. hassil_arm.predict returns canonical calls;
they are renamed into S1's tool and argument names (the inverse of contracts/mapping.py) so the one shared
scorer applies. Untuned: there is nothing to tune. usage:
NEEDLE3_INTENTS_DIR=/private/tmp/needle3-intents uv run hassil/score_dev.py [partition] [out.json]"""
import collections, json, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent.parent
sys.path.insert(0, str(H)); import hassil_arm  # noqa: E402
sys.path.insert(0, str(R / "harness")); import score  # noqa: E402
sys.path.insert(0, str(R / "contracts")); import mapping  # noqa: E402
part = sys.argv[1] if len(sys.argv) > 1 else "dev"
inv = {}
for raw, (action, amap) in mapping.TABLES["S1-home"].items():
    inv[action] = (raw, {c: r for r, c in amap.items()})
gold = [g for g in map(json.loads, open(R / "partitions" / "gold.jsonl")) if g["app"] == "home" and g["partition"] == part and g["gold"] != "ambiguous"]
rows, cells = [], collections.defaultdict(list)
for g in gold:
    pc = hassil_arm.predict(g["text"])
    raw = [{"name": inv[c["action"]][0], "arguments": {inv[c["action"]][1].get(k, k): v for k, v in c["args"].items()}} for c in pc]
    s = score.score_item(g["gold"], raw, "S1-home")
    ok = s["outcome"] in ("correct_action", "correct_nonaction")
    cells[g["stratum"]].append(ok); rows.append({"id": g["id"], "pred": pc, "outcome": s["outcome"]})
m = sum(sum(v) / len(v) for v in cells.values()) / len(cells)
res = {"partition": part, "n": len(rows), "macro_home": round(m, 4), "per_stratum": {k: [sum(v), len(v)] for k, v in cells.items()},
       "outcomes": dict(collections.Counter(r["outcome"] for r in rows)), "rows": rows}
json.dump(res, open(sys.argv[2] if len(sys.argv) > 2 else H / f"DEV-{part}.json", "w"), indent=1)
print({k: v for k, v in res.items() if k != "rows"})
