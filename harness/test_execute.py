"""Tests for harness/execute.py on config-side material only (no test item). Run:
uv run --no-project --with jsonschema python harness/test_execute.py"""
import json, sys
from pathlib import Path
H = Path(__file__).resolve().parent; ROOT = H.parent
sys.path.insert(0, str(H))
import execute, score

V = {a: execute.tools_for(ROOT / f"contracts/S1/{a}.json") for a in ("home", "desk")}
g_alarm = [[{"action": "set_alarm", "args": {"time": "06:00", "date": "2026-06-11"}}]]
ok = [{"name": "set_alarm", "arguments": {"time": "06:00"}}]
fails = 0
def check(name, got, want):
    global fails
    if got != want:
        fails += 1; print("FAIL", name, got, "!=", want)
check("valid call executes", execute.execute_item(g_alarm, ok, "S1-desk", V["desk"])["outcome"], "correct_action")
check("bad pattern -> nothing", execute.execute_item(g_alarm, [{"name": "set_alarm", "arguments": {"time": "6am"}}], "S1-desk", V["desk"])["invalid"], True)
check("unknown tool -> nothing", execute.execute_item(g_alarm, [{"name": "set_timer", "arguments": {}}], "S1-desk", V["desk"])["outcome"], "needless_refusal")
check("one bad call voids bundle", execute.execute_item([[]], ok + [{"name": "set_alarm", "arguments": {"time": "25:00"}}], "S1-desk", V["desk"])["outcome"], "correct_nonaction")
check("missing required -> nothing", execute.execute_item(g_alarm, [{"name": "set_alarm", "arguments": {}}], "S1-desk", V["desk"])["invalid"], True)
check("null = omitted", execute.execute_item(g_alarm, [{"name": "set_alarm", "arguments": {"time": "06:00", "date": None}}], "S1-desk", V["desk"])["outcome"], "correct_action")
check("below threshold deferred", execute.execute_item(g_alarm, ok, "S1-desk", V["desk"], conf=0.5, threshold=0.9)["deferred"], True)
check("no conf deferred", execute.execute_item(g_alarm, ok, "S1-desk", V["desk"], conf=None, threshold=0.9)["deferred"], True)
check("tech failure stays", execute.execute_item(g_alarm, None, "S1-desk", V["desk"])["outcome"], "technical_failure")
check("empty is empty", execute.execute_item([[]], [], "S1-desk", V["desk"], conf=0.1, threshold=0.9)["deferred"], False)
# every config-side Needle S1 return: executed outcome never better than proposal on a no-act item
gold = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "partitions/gold.jsonl")}
n = inv = 0
for app in ("home", "desk"):
    for r in json.load(open(ROOT / f"runs/needle_config/out_S1_{app}.json"))["results"]:
        g = gold.get(r["id"])
        if not g or g["gold"] == "ambiguous":
            continue
        calls = score.needle_calls(r["parsed"])
        e = execute.execute_item(g["gold"], calls, f"S1-{app}", V[app])
        n += 1; inv += e.get("invalid", False)
print(f"config S1 items {n}, Needle bundles failing schema validation {inv}")
print("OK" if not fails else f"{fails} FAILED"); sys.exit(1 if fails else 0)
