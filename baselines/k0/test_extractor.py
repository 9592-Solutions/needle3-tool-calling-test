"""Author-made utterances (not from any dataset) exercising the K0 extractor."""
import json
import os
import unittest

from extractor import extract, split

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "contracts")
FACT = "date: 2026-06-10 Wed 14:30; locale: en-US"


def tools(s, app):
    with open(os.path.join(C, s, f"{app}.json")) as f:
        return {t["function"]["name"]: t for t in json.load(f)}


H0, D0, H1, D1 = tools("S0", "home"), tools("S0", "desk"), tools("S1", "home"), tools("S1", "desk")


class Home(unittest.TestCase):
    def test_power(self):
        self.assertEqual(extract(H0["set_lights_power"], "turn off the kitchen lights", None),
                         {"power": "off", "room": "kitchen"})
        self.assertEqual(extract(H0["set_lights_power"], "lights on in the living room", None),
                         {"power": "on", "room": "living_room"})
        self.assertEqual(extract(H1["set_lights_power"], "switch off the lights in the lounge", None),
                         {"power": "off", "room": "living room"})
        self.assertEqual(extract(H1["set_lights_power"], "turn out all the lights", None),
                         {"power": "off", "room": "whole house"})
        self.assertEqual(extract(H0["set_lights_power"], "turn the lights on", None), {"power": "on"})
        self.assertIsNone(extract(H0["set_lights_power"], "the lights in the study", None))

    def test_brightness(self):
        self.assertEqual(extract(H0["set_lights_brightness"], "dim the bedroom to 30%", None),
                         {"brightness": 30, "room": "bedroom"})
        self.assertEqual(extract(H1["set_lights_brightness"], "set the hall lights to seventy five percent", None),
                         {"brightness": 75, "room": "hallway"})
        self.assertEqual(extract(H1["set_lights_brightness"], "full brightness in the kitchen", None),
                         {"brightness": 100, "room": "kitchen"})
        self.assertIsNone(extract(H0["set_lights_brightness"], "brightness to 150", None))
        self.assertIsNone(extract(H0["set_lights_brightness"], "make it a bit brighter", None))
        self.assertIsNone(extract(H0["set_lights_brightness"], "full brightness", None))  # S0 declares no 'full'

    def test_color(self):
        self.assertEqual(extract(H1["set_lights_color"], "make the bedroom lights violet", None),
                         {"color": "purple", "room": "bedroom"})
        self.assertEqual(extract(H0["set_lights_color"], "set the study to warm white", None),
                         {"color": "warm_white", "room": "study"})
        self.assertEqual(extract(H1["set_lights_color"], "daylight please", None), {"color": "cool white"})

    def test_vacuum(self):
        self.assertEqual(extract(H0["control_vacuum"], "vacuum the kitchen", None),
                         {"action": "start", "room": "kitchen"})
        self.assertEqual(extract(H1["control_vacuum"], "stop cleaning", None), {"action": "stop"})
        self.assertEqual(extract(H1["control_vacuum"], "send the roomba back to its base", None),
                         {"action": "dock"})
        self.assertEqual(extract(H0["control_vacuum"], "stop the vacuum in the kitchen", None),
                         {"action": "stop"})

    def test_plug(self):
        self.assertEqual(extract(H1["set_plug_power"], "switch the socket on", None), {"power": "on"})
        self.assertEqual(extract(H0["set_plug_power"], "turn off the smart plug", None), {"power": "off"})


class Desk(unittest.TestCase):
    def test_alarm(self):
        self.assertEqual(extract(D0["set_alarm"], "wake me up at 6:45 tomorrow", FACT),
                         {"time": "06:45", "date": "2026-06-11"})
        self.assertEqual(extract(D1["set_alarm"], "set an alarm for 7pm on friday", FACT),
                         {"time": "19:00", "date": "2026-06-12"})
        self.assertEqual(extract(D1["set_alarm"], "alarm at half past six", FACT), {"time": "06:30"})
        self.assertEqual(extract(D0["set_alarm"], "set an alarm in 20 minutes", FACT), {"time": "14:50"})
        self.assertIsNone(extract(D0["set_alarm"], "set an alarm", FACT))
        self.assertIsNone(extract(D0["set_alarm"], "set an alarm for 25:00", FACT))
        self.assertEqual(extract(D1["remove_alarm"], "cancel my 7:30 am alarm on June 15th", FACT),
                         {"time": "07:30", "date": "2026-06-15"})

    def test_lists(self):
        self.assertEqual(extract(D0["add_list_item"], "add milk to my shopping list", FACT),
                         {"list": "shopping", "item": "milk"})
        self.assertEqual(extract(D0["add_list_item"], "put call the plumber on the to-do list", FACT),
                         {"list": "todo", "item": "call the plumber"})
        self.assertEqual(extract(D1["add_list_item"], "add two bottles of milk to the grocery list", FACT),
                         {"list": "shopping", "item": "two bottles of milk"})
        self.assertEqual(extract(D1["add_list_item"], "add packing tape to my shopping list", FACT),
                         {"list": "shopping", "item": "packing tape"})
        self.assertEqual(extract(D1["remove_list_item"], "take sunscreen off the travel list", FACT),
                         {"list": "packing", "item": "sunscreen"})
        self.assertIsNone(extract(D0["add_list_item"], "add milk", FACT))

    def test_reminder(self):
        self.assertEqual(extract(D0["create_reminder"], "remind me to take the bins out tomorrow at 7pm", FACT),
                         {"text": "take the bins out", "time": "19:00", "date": "2026-06-11"})
        self.assertEqual(extract(D1["create_reminder"], "remind me in an hour to check the oven", FACT),
                         {"text": "check the oven", "time": "15:30"})
        self.assertEqual(extract(D1["create_reminder"], "don't let me forget to water the plants", FACT),
                         {"text": "water the plants"})
        self.assertIsNone(extract(D0["create_reminder"], "remind me at 5pm", FACT))


class Split(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split("turn off the lights and start the vacuum"),
                         ["turn off the lights", "start the vacuum"])
        self.assertEqual(split("add eggs to the shopping list, then remind me to cook at 6pm"),
                         ["add eggs to the shopping list", "remind me to cook at 6pm"])
        self.assertEqual(split("dim the lights; lock up"), ["dim the lights", "lock up"])
        self.assertEqual(split("stop the vacuum and then dock it"), ["stop the vacuum", "dock it"])


if __name__ == "__main__":
    unittest.main()
