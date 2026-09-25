# Needle 3: contamination canary on non-test material (DESIGN §6.2, §10 step 7)

Run 2026-09-22 by the configuration lead (session 2537465c). Config-side material only; the sealed test's own
canary (P1 crowd phrasing against P2 fresh phrasing, read as a difference in differences across arms) runs at
step 9 and is not here.

What any result here can claim: these checks can find evidence of memorisation of the public request corpora;
a clean result is **weak evidence of cleanliness**, never proof (Needle's 360B-token training set is proprietary,
and MASSIVE's text has been public since 2019).

## 1. Prefix completion (LLM arms only; Needle cannot produce free text)

Method (jev-2's): for 60 MASSIVE train/dev requests of at least 8 words, give the first half and ask for the rest,
under a GENERAL instruction and a GUIDED one that names the MASSIVE/SLURP dataset and asks for its exact text. The
control is 60 fresh paraphrases of the same requests written by a blind agent (no 4-word run shared with the
original). Script `prefix_probe.py`, summary `score_prefix.py` → `prefix_summary.json`; raw `prefix__*.jsonl`.
Serving config: each arm's frontier config (host pinned, temperature 0, reasoning off).

| arm | instruction | verbatim reproductions: originals / paraphrases | mean similarity of the continuation: originals / paraphrases | paired difference [95% CI] |
|---|---|---|---|---|
| deepseek/deepseek-v4-flash-0731 | general | 0/60 / 0/60 | 0.367 / 0.339 | +0.028 [-0.018, +0.073] |
| deepseek/deepseek-v4-flash-0731 | guided | 0/60 / 0/60 | 0.371 / 0.317 | +0.053 [+0.007, +0.101] |
| deepseek/deepseek-v4-flash | general | 0/60 / 0/60 | 0.332 / 0.311 | +0.021 [-0.028, +0.068] |
| deepseek/deepseek-v4-flash | guided | 0/60 / 0/60 | 0.362 / 0.298 | +0.064 [+0.017, +0.112] |

**Reading.** Neither arm reproduced a single public request, under either instruction. Under the GUIDED
instruction the continuations are slightly more similar to the originals than to the paraphrases, with intervals
that exclude zero. That edge is weak evidence, and it is confounded: the paraphrases are written in a different
(written, LLM-style) register, so their second halves are harder to predict whatever the model saw, and the
GENERAL instruction, which carries the same confound, shows about half the difference with an interval including
zero. Nothing here goes on screen as contamination.

## 2. Partition gap (Needle and the LLM arms)

Method: accuracy (exact contract correctness, CONTRACT v1.1 gold) on config items from MASSIVE en-US **train**
against items from MASSIVE en-US **dev**, matched by source intent (per-intent accuracy weighted by the dev-side
count), with a bootstrap interval. Both splits are public, so this can only reveal selective memorisation of one
split. Script `partition_gap.py` → `partition_gap.json`.

| system | train acc | dev acc | gap [95% CI] | items (train / dev) | intents |
|---|---|---|---|---|---|
| needle S1 home | 0.593 | 0.600 | -0.007 [-0.112, +0.096] | 369 / 55 | 18 |
| needle S1 desk | 0.700 | 0.646 | +0.053 [-0.058, +0.171] | 360 / 65 | 9 |
| deepseek-v4-flash-0731 schema (selection only) | 0.854 | 0.800 | +0.054 [-0.052, +0.167] | 182 / 35 | 17 |
| deepseek-v4-flash native (selection only) | 0.787 | 0.743 | +0.044 [-0.086, +0.182] | 182 / 35 | 17 |

**Reading.** No gap resolves: every interval includes zero. Three of the four point estimates lean the same way
(train about 5 points above dev); with 35-65 dev items per system that is inside the noise, and it is recorded rather
than read. The LLM rows use only the selection partition, so their intervals are wide; this is weak evidence either
way.
