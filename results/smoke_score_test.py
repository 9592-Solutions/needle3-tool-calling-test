"""Smoke test for results/score_test.py on CONFIG-SIDE data only (never test material): builds a fake sealed world in
a scratch directory from the selection partition (partitions/gold.jsonl), the stored config-side Needle outputs
(runs/needle_config/out_*.json) and the frontier-stage LLM outputs of the two frozen arms, then runs the scorer end to
end with the NEEDLE3_* overrides. It checks that the code runs and that its numbers agree with a direct count;
the numbers themselves mean nothing (fake families, variant gold copied from main gold).
usage: uv run --no-project --with numpy --with jsonschema==4.26.0 --with bm25s==0.3.9 --with PyStemmer==3.1.0 \
         --with hassil==3.12.1 --with PyYAML==6.0.3 python results/smoke_score_test.py <scratch-dir>
"""
import json, os, subprocess, sys
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parent
ROOT = R.parent
W = Path(sys.argv[1]); K = W / "keys"; I = W / "inputs"; O = W / "out"; RES = W / "results"
for d in (K, I, O / "needle", O / "llm" / "llm-a", O / "llm" / "llm-named", RES):
    d.mkdir(parents=True, exist_ok=True)

gold = [json.loads(l) for l in open(ROOT / "partitions" / "gold.jsonl")]
sel = [g for g in gold if g["partition"] == "selection"]
cells = defaultdict(list)
for g in sel:
    cells[(g["app"], g["stratum"])].append(g)
test, fam = [], 0
for c, gs in sorted(cells.items()):
    for j in range(0, len(gs) - 1, 2):
        fam += 1
        for p, g in zip(("P1", "P2"), gs[j:j + 2]):
            test.append({**g, "family": f"f{fam}", "phrasing": p})
diag = [g for g in sel[:60]]
band = [g for g in sel[60:80]]


def wk(name, rows, extra):
    with open(K / f"{name}-key.jsonl", "w") as f:
        for g in rows:
            r = {"id": g["id"], "app": g["app"], "gold": g["gold"], "stratum": g["stratum"], **extra(g)}
            f.write(json.dumps(r) + "\n")


wk("test", test, lambda g: {"family": g["family"], "phrasing": g["phrasing"],
                            **({"V-REL": g["gold"], "V-ROOMREQ": g["gold"]} if g["app"] == "home" else {})})
wk("diagnostics", diag, lambda g: {"V-COUNT-6": g["gold"], "V-COUNT-10": g["gold"], "V-COUNT-20": g["gold"],
                                   **({"V-TIMER": g["gold"]} if g["app"] == "desk" else {})})
wk("bandF", band, lambda g: {})
for s, rows in (("test", test), ("diag", diag), ("bandF", band)):
    for app in ("home", "desk"):
        with open(I / f"{s}-{app}.jsonl", "w") as f:
            for g in rows:
                if g["app"] == app:
                    f.write(json.dumps({"id": g["id"], "app": app, "text": g["text"]}) + "\n")
for app in ("home", "desk"):
    with open(I / f"repeat-{app}.jsonl", "w") as f:
        for g in [g for g in test if g["app"] == app][:10]:
            f.write(json.dumps({"id": g["id"], "app": app, "text": g["text"]}) + "\n")


def needle_out(ver, app, ids, name):
    d = json.load(open(ROOT / "runs" / "needle_config" / f"out_{ver}_{app}.json"))
    d["results"] = [r for r in d["results"] if r["id"] in ids]
    (O / "needle" / f"{name}.json").write_text(json.dumps(d))


ids = lambda rows, app: {g["id"] for g in rows if g["app"] == app}
for app in ("home", "desk"):
    for ver in ("S1", "S0"):
        needle_out(ver, app, ids(test, app), f"needle_{ver}_{app}_test")
    needle_out("S1", app, ids(band, app), f"needle_S1_{app}_bandF")
    for name in ("S1_{a}_diag", "count6_{a}_diag", "count10_{a}_diag", "count20_{a}_diag", "renamed_{a}_diag",
                 "dispatch_{a}_diag", "triggers_{a}_diag", "forced_{a}_diag", "S1_{a}_repeat_r1", "S1_{a}_repeat_r2"):
        needle_out("S1", app, ids(diag if "diag" in name else test, app), "needle_" + name.format(a=app))
    needle_out("S1", app, ids(test, app), f"needle_triggers_{app}_test")
needle_out("S1", "desk", ids(diag, "desk"), "needle_timerS_desk_diag")

ST = ROOT / "frontier" / "stage"
src = {"llm-a": "deepseek__deepseek-v4-flash-0731__schema__{a}.jsonl", "llm-named": "deepseek__deepseek-v4-flash__native__{a}.jsonl"}
for arm, pat in src.items():
    for app in ("home", "desk"):
        recs = [json.loads(l) for l in open(ST / pat.format(a=app))]
        def w(name, keep):
            with open(O / "llm" / arm / f"{name}.jsonl", "w") as f:
                for r in recs:
                    if r["id"] in keep:
                        f.write(json.dumps(r) + "\n")
        for ver in ("S1", "S0"):
            w(f"test_{ver}_{app}", ids(test, app))
        w(f"bandF_S1_{app}", ids(band, app)); w(f"diag_S1_{app}", ids(diag, app))
        w(f"renamed_{app}", ids(diag, app)); w(f"contract_S1_{app}", ids(diag, app))
        w(f"repeat_r1_S1_{app}", ids(test, app)); w(f"repeat_r2_S1_{app}", ids(test, app))
env = {**os.environ, "NEEDLE3_INPUTS": str(I), "NEEDLE3_SEALED_OUT": str(O), "NEEDLE3_KEYS": str(K),
       "NEEDLE3_RESULTS_DIR": str(RES), "NEEDLE3_INTENTS_DIR": "/private/tmp/needle3-intents"}
subprocess.run([sys.executable, str(ROOT / "runs" / "sealed" / "baselines_sealed.py")], env=env, check=True)
subprocess.run([sys.executable, str(R / "score_test.py")], env=env, check=True)
sc = json.load(open(RES / "SCORES.json"))
# independent recount of one number: needle S1 plain accuracy on the fake test
sys.path.insert(0, str(ROOT / "harness")); import score  # noqa: E402
d = {**{r["id"]: r for r in json.load(open(O / "needle" / "needle_S1_home_test.json"))["results"]},
     **{r["id"]: r for r in json.load(open(O / "needle" / "needle_S1_desk_test.json"))["results"]}}
okc = n = 0
for g in test:
    if g["gold"] == "ambiguous":
        continue
    s = score.score_item(g["gold"], score.needle_calls(d[g["id"]]["parsed"]) if d[g["id"]]["rc"] == 0 else None, f"S1-{g['app']}")
    okc += s["outcome"] in ("correct_action", "correct_nonaction"); n += 1
print("recount needle S1 plain accuracy", okc / n, "scorer", sc["arms"]["needle|S1"]["plain_accuracy"])
assert abs(okc / n - sc["arms"]["needle|S1"]["plain_accuracy"]) < 1e-9
print("SMOKE OK")
