# /// script
# requires-python = ">=3.11"
# dependencies = ["bm25s==0.3.9", "PyStemmer==3.1.0", "numpy"]
# ///
"""Step 5: tune the keyword baselines on DEV only (DESIGN §4.3) and score every baseline on dev.
K0 and K1 tune only tau (top-1 BM25 score floor), mu (vote margin) and k (neighbours); phrase lists and
extractor rules are never revised. Objective: the DESIGN §13 D6 axis (the same as the LLM frontier). Also scores always-decline and hassil (home) on dev, untuned.
Writes baselines/DEV-RESULTS.json. usage: uv run baselines/tune.py"""
import collections, itertools, json, os, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parent
sys.path.insert(0, str(H)); import bm25_arm as B  # noqa: E402
sys.path.insert(0, str(R / "harness")); import score  # noqa: E402
gold = [g for g in map(json.loads, open(R / "partitions" / "gold.jsonl"))]
dev = [g for g in gold if g["partition"] == "dev" and g["gold"] != "ambiguous"]
bank = [g for g in gold if g["partition"] == "lexical"]


def macro(res):
    return score.macro_cells([((g["app"], g["stratum"]), ok) for g, ok in res])


def evaluate(pred_fn, ver):
    res = []
    for g in dev:
        calls = pred_fn(g)
        s = score.score_item(g["gold"], calls, f"{ver}-{g['app']}")
        res.append((g, s["outcome"] in ("correct_action", "correct_nonaction")))
    return macro(res), sum(ok for _, ok in res) / len(res), res


out = {"dev_n": len(dev), "cells": dict(collections.Counter(f"{g['app']}/{g['stratum']}" for g in dev)), "arms": {}}
GRID = {"k": [1, 3, 5, 7, 11], "mu": [0, 1, 2], "tau_q": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}
for arm in ("K0", "K1", "K1-firstbank", "K1-firstbank-none"):
    for ver in ("S1", "S0"):
        routers = {}
        for app in ("home", "desk"):
            sid = f"{ver}-{app}"
            ob = [b for b in bank if b["app"] == app]
            docs = (B.k0_docs(sid) if arm == "K0" else B.k1_bank_docs(sid, ob) if arm == "K1"
                    else B.k1_docs(sid, ob, include_none=(arm == "K1-firstbank-none")))
            routers[app] = B.Router(sid, docs)
        # tau grid from the dev top-1 score distribution (quantiles), computed once per router
        tops = {app: sorted(r.route(g["text"], 1, 0, 0)[1]["top"] for g in dev if g["app"] == app) for app, r in routers.items()}
        best = None
        for k, mu, q in itertools.product(GRID["k"], GRID["mu"], GRID["tau_q"]):
            tau = {app: (t[int(q * (len(t) - 1))] if q else 0.0) for app, t in tops.items()}
            m, micro, _ = evaluate(lambda g: routers[g["app"]].predict(g["text"], k, tau[g["app"]], mu)[0], ver)
            if best is None or m > best["macro"]:
                best = {"k": k, "mu": mu, "tau_quantile": q, "tau": tau, "macro": round(m, 4), "micro": round(micro, 4)}
        out["arms"][f"{arm}-{ver}"] = {"tuned": best, "n_docs": {a: len(r.labels) for a, r in routers.items()}}
        print(arm, ver, best)
m, micro, _ = evaluate(lambda g: [], "S1")
out["arms"]["always-decline"] = {"macro": round(m, 4), "micro": round(micro, 4)}
print("always-decline", m, micro)
json.dump(out, open(H / "DEV-RESULTS.json", "w"), indent=1)
