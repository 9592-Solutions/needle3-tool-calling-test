"""Needle 3 executed scoreboard (DESIGN §7.1): what the app would actually DO with a system's returned calls.

Frozen in FREEZE.md §5. Same scorer as the proposal scoreboard (harness/score.py); this only decides which calls
reach it:
  1. A technical failure (pred_calls is None) executes nothing and stays a technical failure (never a refusal).
  2. Confidence policy (Needle only): if a threshold is set, a bundle whose confidence is missing or below it is
     DEFERRED: nothing executes, and the item is flagged deferred.
  3. Deterministic schema validation: every call must name a tool in the schema the arm was given, and its
     arguments must validate against that tool's `parameters` (JSON Schema 2020-12, formats checked). If ANY call
     in the bundle fails, NOTHING executes (the atomic rule, CONTRACT R1, applied by the app). A null argument is
     read as omitted first (the strict-schema contract renders optional fields as required and nullable).
For Needle, pred_calls is already `score.needle_calls(parsed)` (validation-flagged calls withheld).
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import score  # noqa: E402

_FC = FormatChecker()


def tools_for(schema_file):
    tools = json.loads(Path(schema_file).read_text())
    out = {}
    for t in tools:
        f = t.get("function", t)
        out[f["name"]] = Draft202012Validator(f.get("parameters", {"type": "object"}), format_checker=_FC)
    return out


def valid_bundle(calls, validators):
    for c in calls:
        v = validators.get(c.get("name"))
        if v is None:
            return False
        args = c.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                return False
        if not isinstance(args, dict):
            return False
        args = {k: x for k, x in args.items() if x is not None}   # strict-schema form: null = omitted (FRONTIER.md)
        if any(True for _ in v.iter_errors(args)):
            return False
    return True


def execute_item(gold, pred_calls, schema_id, validators, conf=None, threshold=None):
    if gold == "ambiguous":
        return {"outcome": "ambiguous"}
    if pred_calls is None:
        s = score.score_item(gold, None, schema_id)
        return {**s, "executed": 0, "deferred": False, "invalid": False}
    deferred = bool(pred_calls) and threshold is not None and (conf is None or conf < threshold)
    invalid = bool(pred_calls) and not deferred and not valid_bundle(pred_calls, validators)
    run = [] if (deferred or invalid) else pred_calls
    s = score.score_item(gold, run, schema_id)
    return {**s, "executed": len(run), "deferred": deferred, "invalid": invalid}
