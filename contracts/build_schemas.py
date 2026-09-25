# /// script
# requires-python = ">=3.11"
# ///
"""Derive S1 from S0 by the vendor's tool-design checklist, and write the diagnostic variant schemas.
Every edit is listed in S1/CHECKLIST.md with the guide rule it applies. Deterministic: re-running rewrites
identical files. usage: uv run --no-project contracts/build_schemas.py"""
import copy, json
from pathlib import Path
H = Path(__file__).resolve().parent
S0 = {a: json.loads((H / "S0" / f"{a}.json").read_text()) for a in ("home", "desk")}

def fn(tools, name):
    return next(t["function"] for t in tools if t["function"]["name"] == name)

ROOMS_S1 = ["living room", "kitchen", "bedroom", "bathroom", "hallway", "study", "whole house", "this room"]
COLORS_S1 = ["red", "orange", "yellow", "green", "blue", "purple", "pink", "white", "warm white", "cool white"]
ROOM_DESC = ("The room whose lights change: living room (lounge), kitchen, bedroom, bathroom, hallway (hall), study, "
             "whole house (every room, all the lights), or this room (the room the user is in).")

def s1_home():
    t = copy.deepcopy(S0["home"])
    for name in ("set_lights_power", "set_lights_brightness", "set_lights_color"):
        f = fn(t, name); r = f["parameters"]["properties"]["room"]
        r["enum"] = ROOMS_S1; r["default"] = "this room"; r["description"] = ROOM_DESC
    f = fn(t, "set_lights_power")
    f["description"] = "Turn a room's lights on or off (switch on, switch off, turn out)."
    f["parameters"]["properties"]["power"]["description"] = "on or off"
    f = fn(t, "set_lights_brightness")
    f["description"] = "Set a room's lights to a brightness percentage from 1 to 100 (full or max is 100, half is 50)."
    f["parameters"]["properties"]["brightness"]["description"] = "brightness in percent, a whole number from 1 to 100"
    f = fn(t, "set_lights_color")
    f["description"] = "Change the colour of a room's lights."
    c = f["parameters"]["properties"]["color"]; c["enum"] = COLORS_S1
    c["description"] = "the colour: red, orange, yellow, green, blue, purple (violet), pink, white, warm white (warm, soft white), cool white (cool, daylight)"
    f = fn(t, "control_vacuum")
    f["description"] = "Start the robot vacuum (roomba, hoover) cleaning, stop it, or send it back to its dock."
    a = f["parameters"]["properties"]["action"]; a["description"] = "start cleaning, stop, or dock (go back to its base)"
    r = f["parameters"]["properties"]["room"]
    r["enum"] = ["living room", "kitchen", "bedroom", "bathroom", "hallway", "study", "whole house", "this room"]
    r["default"] = "whole house"
    r["description"] = "the room to clean when starting: living room, kitchen, bedroom, bathroom, hallway, study, whole house, or this room"
    f = fn(t, "set_plug_power")
    f["description"] = "Switch the smart plug (socket, outlet, wemo) on or off."
    f["parameters"]["properties"]["power"]["description"] = "on or off"
    return t

TIME_DESC = "clock time in 24-hour HH:MM, e.g. 07:30 for 7:30 am or 19:30 for 7:30 pm"
DATE_DESC = "ISO date YYYY-MM-DD, e.g. 2026-06-12"
def s1_desk():
    t = copy.deepcopy(S0["desk"])
    for name in ("set_alarm", "remove_alarm", "create_reminder"):
        p = fn(t, name)["parameters"]["properties"]
        p["time"]["description"] = TIME_DESC; p["date"]["description"] = DATE_DESC
    fn(t, "set_alarm")["description"] = "Set an alarm (wake me up) at a clock time, on a date if one is given."
    fn(t, "remove_alarm")["description"] = "Remove (cancel, delete, turn off) the alarm set at a clock time, on a date if one is given."
    for name, verb in (("add_list_item", "Add one item to"), ("remove_list_item", "Remove (take off, delete) one item from")):
        f = fn(t, name); f["description"] = f"{verb} the shopping list, the to-do list or the packing list."
        l = f["parameters"]["properties"]["list"]; l["enum"] = ["shopping", "to-do", "packing"]
        l["description"] = "shopping (grocery, groceries), to-do (to do, tasks) or packing (trip, travel)"
        f["parameters"]["properties"]["item"]["description"] = "the one item, in the user's words, e.g. two bottles of milk"
    f = fn(t, "create_reminder")
    f["description"] = "Create a reminder (remind me, don't let me forget) at a clock time on a date."
    p = f["parameters"]["properties"]
    p["text"]["description"] = "what to be reminded about, in the user's words, e.g. take the bins out"
    p["time"]["default"] = "09:00"
    return t

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

S1 = {"home": s1_home(), "desk": s1_desk()}
for a in S1: dump(H / "S1" / f"{a}.json", S1[a])

# ---- V-REL: S1 home, plug removed, adjust_light_level added (5 tools) ----
rel = [x for x in copy.deepcopy(S1["home"]) if x["function"]["name"] != "set_plug_power"]
rel.insert(2, {"type": "function", "function": {"name": "adjust_lights_brightness",
    "description": "Make a room's lights brighter or dimmer by one step.",
    "parameters": {"type": "object", "properties": {
        "room": {"type": "string", "enum": ROOMS_S1, "default": "this room", "description": ROOM_DESC},
        "direction": {"type": "string", "enum": ["up", "down"], "description": "up (brighter, raise, more light) or down (dim, dimmer, lower, less bright)"}},
        "required": ["direction"]}}})
dump(H / "variants" / "home-rel.json", rel)

# ---- V-ROOMREQ: room required, no default, in the three light tools ----
rq = copy.deepcopy(S1["home"])
for name in ("set_lights_power", "set_lights_brightness", "set_lights_color"):
    f = fn(rq, name); r = f["parameters"]["properties"]["room"]; r.pop("default", None)
    f["parameters"]["required"] = ["room"] + f["parameters"]["required"]
dump(H / "variants" / "home-roomreq.json", rq)

# ---- V-TIMER-S / V-TIMER-U: desk with remove_alarm replaced by a timer ----
def timer_variant(params, req):
    d = [x for x in copy.deepcopy(S1["desk"]) if x["function"]["name"] != "remove_alarm"]
    d.insert(1, {"type": "function", "function": {"name": "start_timer",
        "description": "Start a countdown timer for a length of time.",
        "parameters": {"type": "object", "properties": params, "required": req}}})
    return d
dump(H / "variants" / "desk-timer-seconds.json", timer_variant(
    {"duration_seconds": {"type": "integer", "minimum": 1, "maximum": 86400, "description": "the length in seconds, e.g. 1500 for 25 minutes"}},
    ["duration_seconds"]))
dump(H / "variants" / "desk-timer-units.json", timer_variant(
    {"amount": {"type": "integer", "minimum": 1, "maximum": 1440, "description": "how many units, e.g. 25"},
     "unit": {"type": "string", "enum": ["seconds", "minutes", "hours"], "description": "seconds, minutes or hours"}},
    ["amount", "unit"]))

# ---- V-DISPATCH: one tool per app ----
dump(H / "variants" / "home-dispatch.json", [{"type": "function", "function": {"name": "home_control",
    "description": "Control the home: lights (power, brightness, colour), the robot vacuum and the smart plug.",
    "parameters": {"type": "object", "properties": {
        "action": {"type": "string", "enum": ["lights power", "lights brightness", "lights colour", "vacuum", "plug"],
                   "description": "what to control"},
        "room": {"type": "string", "enum": ROOMS_S1, "description": ROOM_DESC},
        "power": {"type": "string", "enum": ["on", "off"], "description": "on or off, for lights power and plug"},
        "brightness": {"type": "integer", "minimum": 1, "maximum": 100, "description": "percent, for lights brightness"},
        "color": {"type": "string", "enum": COLORS_S1, "description": "for lights colour"},
        "vacuum_action": {"type": "string", "enum": ["start", "stop", "dock"], "description": "for vacuum"}},
        "required": ["action"]}}}])
dump(H / "variants" / "desk-dispatch.json", [{"type": "function", "function": {"name": "desk_action",
    "description": "Manage alarms, the shopping, to-do and packing lists, and reminders.",
    "parameters": {"type": "object", "properties": {
        "action": {"type": "string", "enum": ["set alarm", "remove alarm", "add to list", "remove from list", "create reminder"],
                   "description": "what to do"},
        "time": {"type": "string", "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$", "description": TIME_DESC},
        "date": {"type": "string", "format": "date", "description": DATE_DESC},
        "list": {"type": "string", "enum": ["shopping", "to-do", "packing"], "description": "for list actions"},
        "item": {"type": "string", "description": "one list item, in the user's words"},
        "text": {"type": "string", "description": "what to be reminded about, in the user's words"}},
        "required": ["action"]}}}])

# ---- V-RENAME: tool names absent from Needle 1/2's 232-tool list ----
RENAME = {"set_lights_power": "lumen_switch", "set_lights_brightness": "lumen_level", "set_lights_color": "lumen_hue",
          "control_vacuum": "floorbot", "set_plug_power": "outlet_toggle",
          "set_alarm": "wake_bell_add", "remove_alarm": "wake_bell_drop", "add_list_item": "ledger_push",
          "remove_list_item": "ledger_pull", "create_reminder": "nudge_note"}
for a in S1:
    r = copy.deepcopy(S1[a])
    for x in r: x["function"]["name"] = RENAME[x["function"]["name"]]
    dump(H / "variants" / f"{a}-renamed.json", r)
dump(H / "variants" / "rename-table.json", RENAME)
