"""Config-side partitions for Needle 3 (DESIGN §3.4): dev, selection, calibration, lexical bank, per app.

Sources (config side of the boundary agreed with the custodian, BUILD-LOG): MASSIVE en-US train+dev,
CLINC150 train+val+oos_train+oos_val, HWU64 rows NOT verbatim in MASSIVE whose sha256(str(data_row_index))[0]
is ODD. Anything whose normalised text is in the custodian's test-pool blocklist is dropped. Exact normalised
duplicates are removed across all config partitions.

Stage 1 (this file, deterministic): sample crowd items per app by source bucket, and pick SEEDS for the
authored items (N3 minimal edits, A3 two-action joins), which an editor agent then writes (stage 2).
Partition assignment is by sha256 of the item id, so it does not depend on content or order.
usage: python3 partitions/build_pool.py   (writes partitions/pool_stage1.json)
"""
import csv, hashlib, json, random, re
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", t.lower())).strip()
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
BLOCK = set(l.strip() for l in open(ROOT / "custodian" / "test-pool-blocklist.sha256") if l.strip() and not l.startswith("#"))

massive = [json.loads(l) for f in ("train", "dev") for l in open(ROOT / "sources" / f"massive_en-US_{f}.jsonl")]
clinc = json.loads((ROOT / "sources" / "clinc150_config_splits.json").read_text())
hwu = list(csv.DictReader(open("/tmp/hwu.csv"), delimiter=";"))
massive_norm = {norm(r["utt"]) for r in massive}

def ok(text):
    return sha(norm(text)) not in BLOCK

POOL = {"home": {}, "desk": {}}
def add(app, bucket, iid, text, src):
    if not text or not ok(text):
        return
    POOL[app].setdefault(bucket, []).append({"id": iid, "text": text.strip(), "source": src})

HOME_ACT = {"iot_hue_lightchange", "iot_hue_lightdim", "iot_hue_lightoff", "iot_hue_lighton", "iot_hue_lightup",
            "iot_cleaning", "iot_wemo_on", "iot_wemo_off"}
DESK_ACT = {"alarm_set", "alarm_remove", "lists_createoradd", "lists_remove", "calendar_set"}
HOME_NEAR = {"iot_coffee", "audio_volume_up", "audio_volume_down", "audio_volume_mute", "weather_query"}
DESK_NEAR = {"alarm_query", "lists_query", "calendar_query", "calendar_remove", "datetime_query", "reminder_query"}
FAR = {"qa_factoid", "general_quirky", "recommendation_events", "cooking_recipe", "play_music", "news_query",
       "transport_query", "email_sendemail", "social_post", "takeaway_order"}
for r in massive:
    iid = f"massive-{r['partition']}-{r['id']}"
    src = f"MASSIVE en-US {r['partition']} id {r['id']} ({r['intent']})"
    if r["intent"] in HOME_ACT: add("home", "act", iid, r["utt"], src)
    if r["intent"] in DESK_ACT: add("desk", "act", iid, r["utt"], src)
    if r["intent"] in HOME_NEAR: add("home", "near", iid, r["utt"], src)
    if r["intent"] in DESK_NEAR: add("desk", "near", iid, r["utt"], src)
    if r["intent"] in FAR:
        add("home", "far", iid, r["utt"], src); add("desk", "far", iid, r["utt"], src)
CL_HOME = {"smart_home"}
CL_DESK = {"alarm", "reminder", "reminder_update", "timer", "shopping_list", "shopping_list_update", "todo_list",
           "todo_list_update", "calendar", "calendar_update", "schedule_meeting", "meeting_schedule"}
for split in ("train", "val"):
    for i, (t, lab) in enumerate(clinc[split]):
        iid = f"clinc-{split}-{i}"; src = f"CLINC150 {split} #{i} ({lab})"
        if lab in CL_HOME: add("home", "clinc_domain", iid, t, src)
        if lab in CL_DESK: add("desk", "clinc_domain", iid, t, src)
for split in ("oos_train", "oos_val"):
    for i, (t, lab) in enumerate(clinc[split]):
        iid = f"clinc-{split}-{i}"; src = f"CLINC150 {split} #{i} (oos)"
        add("home", "far", iid, t, src); add("desk", "far", iid, t, src)
# HWU odd rows not in MASSIVE: seeds for authored edits (and their own crowd phrasing is not used directly)
SEEDS = {"home": [], "desk": []}
for idx, r in enumerate(hwu):
    if int(sha(str(idx))[0], 16) % 2 == 0:
        continue                                  # even = custodian's
    t = (r.get("answer") or "").strip()
    if not t or norm(t) in massive_norm or not ok(t):
        continue
    if r["scenario"] == "iot" and r["intent"] in ("hue_lightchange", "hue_lightdim", "hue_lightoff", "hue_lighton", "hue_lightup", "cleaning", "wemo_on", "wemo_off"):
        SEEDS["home"].append({"id": f"hwu-{idx}", "text": t, "source": f"HWU64 row {idx} ({r['scenario']}_{r['intent']})"})
    if r["scenario"] in ("alarm", "lists", "calendar") and r["intent"] in ("set", "remove", "createoradd"):
        SEEDS["desk"].append({"id": f"hwu-{idx}", "text": t, "source": f"HWU64 row {idx} ({r['scenario']}_{r['intent']})"})

# ---- sampling: per app 620 items = crowd buckets + authored ----
TARGET = {"act": 300, "near": 60, "clinc_domain": 50, "far": 60, "n3_edit": 110, "a3_join": 40}
PARTS = [("dev", 150), ("selection", 150), ("calibration", 120), ("lexical", 200)]
random.seed(20260922)
out = {"built": "2026-09-22", "rule": __doc__, "apps": {}}
for app in ("home", "desk"):
    seen, items = set(), []
    for bucket, n in TARGET.items():
        if bucket in ("n3_edit", "a3_join"):
            continue
        cand = sorted(POOL[app].get(bucket, []), key=lambda x: sha(x["id"]))
        k = 0
        for c in cand:
            if k >= n: break
            if norm(c["text"]) in seen: continue
            seen.add(norm(c["text"])); items.append({**c, "bucket": bucket}); k += 1
    seeds = [s for s in sorted(SEEDS[app], key=lambda x: sha(x["id"])) if norm(s["text"]) not in seen]
    edit_seeds = seeds[:TARGET["n3_edit"]]
    kinds = ["negation", "quotation", "reported_speech", "conditional", "question_about_state"]
    for j, s in enumerate(edit_seeds):
        items.append({"id": f"edit-{s['id']}", "text": None, "source": s["source"], "bucket": "n3_edit",
                      "seed_text": s["text"], "edit_kind": kinds[j % len(kinds)]})
    acts = [x for x in items if x["bucket"] == "act"]
    for j in range(TARGET["a3_join"]):
        a, b = acts[(2 * j) % len(acts)], acts[(2 * j + 1) % len(acts)]
        items.append({"id": f"join-{app}-{j:03d}", "text": None, "source": f"join of {a['id']} + {b['id']}",
                      "bucket": "a3_join", "seed_text": [a["text"], b["text"]]})
    # partition by hash of id, into the fixed sizes
    items.sort(key=lambda x: sha("part:" + x["id"]))
    i0 = 0
    for name, n in PARTS:
        for x in items[i0:i0 + n]:
            x["partition"] = name
        i0 += n
    out["apps"][app] = {"pool_sizes": {b: len(v) for b, v in POOL[app].items()} | {"hwu_seeds": len(SEEDS[app])},
                        "items": items}
    print(app, out["apps"][app]["pool_sizes"], len(items))
(H / "pool_stage1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
