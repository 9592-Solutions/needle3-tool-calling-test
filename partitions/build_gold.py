"""Assemble config-side gold: items both annotators agreed on (gold and stratum), plus the adjudicator's
decision wherever they differed (DESIGN §3.5). Writes partitions/gold.jsonl. usage: python3 partitions/build_gold.py"""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
items = {x["id"]: x for x in map(json.loads, open(H / "items.jsonl"))}
ag = json.load(open(H / "annotation" / "agreement.json"))
adj = {x["id"]: x for x in map(json.loads, open(H / "annotation" / "adjudicated.jsonl"))}
out, missing = [], []
for i, x in items.items():
    if i in adj:
        g, s, how = adj[i]["gold"], adj[i]["stratum"], f"adjudicated ({adj[i]['issue']}, chose {adj[i]['chose']})"
    elif i in ag["agree"] and ag["agree"][i]["stratum_A"] == ag["agree"][i]["stratum_B"]:
        g, s, how = ag["agree"][i]["gold"], ag["agree"][i]["stratum_A"], "agreed"
    else:
        missing.append(i); continue
    out.append({"id": i, "app": x["app"], "partition": x["partition"], "bucket": x["bucket"], "text": x["text"],
                "gold": g, "stratum": s, "label_source": how})
assert not missing, missing
with open(H / "gold.jsonl", "w") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
import collections
print(len(out), collections.Counter((r["app"], r["partition"], r["stratum"]) for r in out if r["partition"] in ("dev", "selection")))
