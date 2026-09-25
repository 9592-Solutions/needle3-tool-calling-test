"""Replace config items that near-duplicate the public test pools (custodian lists at f67ac86a and 509e7de3,
pool-level). Each removed item is replaced by a clean supply row of the same app and bucket, in the same
partition. For the 'act' bucket, act-rich source intents are drawn first (rows whose MASSIVE annotation names
the slots the contract needs), because the first round came out act-light (266 of 1,170). Authored items
(edits, joins) are re-seeded from clean seeds and go back to the blind editor. Deterministic.
usage: python3 partitions/resample.py"""
import hashlib, json, re
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", t.lower())).strip()
bad_items = {l.split(":")[0].strip() for l in open(R / "custodian/config-neardup-vs-test-pools.txt") if l.strip() and not l.startswith("#")}
bad_supply = {l.split(":")[0].strip() for l in open(R / "custodian/config-supply-neardup-vs-test-pools.txt") if l.strip() and not l.startswith("#")}
items = [json.loads(l) for l in open(H / "items.jsonl")]
supply = [json.loads(l) for l in open(H / "candidate_supply.jsonl")]
massive = {f"massive-{r['partition']}-{r['id']}": r for f in ("train", "dev") for r in map(json.loads, open(R / f"sources/massive_en-US_{f}.jsonl"))}
used_ids = {x["id"] for x in items}; used_txt = {norm(x["text"]) for x in items}
def rich(row):
    m = massive.get(row["id"])
    if not m: return False
    a, it = m["annot_utt"], m["intent"]
    if it in ("iot_hue_lightchange",): return "color_type" in a
    if it in ("iot_hue_lightoff", "iot_hue_lighton"): return True
    if it in ("iot_cleaning", "iot_wemo_on", "iot_wemo_off"): return "time :" not in a and "date :" not in a
    if it == "alarm_set": return "time :" in a and "general_frequency" not in a
    if it in ("lists_createoradd", "lists_remove"): return "list_name" in a
    if it == "calendar_set": return "remind" in m["utt"] and "general_frequency" not in a
    return False
pools = {}
for r in supply:
    if r["id"] in bad_supply or r["id"] in used_ids or norm(r["text"]) in used_txt: continue
    pools.setdefault((r["app"], r["bucket"]), []).append(r)
for k in pools:
    pools[k].sort(key=lambda r: (not rich(r) if k[1] == "act" else 0, sha("re:" + r["id"])))
kept, new, edits = [], [], []
for x in items:
    if x["id"] not in bad_items:
        kept.append(x); continue
    b = x["bucket"]
    if b in ("n3_edit", "a3_join"):
        edits.append(x); continue
    cand = pools[(x["app"], b)]
    while cand and (cand[0]["id"] in used_ids or norm(cand[0]["text"]) in used_txt): cand.pop(0)
    r = cand.pop(0)
    used_ids.add(r["id"]); used_txt.add(norm(r["text"]))
    new.append({"id": r["id"], "text": r["text"], "source": (massive.get(r["id"]) or {}).get("intent", r["bucket"]),
                "bucket": b, "partition": x["partition"], "app": x["app"], "replaces": x["id"]})
# authored replacements: fresh seeds, back to the editor
seeds = pools.get(("home", "hwu_seed"), []), pools.get(("desk", "hwu_seed"), [])
seed_pool = {"home": list(seeds[0]), "desk": list(seeds[1])}
act_pool = {a: [r for r in pools.get((a, "act"), []) if r["id"] not in used_ids] for a in ("home", "desk")}
tasks = []
for j, x in enumerate(edits):
    if x["bucket"] == "n3_edit":
        s = seed_pool[x["app"]].pop(0)
        nid = f"edit-{s['id']}"
        tasks.append({"id": nid, "kind": x["edit_kind"], "seed": s["text"]})
        new.append({"id": nid, "text": None, "source": f"edit of {s['id']}", "bucket": "n3_edit", "edit_kind": x["edit_kind"],
                    "seed_text": s["text"], "partition": x["partition"], "app": x["app"], "replaces": x["id"]})
    else:
        a, b = act_pool[x["app"]].pop(0), act_pool[x["app"]].pop(0)
        nid = f"join2-{x['app']}-{j:03d}"
        tasks.append({"id": nid, "kind": "join", "seeds": [a["text"], b["text"]]})
        new.append({"id": nid, "text": None, "source": f"join of {a['id']} + {b['id']}", "bucket": "a3_join",
                    "seed_text": [a["text"], b["text"]], "partition": x["partition"], "app": x["app"], "replaces": x["id"]})
json.dump({"kept": len(kept), "new": new}, open(H / "resample_round2.json", "w"), indent=1, ensure_ascii=False)
open(H / "editor_tasks_round2.jsonl", "w").write("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n")
print("kept", len(kept), "new", len(new), "authored tasks", len(tasks),
      "rich act drawn", sum(1 for n in new if n["bucket"] == "act" and rich({"id": n["id"]})))
