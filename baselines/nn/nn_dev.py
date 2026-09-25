# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Embedding nearest-neighbour router, a DIAGNOSTIC on dev only (DESIGN §4.3): the K1 bank (intent-labelled act
examples, D8) embedded with bge-small-en-v1.5 on Modal; a request routes to its nearest bank example's tool when
cosine >= t, else nothing; arguments from the shared K0 extractor. Only t is tuned, on dev. It becomes an arm only
if it beats K1 by more than the noise.  usage: uv run baselines/nn/nn_dev.py"""
import json, sys
from pathlib import Path
import numpy as np
H = Path(__file__).resolve().parent; B = H.parent; R = B.parent
sys.path.insert(0, str(B / "k0")); import extractor  # noqa
sys.path.insert(0, str(R / "harness")); import score  # noqa
sys.path.insert(0, str(R / "contracts")); import mapping  # noqa
it = np.load(H / "items_bge_small.npz"); bk = np.load(H / "bank_bge_small.npz")
iv = dict(zip(it["ids"], it["vecs"])); bank = json.load(open(B / "k1_bank" / "bank.json"))
bvec = dict(zip(bk["ids"], bk["vecs"]))
tools = {a: {t["function"]["name"]: t for t in json.load(open(R / f"contracts/S1/{a}.json"))} for a in ("home", "desk")}
gold = [g for g in map(json.loads, open(R / "partitions/gold.jsonl")) if g["partition"] == "dev" and g["gold"] != "ambiguous"]
M = {a: np.stack([bvec[r["id"]] for r in bank[a]]) for a in bank}
def run(t):
    res = []
    for g in gold:
        a = g["app"]; sims = M[a] @ iv[g["id"]]; j = int(sims.argmax())
        calls = []
        if sims[j] >= t:
            tool = bank[a][j]["tool"]; args = extractor.extract(tools[a][tool], g["text"], mapping.FACT_LINE if a == "desk" else None)
            if args is not None: calls = [{"name": tool, "arguments": args}]
        s = score.score_item(g["gold"], calls, f"S1-{a}")
        res.append(((a, g["stratum"]), s["outcome"] in ("correct_action", "correct_nonaction")))
    return score.macro_cells(res)
grid = [round(x, 2) for x in np.arange(0.5, 0.96, 0.05)]
scores = {t: round(run(t), 4) for t in grid}
best = max(scores, key=scores.get)
out = {"grid": scores, "best_t": best, "macro": scores[best]}
json.dump(out, open(H / "NN-DEV.json", "w"), indent=1); print(out)
