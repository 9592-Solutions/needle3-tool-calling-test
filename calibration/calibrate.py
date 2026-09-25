"""Needle 3 confidence operating points (DESIGN §7.3, §10 step 8; D1: depth 20 = shipped default only).

Reads ONLY the calibration partition (partitions/gold.jsonl, partition == "calibration") and the existing
config-side Needle outputs (runs/needle_config/out_{S0,S1}_{home,desk}.json, all on Intel fam 6 model 85).
No model is run. Writes calibration/CALIBRATION.json.

Policy under test (the executed scoreboard): the app executes what Needle returned (function_calls after the
engine's validation flags, harness/score.py needle_calls) when confidence >= t; otherwise it defers.
An empty return executes nothing whatever t is. A technical failure executes nothing.

Frozen rule (DESIGN §7.3): per app and schema, the LOWEST t (so the most coverage) whose accepted set on
calibration has >= 20 requests and an observed wrong-execution rate (wrong executions / executed) <= 5%.
Candidate thresholds are the distinct observed confidences of call-returning items. No such t -> "none":
the app executes nothing at that ceiling on calibration, and that is the finding (the vendor's example
threshold is never borrowed).
"""
import json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import score  # noqa: E402

CEIL, MIN_N, SEED = 0.05, 20, 20260922


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def rows_for(schema, app, respect_validation=True):
    gold = {}
    for l in open(ROOT / "partitions/gold.jsonl"):
        r = json.loads(l)
        if r["partition"] == "calibration" and r["app"] == app:
            gold[r["id"]] = r
    out = json.load(open(ROOT / f"runs/needle_config/out_{schema}_{app}.json"))
    assert not out["missing"]
    res = {r["id"]: r for r in out["results"] if r["id"] in gold}
    assert set(res) == set(gold), (schema, app, len(set(gold) - set(res)))
    rows = []
    for i, g in gold.items():
        r = res[i]
        assert "fam 6 model 85" in r["cpu"]
        p = r.get("parsed")
        calls = score.needle_calls(p, respect_validation=respect_validation)
        s = score.score_item(g["gold"], calls, f"{schema}-{app}")
        if s["outcome"] == "ambiguous":
            continue
        conf = p.get("confidence") if isinstance(p, dict) else None
        rows.append({"id": i, "stratum": g["stratum"], "outcome": s["outcome"], "returned": bool(calls),
                     "conf": conf, "empty_kind": score.empty_kind(p), "tf": calls is None})
    return rows


def at(rows, t, w=None):
    """w: optional per-stratum weights (sensitivity reading only; counts stay raw, rates are weighted)."""
    acc = [r for r in rows if r["returned"] and r["conf"] is not None and r["conf"] >= t]
    wrong = sum(r["outcome"] != "correct_action" for r in acc)
    n = len(rows)
    if w:
        W = lambda xs: sum(w[r["stratum"]] for r in xs)
        wacc = W(acc); wwrong = W([r for r in acc if r["outcome"] != "correct_action"])
        return {"threshold": t, "executed": len(acc), "risk_weighted": round(wwrong / wacc, 4) if wacc else None,
                "coverage_weighted": round(wacc / W(rows), 4)}
    return {"threshold": t, "executed": len(acc), "wrong_executed": wrong,
            "correct_executed": len(acc) - wrong,
            "risk": round(wrong / len(acc), 4) if acc else None, "risk_wilson95": wilson(wrong, len(acc)),
            "coverage_all": round(len(acc) / n, 4),
            "wrong_exec_per_request": round(wrong / n, 4),
            "deferred_returned": sum(r["returned"] and not (r["conf"] is not None and r["conf"] >= t) for r in rows)}


def reliability(rows):
    bins = [dict(lo=b / 10, hi=(b + 1) / 10, n=0, k=0, sconf=0.0) for b in range(10)]
    for r in rows:
        if not r["returned"] or r["conf"] is None:
            continue
        b = min(9, int(r["conf"] * 10))
        bins[b]["n"] += 1; bins[b]["k"] += r["outcome"] == "correct_action"; bins[b]["sconf"] += r["conf"]
    out = []
    for b in bins:
        out.append({"bin": [b["lo"], b["hi"]], "n": b["n"], "correct": b["k"],
                    "mean_conf": round(b["sconf"] / b["n"], 4) if b["n"] else None,
                    "acc": round(b["k"] / b["n"], 4) if b["n"] else None, "wilson95": wilson(b["k"], b["n"])})
    return out


def auroc(rows):
    ret = [r for r in rows if r["returned"] and r["conf"] is not None]
    pos = [r["conf"] for r in ret if r["outcome"] == "correct_action"]
    neg = [r["conf"] for r in ret if r["outcome"] != "correct_action"]
    if not pos or not neg:
        return None
    s = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return round(s / (len(pos) * len(neg)), 4)


def main():
    out = {"rule": {"ceiling": CEIL, "min_accepted": MIN_N, "risk": "wrong executions / executed",
                    "choose": "lowest observed threshold meeting both"}, "cells": {}}
    for schema in ("S1", "S0"):
        for app in ("home", "desk"):
            rows = rows_for(schema, app)
            cands = sorted({r["conf"] for r in rows if r["returned"] and r["conf"] is not None})
            curve = [at(rows, t) for t in cands]
            ok = [c for c in curve if c["executed"] >= MIN_N and c["risk"] <= CEIL]
            pick = ok[0] if ok else None
            best_risk_20 = min((c for c in curve if c["executed"] >= MIN_N), key=lambda c: (c["risk"], -c["executed"]), default=None)
            out["cells"][f"{schema}-{app}"] = {
                "n": len(rows), "strata": dict(sorted(Counter(r["stratum"] for r in rows).items())),
                "outcomes_proposal": dict(Counter(r["outcome"] for r in rows)),
                "empty_kinds": dict(Counter(r["empty_kind"] for r in rows if not r["returned"])),
                "returned": sum(r["returned"] for r in rows),
                "no_gate": at(rows, -1.0),
                "operating_point": pick,
                "lowest_risk_with_20_accepted": best_risk_20,
                "auroc_correct_vs_wrong_among_returned": auroc(rows),
                "reliability": reliability(rows),
                "curve": curve,
            }
    # Sensitivity readings, added AFTER the primary result above was seen (FREEZE.md §6); never the rule of record.
    out["sensitivity"] = {}
    for schema in ("S1", "S0"):
        for app in ("home", "desk"):
            key = f"{schema}-{app}"
            # (a) validation-flagged calls counted as returned (what function_calls holds before an app withholds)
            rows = rows_for(schema, app, respect_validation=False)
            cands = sorted({r["conf"] for r in rows if r["returned"] and r["conf"] is not None})
            curve = [at(rows, t) for t in cands]
            ok = [c for c in curve if c["executed"] >= MIN_N and c["risk"] <= CEIL]
            lr = min((c for c in curve if c["executed"] >= MIN_N), key=lambda c: (c["risk"], -c["executed"]), default=None)
            # (b) strata re-weighted to the sealed test's balance (six strata, equal weight), primary reading
            rows_p = rows_for(schema, app)
            cnt = Counter(r["stratum"] for r in rows_p)
            w = {k: 1.0 / v for k, v in cnt.items()}
            cands_p = sorted({r["conf"] for r in rows_p if r["returned"] and r["conf"] is not None})
            wc = [at(rows_p, t, w) for t in cands_p]
            okw = [c for c in wc if c["executed"] >= MIN_N and c["risk_weighted"] <= CEIL]
            lrw = min((c for c in wc if c["executed"] >= MIN_N), key=lambda c: (c["risk_weighted"], -c["executed"]), default=None)
            out["sensitivity"][key] = {
                "flagged_counted": {"outcomes_proposal": dict(Counter(r["outcome"] for r in rows)),
                                    "no_gate": at(rows, -1.0), "operating_point": ok[0] if ok else None,
                                    "lowest_risk_with_20_accepted": lr},
                "balanced_strata": {"strata_present": dict(sorted(cnt.items())), "no_gate": at(rows_p, -1.0, w),
                                    "operating_point": okw[0] if okw else None, "lowest_risk_with_20_accepted": lrw}}
    json.dump(out, open(ROOT / "calibration/CALIBRATION.json", "w"), indent=1)
    for k, v in out["sensitivity"].items():
        f = v["flagged_counted"]; b = v["balanced_strata"]
        print("SENS", k, "flagged:", f["outcomes_proposal"], "pick", f["operating_point"] and f["operating_point"]["threshold"],
              "lowest", f["lowest_risk_with_20_accepted"] and {x: f["lowest_risk_with_20_accepted"][x] for x in ("threshold","executed","wrong_executed","risk")})
        print("     balanced: no-gate", b["no_gate"], "pick", b["operating_point"], "lowest", b["lowest_risk_with_20_accepted"])
    for k, v in out["cells"].items():
        print(k, "n", v["n"], "returned", v["returned"], "proposal", v["outcomes_proposal"])
        print("   no gate:", {x: v["no_gate"][x] for x in ("executed", "wrong_executed", "risk")})
        print("   pick:", v["operating_point"] and {x: v["operating_point"][x] for x in ("threshold", "executed", "wrong_executed", "risk", "risk_wilson95")})
        lr = v["lowest_risk_with_20_accepted"]
        print("   lowest risk w/ >=20:", lr and {x: lr[x] for x in ("threshold", "executed", "wrong_executed", "risk")}, "auroc", v["auroc_correct_vs_wrong_among_returned"])


if __name__ == "__main__":
    main()
