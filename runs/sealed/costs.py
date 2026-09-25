"""Needle 3 sealed run: worst-case cost of a stage (FREEZE §10 rates), from the input line counts, printed in dollars.
Rates: LLM call at list price, no caching, 3,000 prompt tokens + the 600-token cap: llm-a $0.000444, llm-named
$0.00042 (both arms: $0.000864 per item). Contract-in-prompt calls are scaled up by their extra prompt length
(CONTRACT text at 3.5 characters per token, conservative for English). Needle $0.30 per 1,000 five-tool requests,
tool-count multipliers 6: 1.2, 10: 1.6, 20: 2.6 (FREEZE gives 2.6 for 20; the others are interpolated upward from
preflight wall times 6.6 s and 9.4 s against 6.2 s).
usage: python3 runs/sealed/costs.py <stage>"""
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
LLM2 = 0.000444 + 0.00042
NEEDLE = 0.30 / 1000


def n(*names):
    return sum(sum(1 for _ in open(H / "inputs" / f"{x}.jsonl")) for x in names)


def contract_factor(app):
    extra = len((H / f"contract_prompt_{app}.txt").read_text()) / 3.5
    return (3000 + extra) / 3000


STAGES = {
    "latency": lambda: 1.10,                                  # FREEZE §10 tier 2, as priced there
    "repeats": lambda: 0.15,
    "V-BASE": lambda: n("diag-home", "diag-desk") * (NEEDLE + LLM2),   # S1 on the anchors: the diagnostics' reference
    "V-REL": lambda: n("relroom-home") * (NEEDLE + LLM2),
    "V-ROOMREQ": lambda: n("relroom-home") * (NEEDLE + LLM2),
    "V-COUNT": lambda: n("diag-home", "diag-desk") * NEEDLE * (1.2 + 1.6 + 2.6),
    "V-RENAME": lambda: n("diag-home", "diag-desk") * (NEEDLE + LLM2),
    "V-DISPATCH": lambda: n("diag-home", "diag-desk") * (NEEDLE + LLM2),
    "V-TIMER": lambda: 2 * n("diag-desk") * (NEEDLE + LLM2),
    "V-VENDOR": lambda: n("diag-home") * (NEEDLE + LLM2),
    "V-TRIGGERS": lambda: n("test-home", "test-desk", "diag-home", "diag-desk") * NEEDLE,
    "V-CONTRACT": lambda: sum(n(f"diag-{a}") * LLM2 * contract_factor(a) for a in ("home", "desk")),
    "V-FORCED": lambda: n("diag-home", "diag-desk") * NEEDLE,
}

if __name__ == "__main__":
    print(f"{STAGES[sys.argv[1]]():.4f}")
