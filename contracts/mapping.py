"""Total mapping from every schema's call to the canonical action form of CONTRACT.md, plus the declared
normalisation (CONTRACT R5) and default filling (CONTRACT §0). Shared by every arm's scorer; no arm-specific
code. Pure standard library.

    to_canonical(schema_id, {"name": ..., "arguments": {...}}) -> {"action": ..., "args": {...}}

A name the schema does not declare maps to action "__unknown__:<name>" (always wrong). An argument the
action does not take is KEPT under its raw name, so it makes the call wrong rather than vanishing. A value
outside the canonical set is kept as given (after case/whitespace folding), so it can never equal gold.
"""
import datetime as _dt
import re

NOW = _dt.datetime(2026, 6, 10, 14, 30)          # the desk app's fixed fact line (CONTRACT §3)
FACT_LINE = "date: 2026-06-10 Wed 14:30; locale: en-US"

ROOMS = {"living room", "kitchen", "bedroom", "bathroom", "hallway", "study", "whole house", "here"}
COLORS = {"red", "orange", "yellow", "green", "blue", "purple", "pink", "white", "warm white", "cool white"}
LISTS = {"shopping", "to-do", "packing"}

# schema-specific value spellings -> canonical value (anything absent passes through folded)
VALUE_MAP = {
    "room": {"living_room": "living room", "whole_house": "whole house", "current_room": "here", "this room": "here"},
    "color": {"warm_white": "warm white", "cool_white": "cool white"},
    "list": {"todo": "to-do"},
}

# per-schema: raw tool name -> (canonical action, {raw arg -> canonical arg})
_HOME_S = {
    "set_lights_power": ("light_power", {"room": "room", "power": "state"}),
    "set_lights_brightness": ("set_light_level", {"room": "room", "brightness": "level"}),
    "set_lights_color": ("set_light_color", {"room": "room", "color": "color"}),
    "control_vacuum": ("vacuum", {"action": "command", "room": "room"}),
    "set_plug_power": ("smart_plug", {"power": "state"}),
}
_DESK_S = {
    "set_alarm": ("set_alarm", {"time": "time", "date": "date"}),
    "remove_alarm": ("remove_alarm", {"time": "time", "date": "date"}),
    "add_list_item": ("add_to_list", {"item": "item", "list": "list"}),
    "remove_list_item": ("remove_from_list", {"item": "item", "list": "list"}),
    "create_reminder": ("create_reminder", {"text": "text", "time": "time", "date": "date"}),
}
_REL = {"adjust_lights_brightness": ("adjust_light_level", {"room": "room", "direction": "direction"})}
_TIMER = {"start_timer": ("start_timer", {"duration_seconds": "duration_seconds", "amount": "amount", "unit": "unit"})}
RENAME = {"set_lights_power": "lumen_switch", "set_lights_brightness": "lumen_level", "set_lights_color": "lumen_hue",
          "control_vacuum": "floorbot", "set_plug_power": "outlet_toggle",
          "set_alarm": "wake_bell_add", "remove_alarm": "wake_bell_drop", "add_list_item": "ledger_push",
          "remove_list_item": "ledger_pull", "create_reminder": "nudge_note"}

TABLES = {
    "S0-home": _HOME_S, "S1-home": _HOME_S, "S0-desk": _DESK_S, "S1-desk": _DESK_S,
    "home-roomreq": _HOME_S,
    "home-rel": {k: v for k, v in _HOME_S.items() if k != "set_plug_power"} | _REL,
    "desk-timer-seconds": {k: v for k, v in _DESK_S.items() if k != "remove_alarm"} | _TIMER,
    "desk-timer-units": {k: v for k, v in _DESK_S.items() if k != "remove_alarm"} | _TIMER,
    "home-renamed": {RENAME[k]: v for k, v in _HOME_S.items()},
    "desk-renamed": {RENAME[k]: v for k, v in _DESK_S.items()},
}
for _n in (6, 10, 20):   # distractors keep their own names (identity), base tools map as S1
    TABLES[f"home-count{_n}"] = _HOME_S
    TABLES[f"desk-count{_n}"] = _DESK_S
IDENTITY_SCHEMAS = {"vendor-smart_home"}     # V-VENDOR: gold uses the vendor's own names
DISPATCH = {
    "home-dispatch": ("home_control", {
        "lights power": ("light_power", {"room": "room", "power": "state"}),
        "lights brightness": ("set_light_level", {"room": "room", "brightness": "level"}),
        "lights colour": ("set_light_color", {"room": "room", "color": "color"}),
        "vacuum": ("vacuum", {"vacuum_action": "command", "room": "room"}),
        "plug": ("smart_plug", {"power": "state"})}),
    "desk-dispatch": ("desk_action", {
        "set alarm": ("set_alarm", {"time": "time", "date": "date"}),
        "remove alarm": ("remove_alarm", {"time": "time", "date": "date"}),
        "add to list": ("add_to_list", {"item": "item", "list": "list"}),
        "remove from list": ("remove_from_list", {"item": "item", "list": "list"}),
        "create reminder": ("create_reminder", {"text": "text", "time": "time", "date": "date"})}),
}
LIGHT_ACTIONS = {"light_power", "set_light_level", "set_light_color", "adjust_light_level"}
NUMERIC = {"level", "duration_seconds", "amount"}
UNIT_S = {"seconds": 1, "minutes": 60, "hours": 3600}


def _fold(v):
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v.strip().lower())
    return v


def _deep(v):
    """Recursive fold for identity schemas (vendor environments): strings lowercased and whitespace-collapsed,
    integral floats to int, applied inside dicts and lists."""
    if isinstance(v, dict):
        return {k: _deep(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_deep(x) for x in v]
    return _fold(_num(v))


def is_identity(schema_id):
    return schema_id in IDENTITY_SCHEMAS or schema_id.startswith("vendor-")


def _num(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v.strip()):
        v = float(v.strip())
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _time(v):
    if isinstance(v, str):
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", v.strip())
        if m:
            return f"{int(m.group(1)):02d}:{m.group(2)}"
    return _fold(v)


def _text(v, reminder=False):
    if not isinstance(v, str):
        return v
    s = re.sub(r"[^\w\s'-]", " ", v.lower())
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(a|an|the|some|my) ", "", s)
    if reminder:
        s = re.sub(r"^(to|about) ", "", s)
        s = re.sub(r"^(a|an|the|some|my) ", "", s)
    return s


def next_occurrence(hhmm):
    """Date of the next occurrence of a clock time strictly after NOW (CONTRACT §3)."""
    try:
        h, m = map(int, hhmm.split(":"))
    except Exception:
        return None
    return (NOW.date() if (h, m) > (NOW.hour, NOW.minute) else NOW.date() + _dt.timedelta(days=1)).isoformat()


def normalise_args(action, args, schema_id):
    out = {}
    for k, v in args.items():
        if k in VALUE_MAP:
            v = _fold(v); v = VALUE_MAP[k].get(v, v)
        elif k in NUMERIC:
            v = _num(v)
        elif k == "time":
            v = _time(v)
        elif k == "date":
            v = _fold(v)
        elif k == "item":
            v = _text(v)
        elif k == "text":
            v = _text(v, reminder=True)
        else:
            v = _fold(v)
        out[k] = v
    # timer units -> seconds (V-TIMER-U)
    if action == "start_timer" and "amount" in out and "unit" in out and "duration_seconds" not in out:
        a, u = out.pop("amount"), out.pop("unit")
        out["duration_seconds"] = a * UNIT_S[u] if isinstance(a, (int, float)) and u in UNIT_S else f"{a} {u}"
    # declared defaults (CONTRACT §0: omitted == default, and only the declared ones)
    if action in LIGHT_ACTIONS and "room" not in out and schema_id != "home-roomreq":
        out["room"] = "here"
    if action == "vacuum":
        if out.get("command") == "start":
            out.setdefault("room", "whole house")
        else:
            out.pop("room", None)              # CONTRACT §2: room ignored on stop and dock
    if action == "create_reminder":
        out.setdefault("time", "09:00")
    if action in ("set_alarm", "remove_alarm", "create_reminder") and "date" not in out and isinstance(out.get("time"), str):
        d = next_occurrence(out["time"])
        if d:
            out["date"] = d
    return out


def to_canonical(schema_id, call):
    name = call.get("name")
    args = call.get("arguments") or {}
    if isinstance(args, str):                  # some hosts return arguments as a JSON string
        import json
        try:
            args = json.loads(args)
        except Exception:
            return {"action": f"__unparseable_args__:{name}", "args": {"raw": args}}
    if not isinstance(args, dict):
        return {"action": f"__bad_args__:{name}", "args": {"raw": repr(args)}}
    if is_identity(schema_id):
        return {"action": name, "args": {k: _deep(v) for k, v in args.items()}}
    if schema_id in DISPATCH:
        tool, acts = DISPATCH[schema_id]
        if name != tool:
            return {"action": f"__unknown__:{name}", "args": args}
        a = _fold(args.get("action"))
        if a not in acts:
            return {"action": f"__unknown_dispatch__:{a}", "args": args}
        action, amap = acts[a]
        raw = {k: v for k, v in args.items() if k != "action"}
    else:
        table = TABLES[schema_id]
        if name not in table:
            if schema_id.startswith(("home-count", "desk-count")):   # a distractor: its own name
                return {"action": name, "args": {k: _deep(v) for k, v in args.items()}}
            return {"action": f"__unknown__:{name}", "args": args}
        action, amap = table[name]
        raw = args
    mapped = {amap.get(k, f"__extra__:{k}"): v for k, v in raw.items() if v is not None}
    return {"action": action, "args": normalise_args(action, mapped, schema_id)}


def canonical_gold_call(call, schema_id="S1-home"):
    """Gold calls are written canonically; this applies the same normalisation and defaults to them."""
    return {"action": call["action"], "args": normalise_args(call["action"], dict(call.get("args", {})), schema_id)}
