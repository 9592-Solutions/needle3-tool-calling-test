"""Needle 3 scorer (DESIGN §7.1). One scorer for every arm. No LLM judge.

score_item(gold, pred_calls, schema_id) -> dict with
  outcome     : correct_action | correct_nonaction | wrong_call | needless_refusal | technical_failure | ambiguous
  act_item    : whether the contract says the app should act
  diagnostics : tool-selection match, argument precision/recall against the closest acceptable answer

pred_calls is the list of raw calls the system returned ({"name", "arguments"}), [] for "nothing", or None for
a TECHNICAL FAILURE (crash, timeout, malformed output, overflow, transport error). A technical failure is
never counted as a refusal (DESIGN §7.1).

Exact correctness: the canonical call multiset (CONTRACT §0, via contracts/mapping.py) equals one acceptable
gold answer. Order-free, duplicates retained. One right call plus an unwanted one is a wrong call.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "contracts"))
import mapping  # noqa: E402

OUTCOMES = ["correct_action", "correct_nonaction", "wrong_call", "needless_refusal", "technical_failure"]


def _key(call):
    return json.dumps({"action": call["action"], "args": call["args"]}, sort_keys=True, ensure_ascii=False)


def canon_pred(schema_id, pred_calls):
    return [mapping.to_canonical(schema_id, c) for c in pred_calls]


def canon_gold(answer, schema_id):
    if mapping.is_identity(schema_id):
        return [mapping.to_canonical(schema_id, {"name": c["action"], "arguments": c.get("args", {})}) for c in answer]
    return [mapping.canonical_gold_call(c, schema_id) for c in answer]


def _arg_pr(pred, gold):
    """Argument-level precision/recall over (action, arg, value) triples; a diagnostic, never absolution."""
    P = Counter((c["action"], k, json.dumps(v, sort_keys=True)) for c in pred for k, v in c["args"].items())
    G = Counter((c["action"], k, json.dumps(v, sort_keys=True)) for c in gold for k, v in c["args"].items())
    tp = sum((P & G).values())
    return (tp / sum(P.values()) if P else None), (tp / sum(G.values()) if G else None)


def score_item(gold, pred_calls, schema_id):
    if gold == "ambiguous":
        return {"outcome": "ambiguous", "act_item": None}
    answers = [canon_gold(a, schema_id) for a in gold]
    act = any(len(a) > 0 for a in answers)
    if act and any(len(a) == 0 for a in answers):
        raise ValueError("gold mixes act and no-act answers; CONTRACT §0 forbids it")
    if pred_calls is None:
        return {"outcome": "technical_failure", "act_item": act}
    pred = canon_pred(schema_id, pred_calls)
    pk = Counter(map(_key, pred))
    exact = any(pk == Counter(map(_key, a)) for a in answers)
    if exact:
        outcome = "correct_action" if act else "correct_nonaction"
    elif not pred:
        outcome = "needless_refusal"          # nothing on an act item (an empty pred always matches a no-act gold)
    else:
        outcome = "wrong_call"                # a call on a no-act item, or a wrong call on an act item
    diag = {}
    if act and pred:
        best = max(answers, key=lambda a: sum((Counter(map(_key, a)) & pk).values()))
        diag["tool_match"] = Counter(c["action"] for c in pred) == Counter(c["action"] for c in best)
        diag["arg_precision"], diag["arg_recall"] = _arg_pr(pred, best)
        diag["extra_calls"] = max(0, len(pred) - len(best))
    return {"outcome": outcome, "act_item": act, "pred_canonical": pred, **diag}


def needle_calls(parsed, respect_validation=True):
    """What an app receives from a Needle response: function_calls, with calls flagged by the engine's
    validation (ungrounded / negation) withheld, as the vendor harness does. None if the response is not a
    well-formed engine envelope (a technical failure)."""
    if not isinstance(parsed, dict) or "function_calls" not in parsed:
        return None
    if parsed.get("success") is False and parsed.get("error"):
        return None
    got = parsed.get("function_calls") or []
    v = parsed.get("validation") or {}
    if respect_validation and got and (v.get("ungrounded") or v.get("negation")):
        return []
    return got


def empty_kind(parsed):
    """DESIGN §7.1: the three kinds of empty, logged apart."""
    if not isinstance(parsed, dict):
        return None
    if parsed.get("function_calls"):
        v = parsed.get("validation") or {}
        return "validation_flagged" if (v.get("ungrounded") or v.get("negation")) else None
    return "engine_suppressed" if parsed.get("suppressed_calls") else "model_empty"

def macro_cells(pairs):
    """D6 axis: per app, 0.5 * act accuracy (act strata pooled) + 0.5 * mean over N1, N2, N3; mean over apps."""
    import collections as _c
    per = _c.defaultdict(lambda: _c.defaultdict(list))
    for (app, stratum), ok in pairs:
        per[app]["A" if stratum.startswith("A") else stratum].append(ok)
    vals = []
    for app, cells in per.items():
        acc = lambda v: sum(v) / len(v)
        a = acc(cells["A"]) if cells.get("A") else None
        ns = [acc(v) for k, v in cells.items() if k != "A" and v]
        n = sum(ns) / len(ns) if ns else None
        parts = [x for x in (a, n) if x is not None]
        vals.append(sum(parts) / len(parts))
    return sum(vals) / len(vals) if vals else float("nan")
