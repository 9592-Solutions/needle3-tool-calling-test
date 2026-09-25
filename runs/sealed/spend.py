# /// script
# requires-python = ">=3.11"
# dependencies = ["modal==1.5.5", "httpx"]
# ///
"""Needle 3 budget gate (FREEZE §10). Observed cumulative episode spend = OpenRouter key `m37-needle3` usage (its
own counter, all-time) + Modal app m37-needle3 cost billed since 2026-09-22 (billing report; can lag, which the
$0.25 below the cap covers). `--gate W` exits 1 when observed + W > $4.75 (the stage must not fire).
usage: uv run runs/sealed/spend.py [--gate 0.35] [--label "tier 2 latency"]"""
import argparse, datetime as dt, json, os, sys
import httpx, modal
ap = argparse.ArgumentParser(); ap.add_argument("--gate", type=float); ap.add_argument("--label", default="")
a = ap.parse_args()
key = os.environ["OPENROUTER_API_KEY"]
k = httpx.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=30).json()["data"]
start = dt.datetime(2026, 9, 22, tzinfo=dt.timezone.utc)
end = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
rows = modal.billing.workspace_billing_report(start=start, end=end, resolution="d", tag_names=["episode"])
m = sum(float(dict(r)["cost"]) for r in rows if dict(r).get("description") == "m37-needle3"
        or (dict(r).get("tags") or {}).get("episode") == "needle3")
tot = float(k["usage"]) + m
rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "label": a.label, "openrouter": round(float(k["usage"]), 5),
       "openrouter_limit": k.get("limit"), "modal": round(m, 5), "observed_total": round(tot, 5)}
if a.gate is not None:
    rec.update(stage_worst=a.gate, projected=round(tot + a.gate, 5), fires=tot + a.gate <= 4.75)
print(json.dumps(rec))
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "spend-ledger.jsonl"), "a") as f:
    f.write(json.dumps(rec) + "\n")
sys.exit(0 if rec.get("fires", True) else 1)
