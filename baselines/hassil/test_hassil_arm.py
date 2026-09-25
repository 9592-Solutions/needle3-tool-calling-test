# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "hassil==3.12.1",
#   "PyYAML==6.0.3",
# ]
# ///
"""Self-test for the hassil arm on sentences written by hand for this test (no dataset material).

    NEEDLE3_INTENTS_DIR=/private/tmp/needle3-intents uv run test_hassil_arm.py

Exits non-zero on any mismatch. The cases pin the declared mapping (mapping_table.json), including the
controls that must return []: a range violation, a colour upstream has but the contract lacks, an
unknown room, negation, a state question, an appliance with no plug, and a sentence no template covers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hassil_arm import HassilArm  # noqa: E402


def c(action, **args):
    return {"action": action, "args": args}


CASES = [
    ("switch off the bathroom lights", [c("light_power", room="bathroom", state="off")]),
    ("turn the lights on", [c("light_power", room="here", state="on")]),
    ("turn off all the lights in the house", [c("light_power", room="whole house", state="off")]),
    ("turn on the lights in the sitting room", [c("light_power", room="living room", state="on")]),
    ("turn on the hallway light", [c("light_power", room="hallway", state="on")]),
    ("set the study brightness to 35%", [c("set_light_level", room="study", level=35)]),
    ("set the brightness to twelve percent", [c("set_light_level", room="here", level=12)]),
    ("set the brightness to the minimum", [c("set_light_level", room="here", level=1)]),
    ("set the brightness to 0%", []),                        # contract range 1..100
    ("set the brightness to 101%", []),                      # outside upstream range, no match
    ("make the bedroom purple", [c("set_light_color", room="bedroom", color="purple")]),
    ("make the lights pink", [c("set_light_color", room="here", color="pink")]),
    ("make the kitchen brown", []),                          # upstream colour, not in COLORS
    ("set the color temperature to daylight", [c("set_light_color", room="here", color="cool white")]),
    ("set the color temperature to 3000 kelvin", []),        # numeric kelvin is unmapped
    ("vacuum the study", [c("vacuum", command="start", room="study")]),
    ("start the hoover", [c("vacuum", command="start", room="whole house")]),
    ("return the robot vacuum to base", [c("vacuum", command="dock")]),
    ("turn on the outlet", [c("smart_plug", state="on")]),
    ("switch off the smart plug", [c("smart_plug", state="off")]),
    ("turn on the lights in the garage", []),                # not an area
    ("don't switch off the lights", []),
    ("is the kitchen light on", []),
    ("turn off the television", []),
    ("make the living room lamps a little brighter", []),
]


def main():
    arm = HassilArm()
    bad = 0
    for text, want in CASES:
        got = arm.predict(text)
        key = lambda calls: sorted(repr(sorted(x["args"].items())) + x["action"] for x in calls)  # noqa: E731
        ok = key(got) == key(want)
        bad += not ok
        print(("ok  " if ok else "FAIL"), text, "->", got, "" if ok else f"(want {want})")
    print(f"{len(CASES) - bad}/{len(CASES)} passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
