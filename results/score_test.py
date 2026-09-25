"""Needle 3: the single scoring of the sealed run (DESIGN §10 step 10; FREEZE.md §4-§8, §11). Fits nothing on test.

Run ONCE, after every arm has finished and after the raw outputs have been read end to end
(results/audit_dump.py writes the per-cell reading sample; it prints no aggregate):
  uv run --no-project --with numpy --with jsonschema==4.26.0 python results/score_test.py
Writes results/SCORES.json (every number) and results/EXAMPLES.json (FREEZE §11 draws). Prints a digest.

Inputs: runs/sealed/out/** (raw outputs), sealed-v2/{test,diagnostics,bandF}-key.jsonl.
The salt is never read.

Key adapter (the key files' field names were not known when this was written, because no key file is opened before
step 10): per record, `id`, `app`, `gold` (a list of acceptable answers, each a list of {"action","args"}, or
"ambiguous", the config-side gold format), `stratum`; family and phrasing are taken from the first present alias
below; per-variant gold from top-level fields named like the variant (V-REL, V-ROOMREQ, V-VENDOR, V-TIMER,
V-COUNT-6/10/20, any case, - or _) or from a dict field of such entries. If a required field cannot be resolved the
script stops and names the record's fields; a change to the ALIASES below is a field-name fix, never a change of
rule, and is committed and reported as such.

Rules applied (FREEZE): outcome per item by harness/score.py (proposal) and harness/execute.py (executed); statistic
of record = exact correctness (correct action or correct non-action) macro-averaged over the (app x stratum) cells,
ambiguous excluded; technical failures count as not correct and never as refusals; an LLM item unserved on every
pass (HTTP 429 as its last attempt, no 200 from the pinned host) is excluded from that arm and from any paired
comparison involving it, counted apart, and flags every number of the arm when > 2% of its test items; intervals
are paired, stratified, family-clustered percentile bootstraps (10,000 resamples, a fresh
numpy.random.default_rng(20260922) per quantity, both phrasings of a drawn family together); cross-check = exact
two-sided sign test at family level (ties dropped); Holm over the five primary sign-test p-values; zero observed
errors also get the one-sided 95% binomial bound 1 - 0.05**(1/n).
"""
import hashlib, json, math, os, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parent
ROOT = R.parent
S = ROOT / "runs" / "sealed"
# The three overrides exist only for results/smoke_score_test.py (config-side data); the real run uses the defaults.
O = Path(os.environ.get("NEEDLE3_SEALED_OUT", S / "out"))
KEYS = Path(os.environ.get("NEEDLE3_KEYS", ROOT / "sealed-v2"))
INP = Path(os.environ.get("NEEDLE3_INPUTS", S / "inputs"))
R = Path(os.environ.get("NEEDLE3_RESULTS_DIR", R))
sys.path.insert(0, str(ROOT / "harness"))
import score, execute  # noqa: E402

SEED, B = 20260922, 10000
CPU = "GenuineIntel fam 6 model 85"
HOSTS = {"llm-a": "Sail Research", "llm-named": "OpenInference"}
STRATA = ["A1", "A2", "A3", "N1", "N2", "N3"]
APPS = ["home", "desk"]
CORRECT = ("correct_action", "correct_nonaction")
GRID = [0.5, 0.9, 0.99]
ALIASES = {"family": ["family", "family_id", "fam", "family_key", "scenario", "scenario_id"],
           "phrasing": ["phrasing", "phrase", "p", "source_kind", "phrasing_kind", "kind", "variant", "role"]}
VARIANTS = ["V-REL", "V-ROOMREQ", "V-VENDOR", "V-TIMER", "V-TIMER-S", "V-TIMER-U", "V-COUNT-6", "V-COUNT-10", "V-COUNT-20"]


# ---------------------------------------------------------------- keys
def _norm(k):
    return k.upper().replace("_", "-")


def _variant_gold(rec):
    out = {}
    for k, v in rec.items():
        if _norm(k) in VARIANTS:
            out[_norm(k)] = v
        elif isinstance(v, dict) and any(_norm(x) in VARIANTS for x in v):
            for x, g in v.items():
                if _norm(x) in VARIANTS:
                    out[_norm(x)] = g
    if "V-TIMER" in out:
        out.setdefault("V-TIMER-S", out["V-TIMER"]); out.setdefault("V-TIMER-U", out["V-TIMER"])
    return out


def _pick(rec, field, required):
    for a in ALIASES[field]:
        if a in rec and rec[a] not in (None, ""):
            return rec[a]
    if required:
        raise SystemExit(f"key adapter: no {field} field in record {rec.get('id')}; fields: {sorted(rec)}")
    return None


def _phr(v):
    s = str(v).upper()
    return "P1" if "P1" in s or s in ("CROWD", "REAL", "1") else "P2" if "P2" in s or s in ("FRESH", "WRITTEN", "2") else s


def load_keys(name, need_family):
    out = {}
    for l in open(KEYS / f"{name}-key.jsonl"):
        r = json.loads(l)
        for f in ("id", "app", "gold"):
            if f not in r:
                raise SystemExit(f"key adapter: {name} record lacks {f}; fields: {sorted(r)}")
        # Field-name fix after the keys were opened (FREEZE-ADDENDUM §2.12): the sealed keys hold gold as a dict
        # {"main": <gold>, "V-REL": <gold>, ...}; main gold is gold["main"], the variant entries are read below as before.
        g = r["gold"]["main"] if isinstance(r["gold"], dict) else r["gold"]
        out[r["id"]] = {"id": r["id"], "app": r["app"], "gold": g, "stratum": r.get("stratum"),
                        "family": _pick(r, "family", need_family), "phrasing": _phr(_pick(r, "phrasing", need_family)),
                        "variants": _variant_gold(r), "diagnostic": r.get("diagnostic") or r.get("diagnostics"),
                        "raw_fields": sorted(r)}
        if need_family and out[r["id"]]["stratum"] not in STRATA:
            raise SystemExit(f"key adapter: stratum {out[r['id']]['stratum']!r} on {r['id']}")
    return out


# ---------------------------------------------------------------- predictions
def needle_file(name):
    p = O / "needle" / f"{name}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    res = {}
    for r in d["results"]:
        if r.get("rep", 0) != 0:
            continue
        if CPU not in r["cpu"]:
            raise SystemExit(f"{name}: item {r['id']} ran on {r['cpu']}")
        p_ = r.get("parsed")
        calls = score.needle_calls(p_)
        loose = score.needle_calls(p_, respect_validation=False)
        kind = None
        if r["rc"] != 0:
            kind = "timeout" if r["rc"] == "timeout" else f"exit {r['rc']}"
            calls = loose = None
        elif calls is None:
            if isinstance(p_, dict) and p_.get("error"):
                e = str(p_.get("error")); kind = "truncated" if "truncat" in e else (p_.get("error_code") or "engine error")
            else:
                kind = "unparseable"
        res[r["id"]] = {"pred": calls, "pred_loose": loose, "tf": kind,
                        "conf": p_.get("confidence") if isinstance(p_, dict) else None,
                        "empty_kind": score.empty_kind(p_), "raw": p_, "stderr": r.get("stderr", "")[-300:]}
    res["__missing__"] = d.get("missing", [])
    return res


def llm_file(arm, name):
    p = O / "llm" / arm / f"{name}.jsonl"
    if not p.exists():
        return None
    recs = defaultdict(list)
    for l in open(p):
        r = json.loads(l); recs[r["id"]].append(r)
    res = {}
    for i, rs in recs.items():
        ok = [r for r in rs if r.get("http") == 200 and r.get("served_by") == HOSTS[arm]]
        if ok:
            r = ok[-1]
            res[i] = {"pred": r.get("pred"), "tf": None if r.get("pred") is not None else f"parse {r.get('parse')}",
                      "conf": None, "raw": r.get("response"), "cost": (r.get("usage") or {}).get("cost")}
        elif all(r.get("http") == 429 or (r.get("http") == 200 and r.get("served_by") != HOSTS[arm]) for r in rs):
            res[i] = {"unserved": True, "raw": rs[-1].get("body")}
        else:
            last = rs[-1]
            res[i] = {"pred": None, "tf": f"http {last.get('http')} {str(last.get('error') or last.get('body'))[:120]}",
                      "conf": None, "raw": last.get("body") or last.get("error")}
    return res


def base_file(name):
    p = O / "baselines" / f"{name}.jsonl"
    if not p.exists():
        return None
    res = {}
    for l in open(p):
        r = json.loads(l)
        res[r["id"]] = {"pred": r["pred"], "tf": None if r["pred"] is not None else "crash", "conf": None, "raw": r.get("trace")}
    return res


def decline(ids):
    return {i: {"pred": [], "tf": None, "conf": None, "raw": None} for i in ids}


# ---------------------------------------------------------------- scoring
def score_run(keys, preds, schema_of, gold_of=lambda k: k["gold"], validators=None, threshold=None):
    """-> {id: row}. schema_of(app) gives the schema id. Items without a prediction are 'missing'."""
    rows = {}
    for i, k in keys.items():
        g = gold_of(k)
        if g is None:
            continue
        sid = schema_of(k["app"])
        p = (preds or {}).get(i)
        base = {"id": i, "app": k["app"], "stratum": k["stratum"], "family": k["family"], "phrasing": k["phrasing"]}
        if p is None:
            rows[i] = {**base, "outcome": "missing"}; continue
        if p.get("unserved"):
            rows[i] = {**base, "outcome": "unserved"}; continue
        s = score.score_item(g, p["pred"], sid)
        row = {**base, "outcome": s["outcome"], "tf": p.get("tf"), "conf": p.get("conf"), "returned": bool(p["pred"]),
               "empty_kind": p.get("empty_kind")}
        if validators is not None and s["outcome"] != "ambiguous":
            ex = execute.execute_item(g, p["pred"], sid, validators[sid], conf=p.get("conf"), threshold=threshold)
            row.update(ex_outcome=ex["outcome"], executed=ex["executed"], deferred=ex["deferred"], invalid=ex["invalid"])
        rows[i] = row
    return rows


def ok(row):
    return row["outcome"] in CORRECT


def scored(rows):
    return {i: r for i, r in rows.items() if r["outcome"] not in ("ambiguous", "unserved", "missing")}


def macro(rows):
    cells = defaultdict(list)
    for r in scored(rows).values():
        cells[(r["app"], r["stratum"])].append(ok(r))
    if not cells:
        return None
    return float(np.mean([np.mean(v) for v in cells.values()]))


def summary(rows):
    sc = scored(rows)
    cells = defaultdict(list)
    for r in sc.values():
        cells[(r["app"], r["stratum"])].append(r)
    out = {"n": len(sc), "stat_of_record": macro(rows), "outcomes": dict(Counter(r["outcome"] for r in rows.values())),
           "per_app": {}, "cells": {}}
    for app in APPS:
        a = [np.mean([ok(r) for r in cells[(app, s)]]) for s in STRATA[:3] if cells.get((app, s))]
        n = [np.mean([ok(r) for r in cells[(app, s)]]) for s in STRATA[3:] if cells.get((app, s))]
        out["per_app"][app] = {"macro": float(np.mean(a + n)) if a + n else None, "act_mean": float(np.mean(a)) if a else None,
                               "noact_mean": float(np.mean(n)) if n else None}
    for (app, s), rs in sorted(cells.items()):
        k = sum(ok(r) for r in rs); n = len(rs)
        c = {"k": k, "n": n, "acc": k / n, "outcomes": dict(Counter(r["outcome"] for r in rs)),
             "tf_kinds": dict(Counter(r["tf"] for r in rs if r["outcome"] == "technical_failure"))}
        if k == n:
            c["errors_zero_upper95"] = 1 - 0.05 ** (1 / n)
        out["cells"][f"{app}/{s}"] = c
    act = [ok(r) for r in sc.values() if r["stratum"].startswith("A")]
    na = [ok(r) for r in sc.values() if r["stratum"].startswith("N")]
    out["act_mean"] = float(np.mean([out["per_app"][a]["act_mean"] for a in APPS if out["per_app"][a]["act_mean"] is not None]))
    out["noact_mean"] = float(np.mean([out["per_app"][a]["noact_mean"] for a in APPS if out["per_app"][a]["noact_mean"] is not None]))
    out["plain_accuracy"] = float(np.mean(act + na)) if act + na else None
    return out


# ---------------------------------------------------------------- bootstrap and sign test
def _cells_matrix(rows_list, keep):
    """For each (app, stratum) cell: families x arms matrices of correct counts and item counts over the items in `keep`."""
    cells = defaultdict(lambda: defaultdict(lambda: [[0] * len(rows_list), [0] * len(rows_list)]))
    for i in keep:
        r0 = rows_list[0][i]
        fam = cells[(r0["app"], r0["stratum"])][r0["family"]]
        for j, rows in enumerate(rows_list):
            fam[0][j] += ok(rows[i]); fam[1][j] += 1
    return {c: (np.array([v[0] for v in fams.values()], float), np.array([v[1] for v in fams.values()], float))
            for c, fams in cells.items()}


def boot(rows_list, contrast, keep=None, cell_filter=None):
    """Paired stratified family-clustered bootstrap of contrast(per-arm macro vector). Returns point, [lo, hi]."""
    if keep is None:
        keep = set.intersection(*[set(scored(r)) for r in rows_list])
    cm = _cells_matrix(rows_list, keep)
    if cell_filter:
        cm = {c: v for c, v in cm.items() if cell_filter(c)}
    rng = np.random.default_rng(SEED)
    acc_sum = np.zeros((B, len(rows_list)))
    pt = []
    for c in sorted(cm):
        k, n = cm[c]
        pt.append(k.sum(0) / n.sum(0))
        idx = rng.integers(0, len(k), size=(B, len(k)))
        acc_sum += k[idx].sum(1) / n[idx].sum(1)
    macros = acc_sum / len(cm)
    point = contrast(np.mean(pt, 0))
    dist = np.array([contrast(m) for m in macros])
    lo, hi = np.percentile(dist, [2.5, 97.5])
    return {"point": float(point), "ci95": [float(lo), float(hi)], "n_items": len(keep),
            "n_families": int(sum(len(v[0]) for v in cm.values())), "excludes_zero": bool(lo > 0 or hi < 0)}


def sign_test(rows_list, fam_score, keep):
    """fam_score(list of per-arm correct counts for a family) -> signed number; exact two-sided binomial on non-ties."""
    fams = defaultdict(lambda: [0] * len(rows_list))
    for i in keep:
        r0 = rows_list[0][i]
        f = fams[(r0["app"], r0["stratum"], r0["family"])]
        for j, rows in enumerate(rows_list):
            f[j] += ok(rows[i])
    d = [fam_score(v) for v in fams.values()]
    pos, neg = sum(x > 0 for x in d), sum(x < 0 for x in d)
    n = pos + neg
    if n == 0:
        return {"pos": 0, "neg": 0, "ties": len(d), "p": 1.0}
    k = min(pos, neg)
    p = min(1.0, 2 * sum(math.comb(n, x) for x in range(k + 1)) / 2 ** n)
    return {"pos": pos, "neg": neg, "ties": len(d) - n, "p": p}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i])); adj[i] = run
    return adj


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


# ---------------------------------------------------------------- executed scoreboard and confidence
def executed(rows):
    out = {}
    for app in APPS + ["all"]:
        rs = [r for r in scored(rows).values() if (app == "all" or r["app"] == app) and "ex_outcome" in r]
        ex = [r for r in rs if r["executed"]]
        wrong = sum(r["ex_outcome"] == "wrong_call" for r in ex)
        out[app] = {"n": len(rs), "executed": len(ex), "wrong_executions": wrong, "wrong_rate": wrong / len(ex) if ex else None,
                    "wilson": wilson(wrong, len(ex)), "deferred": sum(r["deferred"] for r in rs),
                    "invalid_blocked": sum(r["invalid"] for r in rs),
                    "correct_proposals_forgone": sum(r["deferred"] and r["outcome"] == "correct_action" for r in rs),
                    "exact_correct_executed_board": sum(r["ex_outcome"] in CORRECT for r in rs),
                    "tech_fail": sum(r["ex_outcome"] == "technical_failure" for r in rs)}
    return out


def confidence_block(rows):
    out = {}
    for app in APPS:
        ret = [r for r in scored(rows).values() if r["app"] == app and r["returned"]]
        withc = [r for r in ret if r["conf"] is not None]
        good = [r["conf"] for r in withc if r["outcome"] == "correct_action"]
        bad = [r["conf"] for r in withc if r["outcome"] != "correct_action"]
        au = None
        if good and bad:
            au = float(np.mean([(g > b) + 0.5 * (g == b) for g in good for b in bad]))
        bins = []
        for b in range(10):
            lo, hi = b / 10, (b + 1) / 10
            inb = [r for r in withc if (lo <= r["conf"] < hi) or (b == 9 and r["conf"] == 1.0)]
            k = sum(r["outcome"] == "correct_action" for r in inb)
            bins.append({"bin": [lo, hi], "n": len(inb), "mean_conf": float(np.mean([r["conf"] for r in inb])) if inb else None,
                         "correct": k, "frac_correct": k / len(inb) if inb else None, "wilson": wilson(k, len(inb))})
        curve = []
        for t in sorted({r["conf"] for r in withc}):
            acc = [r for r in withc if r["conf"] >= t]
            w = sum(r["outcome"] != "correct_action" for r in acc)
            curve.append({"t": t, "accepted": len(acc), "wrong": w, "risk": w / len(acc)})
        out[app] = {"returned": len(ret), "conf_none_among_returned": len(ret) - len(withc), "auroc": au,
                    "n_correct": len(good), "n_wrong": len(bad), "reliability": bins, "risk_coverage": curve}
    return out


def tf_breakdown(rows):
    return dict(Counter(r["tf"] for r in scored(rows).values() if r["outcome"] == "technical_failure"))


# ---------------------------------------------------------------- main
def main():
    test = load_keys("test", True)
    diag = load_keys("diagnostics", False)
    band = load_keys("bandF", False)
    for i, k in diag.items():
        k["stratum"] = k["stratum"] or "?"
    val = {}
    def V(sid):
        if sid not in val:
            f = (ROOT / "contracts" / sid.split("-")[0] / f"{sid.split('-', 1)[1]}.json") if sid[:2] in ("S0", "S1") \
                else ROOT / "contracts" / "variants" / f"{sid}.json"
            val[sid] = execute.tools_for(f)
        return val
    out = {"meta": {"seed": SEED, "resamples": B, "keys": {n: len(k) for n, k in (("test", test), ("diag", diag), ("bandF", band))},
                    "key_fields": {n: sorted({f for k in kk.values() for f in k["raw_fields"]}) for n, kk in
                                   (("test", test), ("diag", diag), ("bandF", band))}}}

    # ---- load every arm on test and band F
    def join(a, b):
        if a is None or b is None:
            return None
        return {**{k: v for k, v in a.items() if k != "__missing__"}, **{k: v for k, v in b.items() if k != "__missing__"}}
    P = {}
    for ver in ("S1", "S0"):
        P[("needle", ver)] = join(needle_file(f"needle_{ver}_home_test"), needle_file(f"needle_{ver}_desk_test"))
        for arm in ("llm-a", "llm-named"):
            P[(arm, ver)] = join(llm_file(arm, f"test_{ver}_home"), llm_file(arm, f"test_{ver}_desk"))
        for arm in ("K0", "K1", "K1-firstbank", "K1-firstbank-none"):
            P[(arm, ver)] = join(base_file(f"{arm}_{ver}_home_test"), base_file(f"{arm}_{ver}_desk_test"))
        P[("always-decline", ver)] = decline(test)
    P[("hassil", "S1")] = base_file("hassil_S1_home_test")
    PB = {"needle": join(needle_file("needle_S1_home_bandF"), needle_file("needle_S1_desk_bandF")),
          "hassil": base_file("hassil_S1_home_bandF"), "always-decline": decline(band)}
    for arm in ("llm-a", "llm-named"):
        PB[arm] = join(llm_file(arm, "bandF_S1_home"), llm_file(arm, "bandF_S1_desk"))
    for arm in ("K0", "K1", "K1-firstbank", "K1-firstbank-none"):
        PB[arm] = join(base_file(f"{arm}_S1_home_bandF"), base_file(f"{arm}_S1_desk_bandF"))

    # ---- proposal + executed (no gate) on test
    RW = {}
    for (arm, ver), preds in P.items():
        if preds is None:
            continue
        keys = {i: k for i, k in test.items() if k["app"] == "home"} if arm == "hassil" else test
        schema_of = lambda app, ver=ver: f"{ver}-{app}"
        vals = {f"{ver}-{a}": V(f"{ver}-{a}")[f"{ver}-{a}"] for a in APPS}
        RW[(arm, ver)] = score_run(keys, preds, schema_of, validators=vals)
    arms_out = {}
    for (arm, ver), rows in RW.items():
        s = summary(rows)
        s["executed"] = executed(rows)
        s["tf_kinds"] = tf_breakdown(rows)
        s["unserved"] = sum(r["outcome"] == "unserved" for r in rows.values())
        s["missing"] = sum(r["outcome"] == "missing" for r in rows.values())
        s["unserved_flag"] = s["unserved"] > 0.02 * len(rows)
        s["boot_own"] = boot([rows], lambda m: m[0])
        arms_out[f"{arm}|{ver}"] = s
    out["arms"] = arms_out

    # ---- Needle specifics: empty kinds, secondary row, D4 truncated in no-act strata, executed grid, confidence
    nd = {}
    for ver in ("S1", "S0"):
        rows = RW[("needle", ver)]
        loose = {i: {**p, "pred": p["pred_loose"]} for i, p in P[("needle", ver)].items()}
        rl = score_run(test, loose, lambda app: f"{ver}-{app}")
        grid = {}
        vals = {f"{ver}-{a}": V(f"{ver}-{a}")[f"{ver}-{a}"] for a in APPS}
        for t in GRID:
            grid[str(t)] = executed(score_run(test, P[("needle", ver)], lambda app: f"{ver}-{app}", validators=vals, threshold=t))
        frozen = executed(score_run(test, P[("needle", ver)], lambda app: f"{ver}-{app}", validators=vals, threshold=float("inf")))
        nd[ver] = {"empty_kinds": {app: dict(Counter(r["empty_kind"] for r in scored(rows).values() if r["app"] == app and not r["returned"]
                                                      and r["outcome"] != "technical_failure")) for app in APPS},
                   "secondary_validation_flagged_as_returned": summary(rl),
                   "truncated_in_noact": {f"{r_app}/{s}": {"truncated": sum(1 for r in scored(rows).values() if r["app"] == r_app and r["stratum"] == s and r["tf"] == "truncated"),
                                                          "correct_nonaction": sum(1 for r in scored(rows).values() if r["app"] == r_app and r["stratum"] == s and r["outcome"] == "correct_nonaction")}
                                          for r_app in APPS for s in STRATA[3:]},
                   "executed_no_gate": executed(rows), "executed_frozen_operating_point_none": frozen,
                   "executed_descriptive_grid": grid, "confidence": confidence_block(rows)}
    out["needle"] = nd

    # ---- the five primary comparisons (S1 unless named)
    N1, N0 = RW[("needle", "S1")], RW[("needle", "S0")]
    A1, A0 = RW[("llm-a", "S1")], RW[("llm-a", "S0")]
    comps = [("1 needle vs llm-a (S1)", [N1, A1], lambda m: m[0] - m[1], lambda v: v[0] - v[1]),
             ("2 needle vs K1 (S1)", [N1, RW[("K1", "S1")]], lambda m: m[0] - m[1], lambda v: v[0] - v[1]),
             ("3 needle vs K0 (S1)", [N1, RW[("K0", "S1")]], lambda m: m[0] - m[1], lambda v: v[0] - v[1]),
             ("4 needle S1 minus needle S0", [N1, N0], lambda m: m[0] - m[1], lambda v: v[0] - v[1]),
             ("5 (needle S1-S0) minus (llm-a S1-S0)", [N1, N0, A1, A0], lambda m: (m[0] - m[1]) - (m[2] - m[3]),
              lambda v: (v[0] - v[1]) - (v[2] - v[3]))]
    prim = []
    for name, rl, con, fs in comps:
        keep = set.intersection(*[set(scored(r)) for r in rl])
        b = boot(rl, con, keep)
        st = sign_test(rl, fs, keep)
        prim.append({"comparison": name, **b, "sign_test": st})
    for p, a in zip(prim, holm([p["sign_test"]["p"] for p in prim])):
        p["sign_test"]["p_holm"] = a
    out["primary"] = prim

    # ---- reported, not ranked: needle vs the other arms, and D8's rejected banks beside K1
    rep = []
    for other in ("llm-named", "K1-firstbank", "K1-firstbank-none", "always-decline"):
        rl = [N1, RW[(other, "S1")]]
        keep = set.intersection(*[set(scored(r)) for r in rl])
        rep.append({"comparison": f"needle vs {other} (S1)", **boot(rl, lambda m: m[0] - m[1], keep),
                    "sign_test": sign_test(rl, lambda v: v[0] - v[1], keep)})
    rl = [RW[("needle", "S1")], RW[("hassil", "S1")]]
    keep = set.intersection(*[set(scored(r)) for r in rl])
    rep.append({"comparison": "needle vs hassil (S1, home only)", **boot(rl, lambda m: m[0] - m[1], keep),
                "sign_test": sign_test(rl, lambda v: v[0] - v[1], keep)})
    for ver in ("S1", "S0"):
        rl = [RW[("llm-a", ver)], RW[("llm-named", ver)]]
        keep = set.intersection(*[set(scored(r)) for r in rl])
        rep.append({"comparison": f"llm-a vs llm-named ({ver})", **boot(rl, lambda m: m[0] - m[1], keep)})
    out["reported_not_ranked"] = rep

    # ---- per-app intervals for the primary pairs (FREEZE §7: per app, never alone)
    per_app = []
    for name, rl, con, fs in comps:
        for app in APPS:
            keep = {i for i in set.intersection(*[set(scored(r)) for r in rl]) if test[i]["app"] == app}
            per_app.append({"comparison": name, "app": app, **boot(rl, con, keep)})
    out["primary_per_app"] = per_app

    # ---- canary on test (P1 crowd minus P2 fresh), DiD against K0
    can = []
    ph = lambda rows, p: {i for i, r in scored(rows).items() if r["phrasing"] == p}
    K0r = RW[("K0", "S1")]
    for arm in ("needle", "llm-a", "llm-named", "K1", "K0", "hassil"):
        rows = RW[(arm, "S1")]
        rl = [rows, rows, K0r, K0r]
        # paired within family: the P1 and P2 of each family; a bootstrap over families of acc(P1)-acc(P2)
        pairs = defaultdict(dict)
        for i, r in scored(rows).items():
            if i in scored(K0r):
                pairs[(r["app"], r["stratum"], r["family"])][r["phrasing"]] = i
        fams = [v for v in pairs.values() if "P1" in v and "P2" in v]
        def gap(fs, rr):
            return np.mean([ok(rr[f["P1"]]) for f in fs]) - np.mean([ok(rr[f["P2"]]) for f in fs])
        if not fams:
            can.append({"arm": arm, "n_families": 0}); continue
        by_cell = defaultdict(list)
        for f in fams:
            by_cell[(test[f["P1"]]["app"], test[f["P1"]]["stratum"])].append(f)
        rng = np.random.default_rng(SEED)
        cells = sorted(by_cell)
        dist_g, dist_d = [], []
        mats = {c: np.array([[ok(rows[f["P1"]]), ok(rows[f["P2"]]), ok(K0r[f["P1"]]), ok(K0r[f["P2"]])] for f in by_cell[c]], float) for c in cells}
        draws = {c: rng.integers(0, len(mats[c]), size=(B, len(mats[c]))) for c in cells}
        for bi in range(B):
            m = np.concatenate([mats[c][draws[c][bi]] for c in cells])
            g = m[:, 0].mean() - m[:, 1].mean(); gk = m[:, 2].mean() - m[:, 3].mean()
            dist_g.append(g); dist_d.append(g - gk)
        allm = np.concatenate([mats[c] for c in cells])
        g0 = allm[:, 0].mean() - allm[:, 1].mean(); d0 = g0 - (allm[:, 2].mean() - allm[:, 3].mean())
        can.append({"arm": arm, "n_families": len(fams), "acc_P1": float(allm[:, 0].mean()), "acc_P2": float(allm[:, 1].mean()),
                    "gap_P1_minus_P2": float(g0), "gap_ci95": [float(x) for x in np.percentile(dist_g, [2.5, 97.5])],
                    "did_vs_K0": float(d0), "did_ci95": [float(x) for x in np.percentile(dist_d, [2.5, 97.5])]})
    out["canary"] = can

    # ---- band F: per request, every arm, S1
    bf = []
    for i, k in sorted(band.items()):
        row = {"id": i, "app": k["app"], "gold_ambiguous": k["gold"] == "ambiguous", "arms": {}}
        for arm, preds in PB.items():
            if preds is None or (arm == "hassil" and k["app"] != "home"):
                continue
            p = preds.get(i)
            if p is None:
                row["arms"][arm] = {"outcome": "missing"}; continue
            if p.get("unserved"):
                row["arms"][arm] = {"outcome": "unserved"}; continue
            s = score.score_item(k["gold"], p["pred"], f"S1-{k['app']}")
            row["arms"][arm] = {"outcome": s["outcome"], "pred": p["pred"], "conf": p.get("conf"), "tf": p.get("tf")}
        bf.append(row)
    out["bandF"] = {"requests": bf, "counts": {arm: dict(Counter(r["arms"][arm]["outcome"] for r in bf if arm in r["arms"]))
                                              for arm in PB}}

    # ---- diagnostics
    dg = {}
    def gold_variant(v):
        return lambda k: k["variants"].get(v)
    def main_gold(k):
        return k["gold"]
    diagS1 = {"needle": join(needle_file("needle_S1_home_diag"), needle_file("needle_S1_desk_diag"))}
    for arm in ("llm-a", "llm-named"):
        diagS1[arm] = join(llm_file(arm, "diag_S1_home"), llm_file(arm, "diag_S1_desk"))
    def add(name, arm, keys, preds, schema_of, gold_of, ref_preds=None, ref_schema_of=None, ref_gold_of=None):
        if preds is None:
            dg.setdefault(name, {})[arm] = {"not_run": True}; return
        rows = score_run(keys, preds, schema_of, gold_of)
        rec = {"summary": {"n": len(scored(rows)), "k": sum(ok(r) for r in scored(rows).values()),
                           "outcomes": dict(Counter(r["outcome"] for r in rows.values())), "tf_kinds": tf_breakdown(rows)}}
        for app in APPS:
            sr = [r for r in scored(rows).values() if r["app"] == app]
            if sr:
                rec[app] = {"n": len(sr), "k": sum(ok(r) for r in sr), "outcomes": dict(Counter(r["outcome"] for r in sr))}
        if ref_preds is not None:
            ref = score_run(keys, ref_preds, ref_schema_of, ref_gold_of or main_gold)
            both = [i for i in scored(rows) if i in scored(ref)]
            rec["reference_S1_same_items"] = {"n": len(both), "k_variant": sum(ok(rows[i]) for i in both),
                                              "k_reference": sum(ok(ref[i]) for i in both),
                                              "variant_only_right": sum(ok(rows[i]) and not ok(ref[i]) for i in both),
                                              "reference_only_right": sum(ok(ref[i]) and not ok(rows[i]) for i in both)}
        dg.setdefault(name, {})[arm] = rec
    home_all = {**{i: k for i, k in test.items() if k["app"] == "home"}, **{i: k for i, k in diag.items() if k["app"] == "home"}}
    ref_home = {arm: join({k: v for k, v in (P[(arm, "S1")] or {}).items()}, diagS1.get(arm) or {}) for arm in ("needle", "llm-a", "llm-named")}
    for v, stem, sid in (("V-REL", "rel", "home-rel"), ("V-ROOMREQ", "roomreq", "home-roomreq")):
        keys = {i: k for i, k in home_all.items() if k["variants"].get(v) is not None}
        add(v, "needle", keys, needle_file(f"needle_{stem}_home_relroom"), lambda app, sid=sid: sid, gold_variant(v),
            ref_home["needle"], lambda app: "S1-home")
        for arm in ("llm-a", "llm-named"):
            add(v, arm, keys, llm_file(arm, f"{stem}_home"), lambda app, sid=sid: sid, gold_variant(v), ref_home[arm], lambda app: "S1-home")
    for c in (6, 10, 20):
        v = f"V-COUNT-{c}"
        keys = {i: k for i, k in diag.items() if k["variants"].get(v) is not None}
        add(v, "needle", keys, join(needle_file(f"needle_count{c}_home_diag"), needle_file(f"needle_count{c}_desk_diag")),
            lambda app, c=c: f"{app}-count{c}", gold_variant(v), diagS1["needle"], lambda app: f"S1-{app}")
    for v, stem in (("V-RENAME", "renamed"), ("V-DISPATCH", "dispatch")):
        keys = dict(diag)
        add(v, "needle", keys, join(needle_file(f"needle_{stem}_home_diag"), needle_file(f"needle_{stem}_desk_diag")),
            lambda app, stem=stem: f"{app}-{stem}", main_gold, diagS1["needle"], lambda app: f"S1-{app}")
        for arm in ("llm-a", "llm-named"):
            add(v, arm, keys, join(llm_file(arm, f"{stem}_home"), llm_file(arm, f"{stem}_desk")), lambda app, stem=stem: f"{app}-{stem}",
                main_gold, diagS1[arm], lambda app: f"S1-{app}")
    for v, stem, sid in (("V-TIMER-S", "timerS", "desk-timer-seconds"), ("V-TIMER-U", "timerU", "desk-timer-units")):
        keys = {i: k for i, k in diag.items() if k["variants"].get(v) is not None}
        add(v, "needle", keys, needle_file(f"needle_{stem}_desk_diag"), lambda app, sid=sid: sid, gold_variant(v), diagS1["needle"], lambda app: "S1-desk")
        for arm in ("llm-a", "llm-named"):
            add(v, arm, keys, llm_file(arm, f"{stem}_desk"), lambda app, sid=sid: sid, gold_variant(v), diagS1[arm], lambda app: "S1-desk")
    keys = {i: k for i, k in diag.items() if k["variants"].get("V-VENDOR") is not None}
    add("V-VENDOR", "needle", keys, needle_file("needle_vendor_home_diag"), lambda app: "vendor-smart_home", gold_variant("V-VENDOR"))
    for arm in ("llm-a", "llm-named"):
        add("V-VENDOR", arm, keys, llm_file(arm, "vendor_home"), lambda app: "vendor-smart_home", gold_variant("V-VENDOR"))
    add("V-TRIGGERS (anchors)", "needle", dict(diag), join(needle_file("needle_triggers_home_diag"), needle_file("needle_triggers_desk_diag")),
        lambda app: f"S1-{app}", main_gold, diagS1["needle"], lambda app: f"S1-{app}")
    trig_rows = None
    tp = join(needle_file("needle_triggers_home_test"), needle_file("needle_triggers_desk_test"))
    if tp is not None:
        trig_rows = score_run(test, tp, lambda app: f"S1-{app}")
        dg["V-TRIGGERS (test)"] = {"needle": {"summary": summary(trig_rows),
                                              "vs_needle_S1": boot([trig_rows, N1], lambda m: m[0] - m[1])}}
    for arm in ("llm-a", "llm-named"):
        add("V-CONTRACT-IN-PROMPT", arm, dict(diag), join(llm_file(arm, "contract_S1_home"), llm_file(arm, "contract_S1_desk")),
            lambda app: f"S1-{app}", main_gold, diagS1[arm], lambda app: f"S1-{app}")
    add("V-FORCED", "needle", dict(diag), join(needle_file("needle_forced_home_diag"), needle_file("needle_forced_desk_diag")),
        lambda app: f"S1-{app}", main_gold, diagS1["needle"], lambda app: f"S1-{app}")
    for arm in ("needle", "llm-a", "llm-named"):
        add("S1 on anchors (reference)", arm, dict(diag), diagS1[arm], lambda app: f"S1-{app}", main_gold)
    out["diagnostics"] = dg

    # ---- repeats (stability, never calibration)
    rp = {}
    for app in APPS:
        ids = [json.loads(l)["id"] for l in open(INP / f"repeat-{app}.jsonl")]
        n0 = P[("needle", "S1")] or {}
        r1, r2 = needle_file(f"needle_S1_{app}_repeat_r1"), needle_file(f"needle_S1_{app}_repeat_r2")
        if r1 and r2:
            same = [i for i in ids if json.dumps(n0[i]["raw"] and n0[i]["raw"].get("function_calls"), sort_keys=True)
                    == json.dumps(r1[i]["raw"] and r1[i]["raw"].get("function_calls"), sort_keys=True)
                    == json.dumps(r2[i]["raw"] and r2[i]["raw"].get("function_calls"), sort_keys=True)]
            dc = [max(abs((x[i]["conf"] or 0) - (n0[i]["conf"] or 0)) for x in (r1, r2)) for i in ids]
            rp[f"needle/{app}"] = {"n": len(ids), "identical_calls_all_three": len(same), "max_conf_move": max(dc),
                                   "items_conf_moved": sum(d > 0 for d in dc)}
        for arm in ("llm-a", "llm-named"):
            a0 = P[(arm, "S1")] or {}
            q1, q2 = llm_file(arm, f"repeat_r1_S1_{app}"), llm_file(arm, f"repeat_r2_S1_{app}")
            if q1 and q2:
                both = [i for i in ids if all(not x.get(i, {}).get("unserved") and i in x for x in (a0, q1, q2))]
                same = [i for i in both if json.dumps(a0[i]["pred"], sort_keys=True) == json.dumps(q1[i]["pred"], sort_keys=True)
                        == json.dumps(q2[i]["pred"], sort_keys=True)]
                rp[f"{arm}/{app}"] = {"n": len(both), "identical_output_all_three": len(same)}
    out["repeats"] = rp

    # ---- latency (separate from the scored passes)
    lat = {}
    pct = lambda v: {"n": len(v), "p50": float(np.percentile(v, 50)), "p95": float(np.percentile(v, 95)), "max": float(max(v))} if v else None
    for app in APPS:
        for n in (1, 4):
            f = O / "latency" / f"needle_{app}_{n}.json"
            if not f.exists():
                continue
            d = json.loads(f.read_text())
            nr = d["needle"]
            lat[f"needle/{app}/{n}core"] = {"cpu": d["cpu_model"], "calls": pct([r["t_s"] for r in nr if r["returned"]]),
                                           "refusals": pct([r["t_s"] for r in nr if not r["returned"] and not r["tech_fail"]]),
                                           "tech_fail": sum(r["tech_fail"] for r in nr),
                                           "prefill_tps_p50": float(np.median([r["prefill_tps"] for r in nr if r["prefill_tps"]])),
                                           "decode_tps_p50": float(np.median([r["decode_tps"] for r in nr if r["decode_tps"]])),
                                           "peak_ram_mb_max": float(max(r["peak_ram_mb"] for r in nr if r["peak_ram_mb"]))}
            for b, rows in d["baselines"].items():
                lat[f"{b}/{app}/{n}core"] = {"calls": pct([r["t_s"] for r in rows if r["returned"]]),
                                            "refusals": pct([r["t_s"] for r in rows if not r["returned"]])}
            if d.get("hassil_load_s") is not None:
                lat[f"hassil/{app}/{n}core"]["load_s"] = d["hassil_load_s"]
        f = O / "latency" / f"cold_{app}.json"
        if f.exists():
            d = json.loads(f.read_text())
            lat[f"needle/{app}/cold"] = {"containers": len(d["containers"]), "unlanded": d["unlanded"],
                                         **(pct([c["first_request"]["t_s"] for c in d["containers"]]) or {})}
    for arm in ("llm-a", "llm-named"):
        f = O / "latency" / f"{arm}.json"
        if f.exists():
            d = json.loads(f.read_text())
            rows = [r for r in d["rows"] if r.get("http") == 200 and r.get("served_by") == HOSTS[arm] and "total_to_decision_s" in r]
            lat[f"{arm}/serial200"] = {"region": d.get("region"), "modal_region": d.get("modal_region"), "served": len(rows),
                                       "of": len(d["rows"]), "calls": pct([r["total_to_decision_s"] for r in rows if r["returned"]]),
                                       "refusals": pct([r["total_to_decision_s"] for r in rows if not r["returned"] and not r["tech_fail"]]),
                                       "ttft": pct([r["ttft_s"] for r in rows if r["ttft_s"] is not None]),
                                       "floor_before": pct([r["total_s"] for r in d["floor_before"] if r["http"] == 200]),
                                       "floor_after": pct([r["total_s"] for r in d["floor_after"] if r["http"] == 200])}
    out["latency"] = lat

    # ---- FREEZE §11 display draws
    ex = defaultdict(list)
    for (arm, ver), rows in RW.items():
        for i in sorted(rows, key=lambda i: hashlib.sha256(("needle3-display-2026-09-22:" + i).encode()).hexdigest()):
            r = rows[i]
            cell = f"{arm}|{ver}|{r['app']}|{r['outcome']}"
            if len(ex[cell]) < 3:
                ex[cell].append(i)
    cellsizes = Counter(f"{arm}|{ver}|{r['app']}|{r['outcome']}" for (arm, ver), rows in RW.items() for r in rows.values())
    (R / "EXAMPLES.json").write_text(json.dumps({c: {"n": cellsizes[c], "ids": v} for c, v in sorted(ex.items())}, indent=1))

    (R / "SCORES.json").write_text(json.dumps(out, indent=1, default=float))
    # ---- digest
    print("arm|schema  stat_of_record  act  no-act  n  unserved  tf")
    for k, s in arms_out.items():
        print(f"{k:28s} {s['stat_of_record']:.3f} [{s['boot_own']['ci95'][0]:.3f},{s['boot_own']['ci95'][1]:.3f}]  "
              f"{s['act_mean']:.3f}  {s['noact_mean']:.3f}  {s['n']}  {s['unserved']}  {sum(s['tf_kinds'].values())}")
    for p in prim:
        print(f"{p['comparison']:45s} {p['point']:+.3f} [{p['ci95'][0]:+.3f},{p['ci95'][1]:+.3f}] sign p={p['sign_test']['p']:.4f} holm={p['sign_test']['p_holm']:.4f}")


if __name__ == "__main__":
    main()
