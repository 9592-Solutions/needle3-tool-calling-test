"""Scorer mutation tests (DESIGN §3.5, §10 step 4). The scorer is not frozen until all pass.
Controls first (a known-correct prediction must score correct, or every failure below is meaningless), then
the five mutation families DESIGN names (swap two arguments, change a unit, add an extra call, drop a field,
flip polarity), each of which must score WRONG, on every act item of the canonical examples AND on every
positive/parallel case of the six vendor suites. usage: python3 harness/test_score.py"""
import copy, json, sys
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import score  # noqa: E402

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)

# ---- canonical examples, one per action (gold canonical; pred in S1 raw form) ----
EX = [
    ("S1-home", [{"action": "light_power", "args": {"room": "kitchen", "state": "off"}}],
     [{"name": "set_lights_power", "arguments": {"room": "kitchen", "power": "off"}}]),
    ("S1-home", [{"action": "set_light_level", "args": {"room": "here", "level": 30}}],
     [{"name": "set_lights_brightness", "arguments": {"brightness": 30}}]),
    ("S0-home", [{"action": "set_light_color", "args": {"room": "living room", "color": "warm white"}}],
     [{"name": "set_lights_color", "arguments": {"room": "living_room", "color": "warm_white"}}]),
    ("S1-home", [{"action": "vacuum", "args": {"command": "start", "room": "bedroom"}}],
     [{"name": "control_vacuum", "arguments": {"action": "start", "room": "bedroom"}}]),
    ("S1-home", [{"action": "smart_plug", "args": {"state": "on"}}],
     [{"name": "set_plug_power", "arguments": {"power": "on"}}]),
    ("S1-desk", [{"action": "set_alarm", "args": {"time": "07:00", "date": "2026-06-11"}}],
     [{"name": "set_alarm", "arguments": {"time": "07:00"}}]),
    ("S1-desk", [{"action": "add_to_list", "args": {"item": "milk", "list": "shopping"}},
                 {"action": "add_to_list", "args": {"item": "eggs", "list": "shopping"}}],
     [{"name": "add_list_item", "arguments": {"list": "shopping", "item": "milk"}},
      {"name": "add_list_item", "arguments": {"list": "shopping", "item": "eggs"}}]),
    ("S1-desk", [{"action": "create_reminder", "args": {"text": "take the bins out", "time": "09:00", "date": "2026-06-11"}}],
     [{"name": "create_reminder", "arguments": {"text": "take the bins out", "date": "2026-06-11"}}]),
    ("desk-timer-units", [{"action": "start_timer", "args": {"duration_seconds": 1500}}],
     [{"name": "start_timer", "arguments": {"amount": 25, "unit": "minutes"}}]),
    ("home-dispatch", [{"action": "smart_plug", "args": {"state": "off"}}],
     [{"name": "home_control", "arguments": {"action": "plug", "power": "off"}}]),
]
POLAR = {"on": "off", "off": "on", "start": "stop", "stop": "start", "up": "down", "down": "up"}


def mutations(pred):
    out = []
    for i, c in enumerate(pred):
        a = c["arguments"]; ks = list(a)
        if len(ks) >= 2 and a[ks[0]] != a[ks[1]]:
            m = copy.deepcopy(pred); m[i]["arguments"][ks[0]], m[i]["arguments"][ks[1]] = a[ks[1]], a[ks[0]]; out.append(("swap", m))
        for k, v in a.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                m = copy.deepcopy(pred); m[i]["arguments"][k] = v * 60; out.append(("unit", m))
            if isinstance(v, str) and ":" in v and len(v) == 5:
                m = copy.deepcopy(pred); m[i]["arguments"][k] = f"{(int(v[:2]) + 12) % 24:02d}{v[2:]}"; out.append(("unit(am/pm)", m))
            if k == "unit":
                m = copy.deepcopy(pred); m[i]["arguments"][k] = "seconds" if v != "seconds" else "minutes"; out.append(("unit", m))
            if isinstance(v, str) and v.lower() in POLAR:
                m = copy.deepcopy(pred); m[i]["arguments"][k] = POLAR[v.lower()]; out.append(("polarity", m))
        for k in ks:
            m = copy.deepcopy(pred); del m[i]["arguments"][k]; out.append(("drop:" + k, m))
    out.append(("extra_call", copy.deepcopy(pred) + [copy.deepcopy(pred[0])]))
    out.append(("extra_other_call", copy.deepcopy(pred) + [{"name": pred[0]["name"] + "_x", "arguments": {}}]))
    return out


# declared default equivalences: dropping an argument whose declared default equals the gold value is NOT a
# mutation (CONTRACT §0), so those drops must score correct, and every other drop must score wrong.
def drop_is_default(schema, gold, name, k):
    g = gold[0]["args"]
    if schema.endswith("home") and k == "room":
        return g.get("room") in ("here", "whole house")
    if k == "date":
        return True       # gold dates in these examples equal the next-occurrence default
    if k == "time" and gold[0]["action"] == "create_reminder":
        return g.get("time") == "09:00"
    return False


n_mut = 0
for schema, gold, pred in EX:
    s = score.score_item([gold], pred, schema)
    check(s["outcome"] == "correct_action", f"CONTROL {schema} {pred} scored {s['outcome']}")
    for kind, m in mutations(pred):
        if kind.startswith("drop:") and drop_is_default(schema, gold, None, kind[5:]):
            r = score.score_item([gold], m, schema)
            check(r["outcome"] == "correct_action", f"default-drop {kind} {schema} scored {r['outcome']}")
            continue
        r = score.score_item([gold], m, schema); n_mut += 1
        check(r["outcome"] == "wrong_call", f"MUTANT {kind} {schema} {m} scored {r['outcome']}")
    check(score.score_item([gold], [], schema)["outcome"] == "needless_refusal", f"empty on act {schema}")
    check(score.score_item([gold], None, schema)["outcome"] == "technical_failure", f"None on act {schema}")
# no-act items
check(score.score_item([[]], [], "S1-home")["outcome"] == "correct_nonaction", "empty on no-act")
check(score.score_item([[]], None, "S1-home")["outcome"] == "technical_failure", "None on no-act must not be a refusal")
check(score.score_item([[]], EX[0][2], "S1-home")["outcome"] == "wrong_call", "call on no-act")
# R7 alternatives
g7 = [[{"action": "set_light_level", "args": {"room": "here", "level": 50}}],
      [{"action": "light_power", "args": {"room": "here", "state": "on"}}, {"action": "set_light_level", "args": {"room": "here", "level": 50}}]]
check(score.score_item(g7, [{"name": "set_lights_brightness", "arguments": {"brightness": 50}}], "S1-home")["outcome"] == "correct_action", "R7 a")
check(score.score_item(g7, [{"name": "set_lights_power", "arguments": {"power": "on"}}, {"name": "set_lights_brightness", "arguments": {"brightness": 50}}], "S1-home")["outcome"] == "correct_action", "R7 b")
check(score.score_item(g7, [{"name": "set_lights_power", "arguments": {"power": "on"}}], "S1-home")["outcome"] == "wrong_call", "R7 c")
# unknown tool, out-of-set value, stringly args
check(score.score_item([EX[0][1]], [{"name": "nope", "arguments": {}}], "S1-home")["outcome"] == "wrong_call", "unknown tool")
check(score.score_item([EX[0][1]], [{"name": "set_lights_power", "arguments": {"room": "garage", "power": "off"}}], "S1-home")["outcome"] == "wrong_call", "value outside set")
check(score.score_item([EX[0][1]], [{"name": "set_lights_power", "arguments": '{"room": "kitchen", "power": "off"}'}], "S1-home")["outcome"] == "correct_action", "JSON-string arguments")

# ---- vendor suites: every positive/parallel case, gold = the vendor's own want ----
V = json.load(open(H.parent / "preflight" / "vendor_harness_pinned.json"))
nv = 0
for e in V:
    for c in e["cases"]:
        if not c["want"]:
            continue
        gold = [[{"action": w["name"], "args": w.get("arguments", {})} for w in c["want"]]]
        sid = f"vendor-{e['env']}"
        check(score.score_item(gold, c["want"], sid)["outcome"] == "correct_action", f"vendor CONTROL {c['query']}")
        for kind, m in mutations(c["want"]):
            r = score.score_item(gold, m, sid); nv += 1
            if r["outcome"] != "wrong_call":
                fails.append(f"vendor MUTANT {kind} {e['env']} {c['query']!r} -> {m} scored {r['outcome']}")

print(f"canonical mutants: {n_mut}; vendor mutants: {nv}; failures: {len(fails)}")
for f in fails:
    print("FAIL", f)
sys.exit(1 if fails else 0)
