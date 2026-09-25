"""Summarise the prefix-continuation canary: exact-reproduction rate and mean similarity of the continuation to
the true second half, originals (public MASSIVE text) vs paraphrases (fresh, in no dataset), per instruction.
A memorising model scores higher on originals than on paraphrases, most of all under GUIDED.
usage: python3 canary/score_prefix.py"""
import glob, json, random, statistics
from pathlib import Path
H = Path(__file__).resolve().parent
out = {}
for f in sorted(glob.glob(str(H / "prefix__orig__*.jsonl"))):
    m = f.split("prefix__orig__")[1][:-6]
    for tag in ("orig", "para"):
        rs = [json.loads(l) for l in open(H / f"prefix__{tag}__{m}.jsonl")]
        for kind in ("general", "guided"):
            x = [r for r in rs if r["kind"] == kind and r.get("cont") is not None]
            out[f"{m}|{kind}|{tag}"] = {"n": len(x), "exact": sum(r["exact"] for r in x), "mean_ratio": round(statistics.mean(r["ratio"] for r in x), 4),
                                        "ratios": {r["id"]: r["ratio"] for r in x}}
res = {}
for key, v in out.items():
    m, kind, tag = key.split("|")
    if tag != "orig": continue
    p = out[f"{m}|{kind}|para"]
    common = sorted(set(v["ratios"]) & set(p["ratios"]))
    d = [v["ratios"][i] - p["ratios"][i] for i in common]
    rng = random.Random(0); boots = sorted(statistics.mean(rng.choice(d) for _ in d) for _ in range(5000))
    res[f"{m} {kind}"] = {"orig_exact": f"{v['exact']}/{v['n']}", "para_exact": f"{p['exact']}/{p['n']}",
                          "orig_mean_similarity": v["mean_ratio"], "para_mean_similarity": p["mean_ratio"],
                          "paired_diff": round(statistics.mean(d), 4), "diff_95ci": [round(boots[125], 4), round(boots[4875], 4)]}
json.dump(res, open(H / "prefix_summary.json", "w"), indent=1)
for k, v in res.items(): print(k, v)
