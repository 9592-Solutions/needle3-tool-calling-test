"""Known-answer control (DESIGN §10 step 4): the vendor's six suites through OUR runner wrapper (native
binary, one process per case) and OUR scoring path, against the vendor harness (Python package) on the
same pinned artifacts. Our scoring here = the vendor's own gold and fold rule, applied to what our runner
returned; the question is whether our apparatus reproduces the vendor apparatus, case by case."""
import json, sys
def fold(v):
    if isinstance(v, str): return v.casefold()
    if isinstance(v, float) and v.is_integer(): return int(v)
    if isinstance(v, dict): return {k: fold(x) for k, x in v.items()}
    if isinstance(v, list): return [fold(x) for x in v]
    return v
key = lambda c: json.dumps(fold(c), sort_keys=True)
V = json.load(open("vendor_harness_raw.json"))
tot = {"py": 0, "nat": 0, "n": 0, "agree_outcome": 0, "same_calls": 0, "same_conf": 0, "nat_fail": 0}
rows = []
for e in V:
    N = {r["id"]: r for r in json.load(open(f"kac_native_{e['env']}.json"))["results"]}
    for i, c in enumerate(e["cases"]):
        r = N[f"{e['env']}-{i:02d}"]; p = r["parsed"]
        if r["rc"] != 0 or p is None:
            tot["nat_fail"] += 1; nat_ok = False; got = None
        else:
            got = p.get("function_calls") or []
            v = p.get("validation") or {}
            if got and (v.get("ungrounded") or v.get("negation")): got = []
            nat_ok = sorted(map(key, got)) == sorted(map(key, c["want"]))
        py = c["response"]
        same_calls = p is not None and key(p.get("function_calls") or []) == key(py.get("function_calls") or [])
        same_conf = p is not None and p.get("confidence") == py.get("confidence")
        tot["n"] += 1; tot["py"] += c["harness_ok"]; tot["nat"] += nat_ok
        tot["agree_outcome"] += (nat_ok == c["harness_ok"]); tot["same_calls"] += same_calls; tot["same_conf"] += same_conf
        rows.append({"env": e["env"], "i": i, "category": c["category"], "query": c["query"], "py_ok": c["harness_ok"], "nat_ok": nat_ok,
                     "py_calls": py.get("function_calls"), "nat_calls": p and p.get("function_calls"),
                     "py_conf": py.get("confidence"), "nat_conf": p and p.get("confidence"),
                     "py_val": py.get("validation"), "nat_val": p and p.get("validation"),
                     "py_supp": py.get("suppressed_calls"), "nat_supp": p and p.get("suppressed_calls"), "wall_s": r["wall_s"]})
per = {}
for x in rows:
    s = per.setdefault(x["env"], [0, 0, 0]); s[0] += x["py_ok"]; s[1] += x["nat_ok"]; s[2] += 1
print(json.dumps(tot)); print(json.dumps(per))
dis = [x for x in rows if x["py_ok"] != x["nat_ok"] or json.dumps(fold(x["py_calls"] or [])) != json.dumps(fold(x["nat_calls"] or []))]
print(len(dis), "cases where calls or outcome differ")
for x in dis: print(json.dumps(x)[:600])
import statistics
cd = [abs((x["py_conf"] or 0) - (x["nat_conf"] or 0)) for x in rows if x["py_conf"] is not None and x["nat_conf"] is not None]
print("confidence |diff|: max", max(cd), "median", statistics.median(cd))
print("wall s: median", statistics.median(x["wall_s"] for x in rows), "max", max(x["wall_s"] for x in rows))
json.dump({"totals": tot, "per_env": per, "rows": rows}, open("kac_compare.json", "w"), indent=1)
