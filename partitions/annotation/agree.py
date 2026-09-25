"""Compare annotators A and B per item after canonical normalisation (contracts/mapping.py), write the
agreed gold and the disagreement list for adjudication. usage: python3 annotation/agree.py"""
import json, sys, glob, collections
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent.parent / "harness")); import score
def load(d):
    out = {}
    for f in glob.glob(str(H / d / "*.jsonl")):
        for l in open(f):
            l = l.strip()
            if l: r = json.loads(l); out[r["id"]] = r
    return out
A, B = load("A"), load("B")
items = {x["id"]: x for x in map(json.loads, open(H.parent / "items.jsonl"))}
def key(gold, app):
    if gold == "ambiguous": return "ambiguous"
    sid = f"S1-{app}"
    return sorted(json.dumps(sorted(score._key(c) for c in score.canon_gold(a, sid))) for a in gold)
agree, dis = {}, []
for i, x in items.items():
    a, b = A.get(i), B.get(i)
    if a is None or b is None: dis.append({"id": i, "why": "missing"}); continue
    try:
        ka, kb = key(a["gold"], x["app"]), key(b["gold"], x["app"])
    except Exception as e:
        dis.append({"id": i, "why": f"unparseable {e}"}); continue
    if ka == kb and ka != "ambiguous":
        agree[i] = {"id": i, "gold": a["gold"], "stratum_A": a.get("stratum"), "stratum_B": b.get("stratum")}
    else:
        dis.append({"id": i, "app": x["app"], "text": x["text"], "A": a, "B": b})
print("items", len(items), "agree", len(agree), "disagree", len(dis))
c = collections.Counter(x["app"] for x in dis if "app" in x); print(dict(c))
st = sum(v["stratum_A"] == v["stratum_B"] for v in agree.values()); print("stratum agreement among agreed gold", st, "/", len(agree))
json.dump({"agree": agree, "disagree": dis}, open(H / "agreement.json", "w"), indent=1, ensure_ascii=False)
