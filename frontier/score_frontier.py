"""Score LLM-arm runs on the selection partition and compute the frontier (DESIGN §4.2 steps 3-5).

Accuracy axis: exact contract accuracy (harness/score.py), the DESIGN §13 D6 axis (per app: half act accuracy,
half the mean over N1/N2/N3; then the mean over apps; ambiguous items excluded). Cost axis: OBSERVED billed dollars
per 1,000 requests (sum of usage.cost / calls * 1000). A technical failure (no parse, failed call) counts wrong.

Rule, fixed before any number (DESIGN §4.2 step 5): drop dominated candidates (another at least as accurate
and no more expensive, one strictly); advance (a) the cheapest frontier candidate whose paired, family-
clustered bootstrap 95% interval for (best minus it) includes zero, and (b) the most accurate frontier
candidate. Families: an item is its own family on the config side (no paired phrasings), so the bootstrap
resamples items, stratified by app x stratum.

usage: python3 frontier/score_frontier.py <run_dir> <out.json> [--items screen|selection]
"""
import argparse, collections, glob, json, random, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent
sys.path.insert(0, str(R / "harness")); import score  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("out"); a = ap.parse_args()
gold = {g["id"]: g for g in map(json.loads, open(R / "partitions" / "gold.jsonl"))}


def load_run(f):
    recs = {}
    for l in open(f):
        r = json.loads(l)
        recs[r["id"]] = r          # later lines win (a resumed run appends retries)
    return recs


cands = collections.defaultdict(dict)   # (model, host, contract) -> {id: rec}
for f in glob.glob(str(Path(a.run_dir) / "*.jsonl")):
    if Path(f).name.startswith("_"):
        continue
    for i, r in load_run(f).items():
        cands[(r["model"], r["host"], r["contract"])][i] = r


def scored(recs):
    out = {}
    for i, r in recs.items():
        g = gold.get(i)
        if g is None or g["gold"] == "ambiguous":
            continue
        if r.get("http") == 429:
            continue                     # unserved by the pinned host's upstream rate limit: excluded, counted apart
        pred = r.get("pred") if r.get("http") == 200 else None
        s = score.score_item(g["gold"], pred, r["schema"])
        ok = s["outcome"] in ("correct_action", "correct_nonaction")
        out[i] = {"ok": ok, "cell": (g["app"], g["stratum"]), "outcome": s["outcome"]}
    return out


def macro(sc, ids=None):
    return score.macro_cells([(v["cell"], v["ok"]) for i, v in sc.items() if ids is None or i in ids])


rows = []
for key, recs in cands.items():
    if not any(r.get("http") == 200 for r in recs.values()):
        continue                         # never served at all: reported as unreachable in FRONTIER.md
    sc = scored(recs)
    n = sum(1 for r in recs.values() if r.get("http") == 200)      # calls actually served (billed)
    cost = sum(((r.get("usage") or {}).get("cost") or 0) for r in recs.values())
    served = collections.Counter(r.get("served_by") for r in recs.values() if r.get("http") == 200)
    tf = sum(v["outcome"] == "technical_failure" for v in sc.values())
    unserved = sum(1 for r in recs.values() if r.get("http") == 429)
    rows.append({"model": key[0], "host": key[1], "contract": key[2], "n": n, "n_scored": len(sc),
                 "macro_acc": round(macro(sc), 4), "micro_acc": round(sum(v["ok"] for v in sc.values()) / max(1, len(sc)), 4),
                 "technical_failures": tf, "unserved_429": unserved, "usd_per_1k": round(cost / n * 1000, 5) if n else None, "usd": round(cost, 6),
                 "served_by": dict(served), "outcomes": dict(collections.Counter(v["outcome"] for v in sc.values())),
                 "_sc": sc})
# keep each model's better contract (ties to schema) for the frontier
best = {}
for r in rows:
    k = r["model"]
    if k not in best or r["macro_acc"] > best[k]["macro_acc"] or (r["macro_acc"] == best[k]["macro_acc"] and r["contract"] == "schema"):
        best[k] = r
B = list(best.values())
for r in B:
    r["dominated_by"] = [o["model"] for o in B if o is not r and o["macro_acc"] >= r["macro_acc"] and o["usd_per_1k"] <= r["usd_per_1k"]
                         and (o["macro_acc"] > r["macro_acc"] or o["usd_per_1k"] < r["usd_per_1k"])]
front = sorted([r for r in B if not r["dominated_by"]], key=lambda r: r["usd_per_1k"])
top = max(front, key=lambda r: r["macro_acc"])


def boot(ra, rb, n=10000, seed=0):
    common = sorted(set(ra["_sc"]) & set(rb["_sc"]))
    strata = collections.defaultdict(list)
    for i in common:
        strata[ra["_sc"][i]["cell"]].append(i)
    rng = random.Random(seed); diffs = []
    for _ in range(n):
        ids = []
        for cell, xs in strata.items():
            ids += [rng.choice(xs) for _ in xs]
        sa = {i + f"#{k}": ra["_sc"][i] for k, i in enumerate(ids)}
        sb = {i + f"#{k}": rb["_sc"][i] for k, i in enumerate(ids)}
        diffs.append(macro(sa) - macro(sb))
    diffs.sort()
    return round(diffs[int(0.025 * n)], 4), round(diffs[int(0.975 * n)], 4)


for r in front:
    r["gap_to_best"] = round(top["macro_acc"] - r["macro_acc"], 4)
    r["gap_ci"] = [0.0, 0.0] if r is top else list(boot(top, r))
pick_cheap = next((r for r in front if r["gap_ci"][0] <= 0 <= r["gap_ci"][1]), top)
res = {"rule": __doc__, "candidates": [{k: v for k, v in r.items() if k != "_sc"} for r in sorted(rows, key=lambda r: r["usd_per_1k"] or 0)],
       "frontier": [{k: v for k, v in r.items() if k != "_sc"} for r in front],
       "advance_cheapest_within_noise": pick_cheap["model"], "advance_most_accurate": top["model"]}
json.dump(res, open(a.out, "w"), indent=1)
for r in front:
    print(f"{r['model']:45s} {r['contract']:6s} acc {r['macro_acc']:.3f} ${r['usd_per_1k']:.4f}/1k gap {r['gap_to_best']:+.3f} {r['gap_ci']}")
print("advance:", pick_cheap["model"], "|", top["model"])
