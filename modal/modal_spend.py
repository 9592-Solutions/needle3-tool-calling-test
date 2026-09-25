# /// script
# requires-python = ">=3.11"
# dependencies = ["modal==1.5.5"]
# ///
"""Sum today's (or --start) Modal cost for app m37-needle3, by resource. usage: uv run modal_spend.py [--start YYYY-MM-DD]"""
import argparse, datetime as dt
import modal
ap = argparse.ArgumentParser(); ap.add_argument("--start", default=dt.date.today().isoformat()); a = ap.parse_args()
start = dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc)
end = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)
end = end.replace(hour=0, minute=0, second=0, microsecond=0)
rows = modal.billing.workspace_billing_report(start=start, end=end, resolution="d", tag_names=["episode"])
tot = {}
for r in rows:
    r = dict(r)
    if r.get("description") == "m37-needle3" or (r.get("tags") or {}).get("episode") == "needle3":
        tot["apps"] = tot.get("apps", 0) + 1
        tot["_total"] = tot.get("_total", 0) + float(r["cost"])
print({k: round(v, 5) for k, v in tot.items()})
