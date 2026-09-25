"""Re-parse stored LLM responses with the current harness/llm_arm.parse (no new calls). The original
parse result is kept under pred_v1/parse_v1. usage: python3 frontier/reparse.py <run_dir>"""
import glob, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
import llm_arm
changed = 0
for f in glob.glob(str(Path(sys.argv[1]) / "*.jsonl")):
    if Path(f).name.startswith("_"): continue
    out = []
    for l in open(f):
        r = json.loads(l)
        if r.get("http") == 200 and r.get("response"):
            pred, st = llm_arm.parse(r["cfg"], r["response"])
            if (pred, st) != (r.get("pred"), r.get("parse")):
                r.setdefault("pred_v1", r.get("pred")); r.setdefault("parse_v1", r.get("parse"))
                r["pred"], r["parse"] = pred, st; changed += 1
        out.append(json.dumps(r, ensure_ascii=False))
    open(f, "w").write("\n".join(out) + "\n")
print("records changed:", changed)
