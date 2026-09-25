# /// script
# requires-python = ">=3.11"
# dependencies = ["bm25s==0.3.9", "PyStemmer==3.1.0", "numpy", "hassil==3.12.1", "PyYAML==6.0.3"]
# ///
"""Needle 3 sealed run: the local, model-free arms (FREEZE §3) on the sealed request files. Raw predictions only;
nothing is scored here. K0, K1, K1-firstbank, K1-firstbank-none on test (S0, S1) and band F (S1); hassil on
home test and home band F (schema-independent, reported once, written in S1-home names exactly as
baselines/hassil/score_dev.py renames them); always-decline is [] and needs no run.
Frozen parameters are read from baselines/DEV-RESULTS.json (FREEZE §3 lists the same numbers).
usage: NEEDLE3_INTENTS_DIR=/private/tmp/needle3-intents uv run runs/sealed/baselines_sealed.py
"""
import json, os, sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT / "baselines")); import bm25_arm as B  # noqa: E402
sys.path.insert(0, str(ROOT / "baselines" / "hassil")); import hassil_arm  # noqa: E402
sys.path.insert(0, str(ROOT / "contracts")); import mapping  # noqa: E402

DEV = json.loads((ROOT / "baselines" / "DEV-RESULTS.json").read_text())["arms"]
BANK = [g for g in map(json.loads, open(ROOT / "partitions" / "gold.jsonl")) if g["partition"] == "lexical"]
INP = Path(os.environ.get("NEEDLE3_INPUTS", H / "inputs"))                  # overridable only for the smoke test
OUT = Path(os.environ.get("NEEDLE3_SEALED_OUT", H / "out")) / "baselines"


def rows(s, app):
    return [json.loads(l) for l in open(INP / f"{s}-{app}.jsonl")]


def router(arm, sid, app):
    ob = [b for b in BANK if b["app"] == app]
    docs = (B.k0_docs(sid) if arm == "K0" else B.k1_bank_docs(sid, ob) if arm == "K1"
            else B.k1_docs(sid, ob, include_none=(arm == "K1-firstbank-none")))
    return B.Router(sid, docs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for arm in ("K0", "K1", "K1-firstbank", "K1-firstbank-none"):
        for ver in ("S1", "S0"):
            t = DEV[f"{arm}-{ver}"]["tuned"]
            for app in ("home", "desk"):
                sid = f"{ver}-{app}"
                r = router(arm, sid, app)
                for s in (("test", "bandF") if ver == "S1" else ("test",)):
                    with open(OUT / f"{arm}_{ver}_{app}_{s}.jsonl", "w") as f:
                        for it in rows(s, app):
                            try:
                                calls, trace = r.predict(it["text"], t["k"], t["tau"][app], t["mu"])
                            except Exception as e:      # a crash is a technical failure (pred None), never dropped
                                calls, trace = None, [{"error": f"{type(e).__name__}: {e}"[:300]}]
                            f.write(json.dumps({"id": it["id"], "arm": arm, "schema": sid, "pred": calls, "trace": trace,
                                                "params": {"k": t["k"], "tau": t["tau"][app], "mu": t["mu"]}},
                                               ensure_ascii=False) + "\n")
                            n += 1
    inv = {}
    for raw, (action, amap) in mapping.TABLES["S1-home"].items():
        inv[action] = (raw, {c: r for r, c in amap.items()})
    for s in ("test", "bandF"):
        with open(OUT / f"hassil_S1_home_{s}.jsonl", "w") as f:
            for it in rows(s, "home"):
                try:
                    pc = hassil_arm.predict(it["text"])
                except Exception as e:
                    f.write(json.dumps({"id": it["id"], "arm": "hassil", "schema": "S1-home", "pred": None,
                                        "error": f"{type(e).__name__}: {e}"[:300]}) + "\n"); n += 1; continue
                raw = [{"name": inv[c["action"]][0], "arguments": {inv[c["action"]][1].get(k, k): v for k, v in c["args"].items()}}
                       for c in pc]
                f.write(json.dumps({"id": it["id"], "arm": "hassil", "schema": "S1-home", "pred": raw, "pred_canonical": pc},
                                   ensure_ascii=False) + "\n")
                n += 1
    print(json.dumps({"written": n, "dir": str(OUT)}))


if __name__ == "__main__":
    main()
