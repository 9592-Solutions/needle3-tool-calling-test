"""Canary, partition gap (DESIGN §6.2): accuracy on config items that come from MASSIVE en-US TRAIN against items
from MASSIVE en-US DEV, matched by source intent (per-intent accuracy, weighted by the dev-side count). Both
splits are public, so a gap would only show selective memorisation of one split; weak evidence either way.
usage: python3 canary/partition_gap.py"""
import collections, json, random, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent
sys.path.insert(0, str(R / "harness")); import score
gold = {g["id"]: g for g in map(json.loads, open(R / "partitions/gold.jsonl"))}
items = {x["id"]: x for x in map(json.loads, open(R / "partitions/items.jsonl"))}
massive = {f"massive-{r['partition']}-{r['id']}": r["intent"] for p in ("train", "dev") for r in map(json.loads, open(R / f"sources/massive_en-US_{p}.jsonl"))}


def results_needle(ver, app):
    d = json.load(open(R / f"runs/needle_config/out_{ver}_{app}.json"))
    out = {}
    for r in d["results"]:
        g = gold.get(r["id"])
        if not g or g["gold"] == "ambiguous" or r["id"] not in massive: continue
        s = score.score_item(g["gold"], score.needle_calls(r["parsed"]), f"{ver}-{app}")
        out[r["id"]] = s["outcome"] in ("correct_action", "correct_nonaction")
    return out


def results_llm(glob_pat):
    import glob as G
    out = {}
    for f in G.glob(str(R / glob_pat)):
        for l in open(f):
            r = json.loads(l); g = gold.get(r["id"])
            if not g or g["gold"] == "ambiguous" or r["id"] not in massive or r.get("http") != 200: continue
            s = score.score_item(g["gold"], r.get("pred"), r["schema"])
            out[r["id"]] = s["outcome"] in ("correct_action", "correct_nonaction")
    return out


def gap(res):
    by = collections.defaultdict(lambda: {"train": [], "dev": []})
    for i, ok in res.items():
        by[massive[i]]["train" if i.startswith("massive-train") else "dev"].append(ok)
    cells = [(k, v) for k, v in by.items() if v["train"] and v["dev"]]
    def est(cs):
        w = sum(len(v["dev"]) for _, v in cs)
        tr = sum(len(v["dev"]) * sum(v["train"]) / len(v["train"]) for _, v in cs) / w
        dv = sum(len(v["dev"]) * sum(v["dev"]) / len(v["dev"]) for _, v in cs) / w
        return tr, dv
    tr, dv = est(cells)
    rng = random.Random(0); bs = []
    for _ in range(4000):
        cs = [(k, {"train": [rng.choice(v["train"]) for _ in v["train"]], "dev": [rng.choice(v["dev"]) for _ in v["dev"]]}) for k, v in cells]
        a, b = est(cs); bs.append(a - b)
    bs.sort()
    return {"train_acc": round(tr, 4), "dev_acc": round(dv, 4), "gap": round(tr - dv, 4), "gap_95ci": [round(bs[100], 4), round(bs[3900], 4)],
            "n_train": sum(len(v["train"]) for _, v in cells), "n_dev": sum(len(v["dev"]) for _, v in cells), "intents": len(cells)}


out = {}
for ver in ("S1",):
    for app in ("home", "desk"):
        p = R / f"runs/needle_config/out_{ver}_{app}.json"
        d = json.load(open(p))
        if d.get("missing"): out[f"needle {ver} {app}"] = f"incomplete: {len(d['missing'])} items not yet run"; continue
        out[f"needle {ver} {app}"] = gap(results_needle(ver, app))
out["deepseek-v4-flash-0731 schema (selection only)"] = gap(results_llm("frontier/stage/deepseek__deepseek-v4-flash-0731__schema__*.jsonl"))
out["deepseek-v4-flash native (selection only)"] = gap(results_llm("frontier/stage/deepseek__deepseek-v4-flash__native__*.jsonl"))
json.dump(out, open(H / "partition_gap.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
