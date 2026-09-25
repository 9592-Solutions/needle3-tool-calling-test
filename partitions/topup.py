"""Top up act-rich items in dev and selection (the desk act strata held 3-14 items per partition after
round 2). Drawn only from supply rows the custodian's whole-supply scan marked clean (509e7de3), never used
before, act-rich MASSIVE intents first (same predicate as resample.py), deterministic by hash.
usage: python3 partitions/topup.py"""
import hashlib, json, re, runpy
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent
g = runpy.run_path(str(H / "resample.py").replace("resample.py", "resample.py"), run_name="not_main") if False else None
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", t.lower())).strip()
bad = {l.split(":")[0].strip() for l in open(R / "custodian/config-supply-neardup-vs-test-pools.txt") if l.strip() and not l.startswith("#")}
items = [json.loads(l) for l in open(H / "items.jsonl")]
used_ids = {x["id"] for x in items} | {x["id"] for x in map(json.loads, open(H / "items_round1.jsonl"))}
used_txt = {norm(x["text"]) for x in items}
massive = {f"massive-{r['partition']}-{r['id']}": r for f in ("train", "dev") for r in map(json.loads, open(R / f"sources/massive_en-US_{f}.jsonl"))}
def rich(i):
    m = massive.get(i)
    if not m: return False
    a, it = m["annot_utt"], m["intent"]
    if it == "iot_hue_lightchange": return "color_type" in a
    if it in ("iot_hue_lightdim", "iot_hue_lightup"): return "change_amount" in a and "percent" in a and " by " not in a
    if it in ("iot_hue_lightoff", "iot_hue_lighton"): return "house_place" in a
    if it == "alarm_set": return "time :" in a and "general_frequency" not in a
    if it == "alarm_remove": return "time :" in a
    if it in ("lists_createoradd", "lists_remove"): return "list_name" in a
    if it == "calendar_set": return "remind" in m["utt"] and "general_frequency" not in a and "time :" in a
    return False
supply = [json.loads(l) for l in open(H / "candidate_supply.jsonl")]
want = {("desk", "selection"): 40, ("desk", "dev"): 30, ("home", "selection"): 20, ("home", "dev"): 20}
new = []
for app in ("desk", "home"):
    cand = [r for r in supply if r["app"] == app and r["bucket"] == "act" and r["id"] not in bad and r["id"] not in used_ids
            and norm(r["text"]) not in used_txt and rich(r["id"])]
    cand.sort(key=lambda r: sha("topup:" + r["id"]))
    for part in ("selection", "dev"):
        k = 0
        while k < want[(app, part)] and cand:
            r = cand.pop(0)
            if norm(r["text"]) in used_txt: continue
            used_txt.add(norm(r["text"])); used_ids.add(r["id"])
            new.append({"id": r["id"], "text": r["text"], "source": massive[r["id"]]["intent"], "bucket": "act",
                        "partition": part, "app": app, "topup": True}); k += 1
with open(H / "items.jsonl", "a") as f:
    for n in new: f.write(json.dumps(n, ensure_ascii=False) + "\n")
b = sorted([{"id": n["id"], "app": n["app"], "text": n["text"]} for n in new], key=lambda x: sha("ann3:" + x["id"]))
open(H / "annotation/batches/r3_0.jsonl", "w").write("\n".join(json.dumps(x, ensure_ascii=False) for x in b) + "\n")
print(len(new))
