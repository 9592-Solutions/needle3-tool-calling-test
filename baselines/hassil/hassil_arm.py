# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "hassil==3.12.1",
#   "PyYAML==6.0.3",
# ]
# ///
"""Needle 3 baseline arm "hassil": Home Assistant's own English sentence templates (OHF-Voice/intents,
UNMODIFIED, pinned commit) matched with hassil, plus the declared intent-to-tool table in
mapping_table.json.

    predict(text) -> list[{"action", "args"}] | []

The templates are NOT copied into this repo. They are loaded from a clone of OHF-Voice/intents at the
pinned commit (PINS.md), located by the env var NEEDLE3_INTENTS_DIR or the `intents_dir` argument, using
the repository's OWN loader (script/intentfest/util.py: load_intents_dict, the function its
merged_output command uses to build the grammar Home Assistant ships), filtered to the supported
intents exactly as merged_output filters them.

CLI:  NEEDLE3_INTENTS_DIR=/path/to/intents uv run hassil_arm.py "turn off the kitchen lights"
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from hassil import Intents, TextSlotList, TextSlotValue, recognize_best
from hassil.expression import TextChunk

HERE = Path(__file__).resolve().parent
TABLE = json.loads((HERE / "mapping_table.json").read_text())
PINNED_SHA = TABLE["pins"]["OHF-Voice/intents"]

CANON_COLORS = {"red", "orange", "yellow", "green", "blue", "purple", "pink", "white"}
TEMPERATURE_NAMES = {  # matched on the spoken text of the {temperature} slot, never on a kelvin number
    "warm white": "warm white",
    "cool white": "cool white",
    "cold white": "cool white",
    "daylight": "cool white",
    "day light": "cool white",
}
HERE_ROOM = TABLE["satellite_context"]["area"]


class HassilArm:
    def __init__(self, intents_dir: str | os.PathLike | None = None, check_pin: bool = True):
        d = intents_dir or os.environ.get("NEEDLE3_INTENTS_DIR")
        if not d:
            raise RuntimeError("set NEEDLE3_INTENTS_DIR (or pass intents_dir) to the pinned OHF-Voice/intents clone")
        self.intents_dir = Path(d).resolve()
        if check_pin:
            sha = subprocess.run(["git", "-C", str(self.intents_dir), "rev-parse", "HEAD"],
                                 capture_output=True, text=True, check=True).stdout.strip()
            if sha != PINNED_SHA:
                raise RuntimeError(f"intents clone at {sha}, pinned {PINNED_SHA}")
            dirty = subprocess.run(["git", "-C", str(self.intents_dir), "status", "--porcelain", "--", "sentences",
                                    "lists", "rules", "intents.yaml", "script"],
                                   capture_output=True, text=True, check=True).stdout.strip()
            if dirty:
                raise RuntimeError(f"intents clone is modified:\n{dirty}")
        self.intents = self._load_intents()
        self.slot_lists = self._slot_lists()
        self.entity_by_name = {n: eid for eid, e in TABLE["entities"].items() if not eid.startswith("_")
                               for n in e["names"]}

    def _load_intents(self) -> Intents:
        import yaml
        sys.path.insert(0, str(self.intents_dir))
        try:
            from script.intentfest.util import load_intents_dict  # upstream's own loader, unmodified
        finally:
            sys.path.pop(0)
        merged = load_intents_dict("en")
        info = yaml.safe_load((self.intents_dir / "intents.yaml").read_text())
        supported = {k for k, v in info.items() if v.get("supported", True)}
        merged["intents"] = {  # same filter as script/intentfest/merged_output.py
            k: {**v, "data": [d for d in v["data"] if d["sentences"]]}
            for k, v in merged["intents"].items() if k in supported
        }
        return Intents.from_dict(merged)

    @staticmethod
    def _slot_lists() -> dict[str, TextSlotList]:
        areas = [TextSlotValue(TextChunk(alias), room)
                 for room, aliases in TABLE["areas"].items() if not room.startswith("_") for alias in aliases]
        names = [TextSlotValue(TextChunk(n), n, context={"domain": e["domain"]})
                 for eid, e in TABLE["entities"].items() if not eid.startswith("_") for n in e["names"]]
        return {
            "area": TextSlotList(name="area", values=areas),
            "name": TextSlotList(name="name", values=names),
            "floor": TextSlotList(name="floor", values=[]),
        }

    def recognize(self, text: str):
        return recognize_best(
            text, self.intents, slot_lists=self.slot_lists,
            intent_context={"area": {"value": HERE_ROOM, "text": HERE_ROOM}},
            language="en", best_slot_name="name",
        )

    def predict(self, text: str) -> list[dict[str, Any]]:
        try:
            r = self.recognize(text)
        except Exception:  # hassil raising on odd input is a non-match, not a crash of the study
            return []
        if r is None:
            return []
        return self._map(r)

    def _map(self, r) -> list[dict[str, Any]]:
        intent = r.intent.name
        ent = {k: v.value for k, v in r.entities.items()}
        text_of = {k: (v.text or "").strip().lower() for k, v in r.entities.items()}
        area = ent.get("area")
        name = ent.get("name")
        eid = self.entity_by_name.get(name) if name is not None else None
        e = TABLE["entities"].get(eid) if eid else None
        if name is not None and e is None:
            return []

        def light_target():
            if e is not None:
                if e["domain"] != "light":
                    return None
                if area is not None and area != e["area"]:
                    return None
                return e["area"]
            if ent.get("domain") not in (None, "light"):
                return None
            return area

        if intent in ("HassTurnOn", "HassTurnOff"):
            state = "on" if intent == "HassTurnOn" else "off"
            if e is not None and e["domain"] == "switch":
                return [] if area is not None else [{"action": "smart_plug", "args": {"state": state}}]
            if e is None and ent.get("domain") != "light":
                return []
            if "device_class" in ent:
                return []
            room = light_target()
            if e is None and room is None:
                room = "whole house"  # light domain with no area and no here-context: the domain_all combination
            if room is None:
                return []
            return [{"action": "light_power", "args": {"room": room, "state": state}}]

        if intent == "HassLightSet":
            room = light_target()
            if room is None:
                return []
            if "brightness" in ent:
                lv = ent["brightness"]
                if isinstance(lv, float) and lv.is_integer():
                    lv = int(lv)
                if not isinstance(lv, int) or isinstance(lv, bool) or not 1 <= lv <= 100:
                    return []
                return [{"action": "set_light_level", "args": {"room": room, "level": lv}}]
            if "color" in ent:
                c = str(ent["color"]).lower()
                return [{"action": "set_light_color", "args": {"room": room, "color": c}}] if c in CANON_COLORS else []
            if "temperature" in ent:
                c = TEMPERATURE_NAMES.get(" ".join(text_of["temperature"].split()))
                return [{"action": "set_light_color", "args": {"room": room, "color": c}}] if c else []
            return []

        if intent == "HassVacuumStart":
            if e is not None and e["domain"] == "vacuum" and area is None:
                return [{"action": "vacuum", "args": {"command": "start", "room": "whole house"}}]
            return []
        if intent == "HassVacuumCleanArea":
            if (e is not None and e["domain"] != "vacuum") or area is None:
                return []
            return [{"action": "vacuum", "args": {"command": "start", "room": area}}]
        if intent == "HassVacuumReturnToBase":
            if e is not None and e["domain"] == "vacuum" and area is None:
                return [{"action": "vacuum", "args": {"command": "dock"}}]
            return []
        return []


_ARM: HassilArm | None = None


def predict(text: str) -> list[dict[str, Any]]:
    global _ARM
    if _ARM is None:
        _ARM = HassilArm()
    return _ARM.predict(text)


if __name__ == "__main__":
    arm = HassilArm()
    for t in sys.argv[1:]:
        r = arm.recognize(t)
        print(json.dumps({"text": t, "intent": r.intent.name if r else None,
                          "entities": {k: v.value for k, v in r.entities.items()} if r else None,
                          "predict": arm.predict(t)}))
