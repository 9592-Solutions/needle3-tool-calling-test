# /// script
# requires-python = ">=3.11"
# ///
"""V-COUNT distractors: S1 plus 1, 5 or 15 extra tools per app, in the same style as S1, for capabilities the
app contract does NOT have (so under V-COUNT they become servable, and gold changes only for requests they
serve). Order: the first k of the list are added for count 5+k. usage: uv run --no-project contracts/build_distractors.py"""
import json
from pathlib import Path
H = Path(__file__).resolve().parent
def t(name, desc, props, req):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": req}}}
S = lambda d, **k: {"type": "string", "description": d, **k}
I = lambda d, lo, hi: {"type": "integer", "minimum": lo, "maximum": hi, "description": d}
HOME = [
    t("set_heating", "Set the heating (thermostat) to a temperature in degrees Celsius.", {"temperature": I("degrees Celsius, 10 to 30", 10, 30)}, ["temperature"]),
    t("set_blinds", "Open or close the blinds (shades, curtains).", {"position": S("open or closed", enum=["open", "closed"])}, ["position"]),
    t("lock_front_door", "Lock or unlock the front door.", {"state": S("locked or unlocked", enum=["locked", "unlocked"])}, ["state"]),
    t("start_coffee", "Make a coffee with the coffee machine.", {"drink": S("espresso, americano or cappuccino", enum=["espresso", "americano", "cappuccino"])}, ["drink"]),
    t("set_fan_speed", "Set the ceiling fan speed.", {"speed": S("off, low, medium or high", enum=["off", "low", "medium", "high"])}, ["speed"]),
    t("set_tv_power", "Switch the TV (television) on or off.", {"power": S("on or off", enum=["on", "off"])}, ["power"]),
    t("set_speaker_volume", "Set the speaker volume in percent.", {"volume": I("percent, 0 to 100", 0, 100)}, ["volume"]),
    t("arm_alarm_system", "Arm or disarm the home security system.", {"mode": S("armed or disarmed", enum=["armed", "disarmed"])}, ["mode"]),
    t("open_garage", "Open or close the garage door.", {"position": S("open or closed", enum=["open", "closed"])}, ["position"]),
    t("water_garden", "Water the garden for a number of minutes.", {"minutes": I("minutes, 1 to 60", 1, 60)}, ["minutes"]),
    t("start_dishwasher", "Start the dishwasher on a programme.", {"programme": S("eco, normal or intensive", enum=["eco", "normal", "intensive"])}, ["programme"]),
    t("set_oven", "Heat the oven to a temperature in degrees Celsius.", {"temperature": I("degrees Celsius, 50 to 250", 50, 250)}, ["temperature"]),
    t("feed_pet", "Dispense food from the pet feeder.", {"portions": I("number of portions, 1 to 5", 1, 5)}, ["portions"]),
    t("set_humidifier", "Switch the humidifier on or off.", {"power": S("on or off", enum=["on", "off"])}, ["power"]),
    t("play_doorbell_camera", "Show the doorbell camera on a screen.", {"screen": S("tv or phone", enum=["tv", "phone"])}, ["screen"]),
]
DESK = [
    t("start_timer", "Start a countdown timer for a length of time.", {"duration_seconds": I("the length in seconds", 1, 86400)}, ["duration_seconds"]),
    t("send_message", "Send a text message to a contact.", {"contact": S("the contact's name"), "message": S("the message, in the user's words")}, ["contact", "message"]),
    t("create_event", "Add an event to the calendar.", {"title": S("the event title"), "date": S("ISO date YYYY-MM-DD", format="date"), "time": S("24-hour HH:MM", pattern="^([01][0-9]|2[0-3]):[0-5][0-9]$")}, ["title", "date"]),
    t("take_note", "Save a note.", {"text": S("the note, in the user's words")}, ["text"]),
    t("play_music", "Play music by an artist or of a genre.", {"query": S("artist, song or genre")}, ["query"]),
    t("get_weather", "Get the weather forecast for a city.", {"city": S("the city")}, ["city"]),
    t("call_contact", "Phone a contact.", {"contact": S("the contact's name")}, ["contact"]),
    t("send_email", "Send an email.", {"to": S("recipient name or address"), "subject": S("the subject")}, ["to", "subject"]),
    t("set_do_not_disturb", "Turn do-not-disturb on or off.", {"state": S("on or off", enum=["on", "off"])}, ["state"]),
    t("convert_units", "Convert an amount between units.", {"amount": {"type": "number", "description": "the amount"}, "from_unit": S("unit to convert from"), "to_unit": S("unit to convert to")}, ["amount", "from_unit", "to_unit"]),
    t("check_calendar", "List the events on a date.", {"date": S("ISO date YYYY-MM-DD", format="date")}, ["date"]),
    t("start_stopwatch", "Start the stopwatch.", {}, []),
    t("log_expense", "Record a purchase amount in euros.", {"amount": {"type": "number", "exclusiveMinimum": 0, "maximum": 100000, "description": "euros"}}, ["amount"]),
    t("translate_text", "Translate text into a language.", {"text": S("the text"), "language": S("target language")}, ["text", "language"]),
    t("search_web", "Search the web.", {"query": S("the search terms")}, ["query"]),
]
for app, dis in (("home", HOME), ("desk", DESK)):
    base = json.loads((H / "S1" / f"{app}.json").read_text())
    for n in (6, 10, 20):
        (H / "variants" / f"{app}-count{n}.json").write_text(json.dumps(base + dis[: n - 5], indent=2, ensure_ascii=False) + "\n")
