"""Needle 3 sealed run (DESIGN §10 step 9; FREEZE.md §3, §8, §12): build every runner input from the three REQUEST
files only (id, app, text). Nothing from a key file is read. Prints counts and file names, never request text.

Writes under runs/sealed/:
  inputs/{test,diag,bandF}-{home,desk}.jsonl   request lines split by app (the LLM arms' --items)
  inputs/repeat-{app}.jsonl                    FREEZE §8: 30 per app, smallest sha256("needle3-repeat-2026-09-22:"+id) on test
  inputs/latency-{app}.jsonl                   FREEZE §8: 100 per app, smallest sha256("needle3-latency-2026-09-22:"+id) on test
  inputs/relroom-home.jsonl                    test-home + diag-home (V-REL and V-ROOMREQ gold lives in home keys; which
                                               items carry it is in the keys, so every home item runs and the scorer
                                               scores the ones whose key carries that variant)
  specs/<name>.json                            Needle specs for modal/needle_modal.py (unchanged, sha256 992199b5…)
usage: python3 runs/sealed/make_specs.py
"""
import hashlib, json, os, re
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
REQ = ROOT / "sealed-v2"
FACT = "date: 2026-06-10 Wed 14:30; locale: en-US"
CPU = "GenuineIntel fam 6 model 85"
# V-VENDOR: the vendor harness's own system text (needle.environments.smart_home.SYSTEM, as captured in
# preflight/kac_in_pinned_smart_home.json) behind the package's date prefix, with our fixed date.
VENDOR_SYSTEM = ("date: 2026-06-10 Wed 14:30; Map each explicit supported home action to exactly one declared call; "
                 "never duplicate an action. Do not guess missing targets or values. Unsupported, invalid, ambiguous, "
                 "and negated requests return no call.")


def read_requests(name):
    rows = [json.loads(l) for l in open(REQ / f"{name}-requests.jsonl")]
    for r in rows:
        extra = set(r) - {"id", "app", "text"}
        assert not extra, f"{name}: unexpected fields {extra}"   # FREEZE §1: request files carry id, app, text only
        assert r["app"] in ("home", "desk")
    assert len({r["id"] for r in rows}) == len(rows)
    return rows


def tools(schema_id):
    if schema_id[:2] in ("S0", "S1"):
        ver, app = schema_id.split("-", 1)
        return json.loads((ROOT / "contracts" / ver / f"{app}.json").read_text())
    return json.loads((ROOT / "contracts" / "variants" / f"{schema_id}.json").read_text())


def trigger_regex(phrase):
    """K0's blind trigger phrases -> Needle `triggers` (regex, case-insensitive per the vendor's guide): the phrase as a
    literal, bounded by word boundaries."""
    esc = re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", phrase)
    return r"\b" + esc + r"\b"


def triggered_tools(app):
    t = json.loads(json.dumps(tools(f"S1-{app}")))
    trig = json.loads((ROOT / "baselines" / "k0" / "triggers_S1.json").read_text())
    for x in t:
        f = x["function"]
        f["triggers"] = [trigger_regex(p) for p in trig.get(f["name"], [])]
    return t


def cfg(schema_id, app, **kw):
    c = {"tools": tools(schema_id) if not kw.get("tools") else kw.pop("tools"),
         "system": FACT if app == "desk" else None, "depth": None, "threads": 1, "forced": False,
         "overflow_flag": True, "require_cpu": CPU}
    c.update(kw)
    return c


def sha_order(rows, salt):
    return sorted(rows, key=lambda r: hashlib.sha256((salt + r["id"]).encode()).hexdigest())


def main():
    sets = {"test": read_requests("test"), "diag": read_requests("diagnostics"), "bandF": read_requests("bandF")}
    (H / "inputs").mkdir(exist_ok=True); (H / "specs").mkdir(exist_ok=True)
    by = {}
    for s, rows in sets.items():
        for app in ("home", "desk"):
            sub = [r for r in rows if r["app"] == app]
            by[(s, app)] = sub
            with open(H / "inputs" / f"{s}-{app}.jsonl", "w") as f:
                for r in sub:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for app in ("home", "desk"):
        for name, salt, n in (("repeat", "needle3-repeat-2026-09-22:", 30), ("latency", "needle3-latency-2026-09-22:", 100)):
            sel = sha_order(by[("test", app)], salt)[:n]
            by[(name, app)] = sel
            with open(H / "inputs" / f"{name}-{app}.jsonl", "w") as f:
                for r in sel:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rr = by[("test", "home")] + by[("diag", "home")]
    by[("relroom", "home")] = rr
    with open(H / "inputs" / "relroom-home.jsonl", "w") as f:
        for r in rr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    specs = {}
    items = lambda s, app: [{"id": r["id"], "prompt": r["text"]} for r in by[(s, app)]]
    for app in ("home", "desk"):
        for ver in ("S1", "S0"):
            specs[f"needle_{ver}_{app}_test"] = (items("test", app), cfg(f"{ver}-{app}", app))
        specs[f"needle_S1_{app}_bandF"] = (items("bandF", app), cfg(f"S1-{app}", app))
        specs[f"needle_S1_{app}_diag"] = (items("diag", app), cfg(f"S1-{app}", app))   # reference for every diagnostic
        for r in (1, 2):
            specs[f"needle_S1_{app}_repeat_r{r}"] = (items("repeat", app), cfg(f"S1-{app}", app))
        for n in (6, 10, 20):
            specs[f"needle_count{n}_{app}_diag"] = (items("diag", app), cfg(f"{app}-count{n}", app))
        specs[f"needle_renamed_{app}_diag"] = (items("diag", app), cfg(f"{app}-renamed", app))
        specs[f"needle_dispatch_{app}_diag"] = (items("diag", app), cfg(f"{app}-dispatch", app))
        for s in ("test", "diag"):
            specs[f"needle_triggers_{app}_{s}"] = (items(s, app), cfg(f"S1-{app}", app, tools=triggered_tools(app)))
        specs[f"needle_forced_{app}_diag"] = (items("diag", app), cfg(f"S1-{app}", app, forced=True))
    specs["needle_rel_home_relroom"] = (items("relroom", "home"), cfg("home-rel", "home"))
    specs["needle_roomreq_home_relroom"] = (items("relroom", "home"), cfg("home-roomreq", "home"))
    specs["needle_timerS_desk_diag"] = (items("diag", "desk"), cfg("desk-timer-seconds", "desk"))
    specs["needle_timerU_desk_diag"] = (items("diag", "desk"), cfg("desk-timer-units", "desk"))
    specs["needle_vendor_home_diag"] = (items("diag", "home"), cfg("vendor-smart_home", "home", system=VENDOR_SYSTEM))
    for name, (it, c) in specs.items():
        (H / "specs" / f"{name}.json").write_text(json.dumps({"items": it, "cfg": c}, ensure_ascii=False))
    counts = {f"{k[0]}-{k[1]}": len(v) for k, v in by.items()}
    print(json.dumps({"counts": counts, "n_specs": len(specs)}, indent=1))


if __name__ == "__main__":
    main()
