# Needle 3: RESULTS (DESIGN §10 step 10, the single scoring)

Scored once, 2026-09-23, by the step 9/10 worker (session 30002c39; Opus 5 for the addendum and tier 1, Opus 5.5
after a session-limit stop). Everything here follows FREEZE.md (accepted at `ea88a7c0`) and FREEZE-ADDENDUM.md
(`de83fb35`, committed and pushed before any sealed input was opened). Scorer `results/score_test.py`, run once
(sha256 `6caed0dc…` after the one field-name fix in §11.1); every number below is copied by script from
`results/SCORES.json` (commit `bbe29cc3`). Draws of examples follow FREEZE §11 (`results/EXAMPLES.json`).
**The salt is not revealed and nothing here is published**; publication is Christo's call after the video.

## 0. Headline

On the sealed test (600 requests: two invented five-tool apps, six strata of 50, 300 families each with a crowd
phrasing P1 and a freshly written P2), under the guide-written tool list S1:

- **Needle 3 as shipped scores 0.545 [0.505, 0.585]** on the statistic of record (exact correctness, macro over the
  twelve app × stratum cells). Always-decline scores 0.500 by construction; Needle's margin over it is +0.045
  [+0.005, +0.085].
- **The screened cheap LLM (llm-a, DeepSeek V4 Flash 0731 on Sail Research) scores 0.775 [0.740, 0.810].** Needle
  minus llm-a is **−0.230 [−0.280, −0.182]**, on both apps, and the family sign test agrees (47 families favour
  Needle, 144 favour llm-a; Holm p 6e-12). This is the one large, clearly resolved result.
- **Against the schema-only keyword baseline K0 (0.555), Needle is unresolved: −0.010 [−0.063, +0.042].** On home
  K0 is ahead (−0.090 [−0.157, −0.023]); on desk the difference is unresolved.
- Against K1 (the example-fed keyword baseline) Needle is +0.057 [+0.003, +0.108]: a difference by the rule of
  record, by a margin of three thousandths at the lower bound, not confirmed by the sign-test cross-check (p 0.088,
  Holm 0.35), and it does not survive against either of the two K1 banks rejected in D8 (§4.3).
- **The guide-written tool list bought Needle nothing:** S1 minus S0 = +0.000 [−0.030, +0.028]. The same change
  bought llm-a 0.040, so the difference in differences is −0.040 [−0.078, −0.003] (a difference by the interval;
  sign test p 0.15, Holm 0.45).
- **What an app would do with Needle's output:** with no gate it executes 235 bundles on test and 118 of them are
  wrong (0.50 [0.44, 0.57]). No confidence threshold on the declared grid comes near the 5% ceiling (at ≥ 0.99:
  82 executed, 34 wrong). Calibration had already frozen no operating point, so the gated app executes nothing and
  forgoes 117 correct calls. On home, 126 of the 179 returned bundles carry confidence ≥ 0.9 and 64 of them are
  right; the confidence barely ranks home mistakes (AUROC 0.55).
- **Band F (the HN requests, 37, reported one by one):** Needle makes a wrong call on 14 of the 37, including
  "My car crashed I need help" → `control_vacuum(stop)`, "Turn the kitchen to 230°C" → kitchen lights on, and
  "I need a wee" → vacuum start; three more are technical failures (§8).

Resolution stated up front (FREEZE §7): about ±4 points for an arm's overall rate, ±6 per app, ±12 per cell;
nothing finer is ranked.

## 1. What ran

| stage | what | dollars (paid API + Modal) |
|---|---|---|
| before step 9 | configuration, preflight, frontier, canary (BUILD-LOG) | 1.271 |
| addendum smoke tests + tier 1 | Needle S0/S1 on test and S1 on band F; both LLM arms likewise; K0, K1, both rejected K1 banks, hassil locally | 0.374 |
| tier 2 | latency (0.245), repeats (0.033) | 0.278 |
| tier 3 | V-BASE, V-REL, V-ROOMREQ, V-COUNT-6/10/20, V-RENAME, V-DISPATCH, V-TIMER-S/U, V-VENDOR, V-TRIGGERS, contract-in-prompt, V-FORCED | 0.636 |
| **total** | observed at the last gate reading (OpenRouter 0.989, Modal 1.570) | **2.559 of 5.00** |

Every stage fired; no gate came near $4.75 (ledger `runs/sealed/spend-ledger.jsonl`). Every Needle output ran on
Intel family 6 model 85 (33 files, none missing; the scorer stops if any item ran elsewhere). Every LLM call was
served by its pinned host on its first pass (46 files, **0 unserved**, so no arm carries the >2% flag). Sealed
inputs: test 600, anchors 128 (home 59, desk 69), band F 37 (home 25, desk 12). Test has no ambiguous item; one
anchor is ambiguous and sits outside its diagnostics.

Before any aggregate was computed, the raw outputs were read end to end (`results/AUDIT-SAMPLE.md`: three items per
arm × schema × outcome cell in display order, every technical failure in every run, every band F item). Every item
read was classified as what it is. Findings from that reading are in §11.

## 2. Statistic of record, every arm

Exact correctness (correct action or correct non-action), macro over the twelve (app × stratum) cells; act mean =
mean over A1-A3, no-act mean = mean over N1-N3 (per app, then averaged); intervals are the stratified,
family-clustered bootstrap of each arm's own rate. Technical failures count as not correct and never as refusals.

| arm | schema | statistic of record [95% CI] | act mean | no-act mean | home | desk | outcomes (ca / cn / wrong / refusal / tech) |
|---|---|---|---|---|---|---|---|
| needle | S1 | **0.545** [0.505, 0.585] | 0.390 | 0.700 | 0.557 | 0.533 | 117 / 210 / 118 / 114 / 41 |
| llm-a | S1 | **0.775** [0.740, 0.810] | 0.920 | 0.630 | 0.793 | 0.757 | 276 / 189 / 130 / 5 / 0 |
| llm-named | S1 | **0.705** [0.665, 0.747] | 0.833 | 0.577 | 0.783 | 0.627 | 250 / 173 / 164 / 13 / 0 |
| K0 | S1 | **0.555** [0.515, 0.595] | 0.563 | 0.547 | 0.647 | 0.463 | 169 / 164 / 216 / 51 / 0 |
| K1 | S1 | **0.488** [0.448, 0.528] | 0.430 | 0.547 | 0.593 | 0.383 | 129 / 164 / 232 / 75 / 0 |
| K1-firstbank | S1 | **0.515** [0.475, 0.555] | 0.410 | 0.620 | 0.577 | 0.453 | 123 / 186 / 205 / 86 / 0 |
| K1-firstbank-none | S1 | **0.522** [0.488, 0.555] | 0.197 | 0.847 | 0.570 | 0.473 | 59 / 254 / 86 / 201 / 0 |
| hassil | S1 | **0.570** [0.543, 0.597] | 0.140 | 1.000 | 0.570 | – | 21 / 150 / 0 / 129 / 0 |
| always-decline | S1 | **0.500** [0.500, 0.500] | 0.000 | 1.000 | 0.500 | 0.500 | 0 / 300 / 0 / 300 / 0 |
| needle | S0 | **0.545** [0.505, 0.587] | 0.417 | 0.673 | 0.587 | 0.503 | 125 / 202 / 118 / 106 / 49 |
| llm-a | S0 | **0.735** [0.697, 0.773] | 0.843 | 0.627 | 0.753 | 0.717 | 253 / 188 / 151 / 8 / 0 |
| llm-named | S0 | **0.702** [0.662, 0.742] | 0.890 | 0.513 | 0.787 | 0.617 | 267 / 154 / 175 / 4 / 0 |
| K0 | S0 | **0.543** [0.503, 0.585] | 0.400 | 0.687 | 0.583 | 0.503 | 120 / 206 / 168 / 106 / 0 |
| K1 | S0 | **0.502** [0.463, 0.540] | 0.327 | 0.677 | 0.580 | 0.423 | 98 / 203 / 172 / 127 / 0 |
| K1-firstbank | S0 | **0.512** [0.472, 0.552] | 0.373 | 0.650 | 0.573 | 0.450 | 112 / 195 / 193 / 100 / 0 |
| K1-firstbank-none | S0 | **0.517** [0.483, 0.550] | 0.183 | 0.850 | 0.570 | 0.463 | 55 / 255 / 82 / 208 / 0 |
| always-decline | S0 | **0.500** [0.500, 0.500] | 0.000 | 1.000 | 0.500 | 0.500 | 0 / 300 / 0 / 300 / 0 |

hassil is home only (Home Assistant's templates have no desk intents) and schema-independent, reported once.

Per cell, correct / n (S1):

| arm (S1) | home/A1 | home/A2 | home/A3 | home/N1 | home/N2 | home/N3 | desk/A1 | desk/A2 | desk/A3 | desk/N1 | desk/N2 | desk/N3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| needle | 37/50 | 29/50 | 19/50 | 23/50 | 43/50 | 16/50 | 16/50 | 8/50 | 8/50 | 44/50 | 45/50 | 39/50 |
| llm-a | 49/50 | 47/50 | 44/50 | 45/50 | 18/50 | 35/50 | 47/50 | 46/50 | 43/50 | 48/50 | 15/50 | 28/50 |
| llm-named | 47/50 | 43/50 | 39/50 | 42/50 | 33/50 | 31/50 | 41/50 | 39/50 | 41/50 | 35/50 | 16/50 | 16/50 |
| K0 | 38/50 | 35/50 | 30/50 | 32/50 | 49/50 | 10/50 | 33/50 | 15/50 | 18/50 | 32/50 | 31/50 | 10/50 |
| K1 | 27/50 | 24/50 | 25/50 | 37/50 | 48/50 | 17/50 | 29/50 | 11/50 | 13/50 | 25/50 | 30/50 | 7/50 |
| K1-firstbank | 28/50 | 24/50 | 17/50 | 41/50 | 48/50 | 15/50 | 27/50 | 14/50 | 13/50 | 30/50 | 36/50 | 16/50 |
| K1-firstbank-none | 12/50 | 11/50 | 11/50 | 47/50 | 50/50 | 40/50 | 10/50 | 9/50 | 6/50 | 42/50 | 41/50 | 34/50 |
| hassil | 15/50 | 3/50 | 3/50 | 50/50 | 50/50 | 50/50 | – | – | – | – | – | – |
| always-decline | 0/50 | 0/50 | 0/50 | 50/50 | 50/50 | 50/50 | 0/50 | 0/50 | 0/50 | 50/50 | 50/50 | 50/50 |
| needle (S0) | 35/50 | 29/50 | 31/50 | 22/50 | 44/50 | 15/50 | 14/50 | 10/50 | 6/50 | 40/50 | 42/50 | 39/50 |

## 3. Needle's outputs, by kind (FREEZE §2, D4)

- **S1** empty results by kind: home {'engine_suppressed': 80, 'validation_flagged': 9, 'model_empty': 8}, desk {'validation_flagged': 177, 'engine_suppressed': 48, 'model_empty': 2}.
  `truncated` beside correct non-actions in the no-act strata: home/N1 4 truncated vs 23 correct non-actions; home/N2 1 truncated vs 43 correct non-actions; home/N3 2 truncated vs 16 correct non-actions; desk/N1 2 truncated vs 44 correct non-actions; desk/N2 4 truncated vs 45 correct non-actions; desk/N3 5 truncated vs 39 correct non-actions.
  Secondary row (validation-flagged calls counted as returned; a reading of the engine output, not an arm): statistic 0.462, act mean 0.540, no-act mean 0.383; outcomes {'correct_action': 162, 'wrong_call': 259, 'correct_nonaction': 115, 'needless_refusal': 23, 'technical_failure': 41}.
- **S0** empty results by kind: home {'engine_suppressed': 80, 'validation_flagged': 8, 'model_empty': 9}, desk {'validation_flagged': 155, 'engine_suppressed': 54, 'model_empty': 2}.
  `truncated` beside correct non-actions in the no-act strata: home/N1 4 truncated vs 22 correct non-actions; home/N2 0 truncated vs 44 correct non-actions; home/N3 3 truncated vs 15 correct non-actions; desk/N1 3 truncated vs 40 correct non-actions; desk/N2 5 truncated vs 42 correct non-actions; desk/N3 5 truncated vs 39 correct non-actions.
  Secondary row (validation-flagged calls counted as returned; a reading of the engine output, not an arm): statistic 0.458, act mean 0.537, no-act mean 0.380; outcomes {'correct_action': 161, 'wrong_call': 245, 'correct_nonaction': 114, 'technical_failure': 49, 'needless_refusal': 31}.

**Every Needle technical failure on test is the engine's `truncated` runtime failure** (41 under S1, 49 under S0;
no timeout, no non-zero exit, no unparseable output). In 22 of the 41 S1 cases (20 of 49 under S0) the engine's own
reasoning line maps "off" to "brightness 0", a value the light-level tool's bounds (1..100) forbid, and decoding runs
out of budget; "Kitchen lights, off." and "Hey, could you switch the light in the study off?" are two of them. Under
D4 these are technical failures, where the vendor harness would count a no-act one as a correct refusal.

Needle's `validation` flags withhold far more on desk than on home (desk: 177 of the 227 empty results under S1 are
validation-flagged calls, home: 9 of 97). The secondary row shows what counting them as returned would do: it lowers
the statistic (0.462 under S1), because the flagged calls are wrong more often than right.

## 4. The five predeclared comparisons (FREEZE §7)

Paired, stratified (app × stratum), family-clustered bootstrap, 10,000 resamples, `default_rng(20260922)` fresh per
quantity, percentile 95% intervals, unadjusted. Cross-check: exact two-sided sign test on families (which arm got
more of the family's two phrasings right; ties dropped); Holm across the five. No LLM item was unserved, so every
comparison uses all 600 items and 300 families.

| # | comparison | difference [95% CI] | home [95% CI] | desk [95% CI] | sign test (families + / − / tie) | p | p Holm | reading by the rule of record |
|---|---|---|---|---|---|---|---|---|
| 1 | needle vs llm-a (S1) | **-0.230** [-0.280, -0.182] | -0.237 [-0.307, -0.170] | -0.223 [-0.293, -0.153] | 47 / 144 / 109 | 1.2e-12 | 6e-12 | difference (interval excludes 0) |
| 2 | needle vs K1 (S1) | **+0.057** [+0.003, +0.108] | -0.037 [-0.110, +0.037] | +0.150 [+0.073, +0.227] | 95 / 72 / 133 | 0.088 | 0.35 | difference (interval excludes 0) |
| 3 | needle vs K0 (S1) | **-0.010** [-0.063, +0.042] | -0.090 [-0.157, -0.023] | +0.070 [-0.010, +0.153] | 78 / 88 / 134 | 0.48 | 0.97 | unresolved |
| 4 | needle S1 minus needle S0 | **+0.000** [-0.030, +0.028] | -0.030 [-0.073, +0.013] | +0.030 [-0.010, +0.073] | 34 / 33 / 233 | 1 | 1 | unresolved |
| 5 | (needle S1-S0) minus (llm-a S1-S0) | **-0.040** [-0.078, -0.003] | -0.070 [-0.123, -0.017] | -0.010 [-0.063, +0.043] | 40 / 55 / 205 | 0.15 | 0.45 | difference (interval excludes 0) |

### 4.1 How to read 2 and 5

Both are differences by the rule of record (the interval excludes zero) and both sit at the edge: the lower bound of
comparison 2 is +0.003 and the upper bound of comparison 5 is −0.003. In both the sign test, a coarser family-level
test, does not reach significance (p 0.088 and 0.15; after Holm 0.35 and 0.45). They are reported as differences,
with the cross-check's disagreement beside them, and are not strong enough to carry a sentence on screen alone.

### 4.2 Reported, not ranked

| comparison | difference [95% CI] | sign test (+ / − / tie, p) | reading |
|---|---|---|---|
| needle vs llm-named (S1) | -0.160 [-0.213, -0.107] | 64 / 127 / 109, p 6e-06 | interval excludes 0 |
| needle vs K1-firstbank (S1) | +0.030 [-0.023, +0.082] | 85 / 72 / 143, p 0.34 | unresolved |
| needle vs K1-firstbank-none (S1) | +0.023 [-0.028, +0.073] | 88 / 76 / 136, p 0.39 | unresolved |
| needle vs always-decline (S1) | +0.045 [+0.005, +0.085] | 79 / 57 / 164, p 0.071 | interval excludes 0 |
| needle vs hassil (S1, home only) | -0.013 [-0.083, +0.057] | 50 / 48 / 52, p 0.92 | unresolved |
| llm-a vs llm-named (S1) | +0.070 [+0.030, +0.110] | – | interval excludes 0 |
| llm-a vs llm-named (S0) | +0.033 [-0.007, +0.073] | – | unresolved |

llm-named is "the model the vendor's claim names, April snapshot as served by OpenInference". It scores 0.705; llm-a
is ahead of it on S1 (+0.070 [+0.030, +0.110]) and unresolved on S0.

### 4.3 D8: the K1 bank choice, on data nobody had seen

The chosen K1 bank scores **0.488**, below both banks D8 rejected (K1-firstbank 0.515, K1-firstbank-none 0.522) and
below always-decline (0.500). Needle's difference against K1 (+0.057) is resolved; against either rejected bank it is
not (+0.030 [−0.023, +0.082]; +0.023 [−0.028, +0.073]). FREEZE §9 asked RESULTS to say so if K1 beat Needle while a
rejected bank did not; the opposite happened: **the one resolved Needle-over-K1 result depends on which bank was
picked, and the bank D8 picked was the weakest on test.** The fair sentence is "Needle does not separate from a
keyword baseline", which K0 already shows.

## 5. The executed scoreboard (FREEZE §5, §6)

What the app would do: a technical failure executes nothing; for Needle the confidence gate defers the whole bundle
below the threshold; every call must validate against the arm's schema (JSON Schema 2020-12, nulls as omitted) or
nothing executes. "Wrong executions" = executed bundles that are not exactly right. Wilson intervals on
wrong / executed.

| arm | schema | policy | app | executed | wrong executions (rate, Wilson 95%) | deferred | blocked by schema validation | correct proposals forgone |
|---|---|---|---|---|---|---|---|---|
| needle | S1 | no gate | home | 179 | 94 (0.525, [0.452, 0.597]) | 0 | 0 | 0 |
| needle | S1 | no gate | desk | 56 | 24 (0.429, [0.308, 0.559]) | 0 | 0 | 0 |
| needle | S1 | no gate | all | 235 | 118 (0.502, [0.439, 0.566]) | 0 | 0 | 0 |
| needle | S1 | frozen operating point (none: defer every bundle) | home | 0 | 0 | 179 | 0 | 85 |
| needle | S1 | frozen operating point (none: defer every bundle) | desk | 0 | 0 | 56 | 0 | 32 |
| needle | S1 | frozen operating point (none: defer every bundle) | all | 0 | 0 | 235 | 0 | 117 |
| needle | S1 | descriptive threshold 0.5 | home | 179 | 94 (0.525, [0.452, 0.597]) | 0 | 0 | 0 |
| needle | S1 | descriptive threshold 0.5 | desk | 55 | 23 (0.418, [0.297, 0.550]) | 1 | 0 | 0 |
| needle | S1 | descriptive threshold 0.5 | all | 234 | 117 (0.500, [0.436, 0.564]) | 1 | 0 | 0 |
| needle | S1 | descriptive threshold 0.9 | home | 126 | 62 (0.492, [0.406, 0.578]) | 53 | 0 | 21 |
| needle | S1 | descriptive threshold 0.9 | desk | 49 | 17 (0.347, [0.229, 0.487]) | 7 | 0 | 0 |
| needle | S1 | descriptive threshold 0.9 | all | 175 | 79 (0.451, [0.380, 0.525]) | 60 | 0 | 21 |
| needle | S1 | descriptive threshold 0.99 | home | 54 | 27 (0.500, [0.371, 0.629]) | 125 | 0 | 58 |
| needle | S1 | descriptive threshold 0.99 | desk | 28 | 7 (0.250, [0.127, 0.434]) | 28 | 0 | 11 |
| needle | S1 | descriptive threshold 0.99 | all | 82 | 34 (0.415, [0.314, 0.523]) | 153 | 0 | 69 |
| needle | S0 | no gate | home | 181 | 86 (0.475, [0.404, 0.548]) | 0 | 0 | 0 |
| needle | S0 | no gate | desk | 62 | 32 (0.516, [0.394, 0.636]) | 0 | 0 | 0 |
| needle | S0 | no gate | all | 243 | 118 (0.486, [0.423, 0.548]) | 0 | 0 | 0 |
| needle | S0 | frozen operating point (none: defer every bundle) | home | 0 | 0 | 181 | 0 | 95 |
| needle | S0 | frozen operating point (none: defer every bundle) | desk | 0 | 0 | 62 | 0 | 30 |
| needle | S0 | frozen operating point (none: defer every bundle) | all | 0 | 0 | 243 | 0 | 125 |
| needle | S0 | descriptive threshold 0.5 | home | 178 | 84 (0.472, [0.400, 0.545]) | 3 | 0 | 1 |
| needle | S0 | descriptive threshold 0.5 | desk | 60 | 30 (0.500, [0.377, 0.623]) | 2 | 0 | 0 |
| needle | S0 | descriptive threshold 0.5 | all | 238 | 114 (0.479, [0.416, 0.542]) | 5 | 0 | 1 |
| needle | S0 | descriptive threshold 0.9 | home | 140 | 63 (0.450, [0.370, 0.533]) | 41 | 0 | 18 |
| needle | S0 | descriptive threshold 0.9 | desk | 41 | 16 (0.390, [0.257, 0.543]) | 21 | 0 | 5 |
| needle | S0 | descriptive threshold 0.9 | all | 181 | 79 (0.436, [0.366, 0.509]) | 62 | 0 | 23 |
| needle | S0 | descriptive threshold 0.99 | home | 100 | 42 (0.420, [0.328, 0.518]) | 81 | 0 | 37 |
| needle | S0 | descriptive threshold 0.99 | desk | 12 | 7 (0.583, [0.320, 0.807]) | 50 | 0 | 25 |
| needle | S0 | descriptive threshold 0.99 | all | 112 | 49 (0.438, [0.349, 0.530]) | 131 | 0 | 62 |
| llm-a | S1 | no gate (no native confidence) | home | 201 | 61 (0.303, [0.244, 0.370]) | 0 | 0 | 0 |
| llm-a | S1 | no gate (no native confidence) | desk | 205 | 69 (0.337, [0.275, 0.404]) | 0 | 0 | 0 |
| llm-a | S1 | no gate (no native confidence) | all | 406 | 130 (0.320, [0.277, 0.367]) | 0 | 0 | 0 |
| llm-named | S1 | no gate (no native confidence) | home | 184 | 55 (0.299, [0.237, 0.369]) | 0 | 0 | 0 |
| llm-named | S1 | no gate (no native confidence) | desk | 228 | 107 (0.469, [0.406, 0.534]) | 0 | 2 | 0 |
| llm-named | S1 | no gate (no native confidence) | all | 412 | 162 (0.393, [0.347, 0.441]) | 0 | 2 | 0 |
| K0 | S1 | no gate (no native confidence) | home | 181 | 78 (0.431, [0.361, 0.504]) | 0 | 0 | 0 |
| K0 | S1 | no gate (no native confidence) | desk | 204 | 138 (0.676, [0.610, 0.737]) | 0 | 0 | 0 |
| K0 | S1 | no gate (no native confidence) | all | 385 | 216 (0.561, [0.511, 0.610]) | 0 | 0 | 0 |
| K1 | S1 | no gate (no native confidence) | home | 140 | 64 (0.457, [0.377, 0.540]) | 0 | 0 | 0 |
| K1 | S1 | no gate (no native confidence) | desk | 221 | 168 (0.760, [0.700, 0.812]) | 0 | 0 | 0 |
| K1 | S1 | no gate (no native confidence) | all | 361 | 232 (0.643, [0.592, 0.690]) | 0 | 0 | 0 |
| hassil | S1 | no gate (no native confidence) | home | 14 | 0 (0.000, [0.000, 0.215]) | 0 | 7 | 0 |
| hassil | S1 | no gate (no native confidence) | desk | 0 | 0 | 0 | 0 | 0 |
| hassil | S1 | no gate (no native confidence) | all | 14 | 0 (0.000, [0.000, 0.215]) | 0 | 7 | 0 |
| llm-a | S0 | no gate (no native confidence) | home | 196 | 71 (0.362, [0.298, 0.432]) | 0 | 0 | 0 |
| llm-a | S0 | no gate (no native confidence) | desk | 208 | 80 (0.385, [0.321, 0.452]) | 0 | 0 | 0 |
| llm-a | S0 | no gate (no native confidence) | all | 404 | 151 (0.374, [0.328, 0.422]) | 0 | 0 | 0 |
| llm-named | S0 | no gate (no native confidence) | home | 207 | 62 (0.300, [0.241, 0.365]) | 0 | 0 | 0 |
| llm-named | S0 | no gate (no native confidence) | desk | 235 | 113 (0.481, [0.418, 0.545]) | 0 | 0 | 0 |
| llm-named | S0 | no gate (no native confidence) | all | 442 | 175 (0.396, [0.351, 0.442]) | 0 | 0 | 0 |

- **Needle, no gate:** 235 executed, 118 wrong (0.502 [0.439, 0.566]); on home 94 of 179.
- **The frozen operating point is "none"** (calibration found no threshold meeting 5% with ≥ 20 accepted), so the
  gated app executes nothing: 235 bundles deferred, among them 117 correct calls forgone.
- **The declared grid** (0.5, 0.9, 0.99) is descriptive, fixed before test. No row approaches 5%: at 0.99 the app
  still executes 82 bundles and 34 are wrong. On test, the lowest observed risk with ≥ 20 accepted is 0.44 on S1
  home (threshold 0.9976, 32 accepted) and 0.19 on S1 desk (0.9841, 37 accepted); these are read off test, so they
  are a description, never a choice.
- The LLM arms have no native confidence and run without a gate: llm-a executes 406 bundles with 130 wrong (0.32),
  llm-named 412 with 162 wrong (0.39). Schema validation blocked 2 llm-named bundles under S1; no other LLM or
  keyword row lost a bundle to it.
- **hassil's executed row is understated by our harness, not by hassil** (finding §11.3): 7 of its 21 returned
  bundles carry the canonical room value `here`, which the S1 enum spells `this room`, so the validator blocks them.
  Its proposal row is unaffected.

## 6. Confidence on test (FREEZE §6.4)

Whole-bundle correctness of returned bundles, ten fixed equal-width bins, empty bins omitted, no `None` confidence
occurred among returned bundles.

| schema / app | bin | bundles | whole-bundle correct | fraction [Wilson 95%] |
|---|---|---|---|---|
| S1 home | 0.5–0.6 | 12 | 2 | 0.17 [0.047, 0.448] |
| S1 home | 0.6–0.7 | 11 | 5 | 0.45 [0.213, 0.720] |
| S1 home | 0.7–0.8 | 12 | 3 | 0.25 [0.089, 0.532] |
| S1 home | 0.8–0.9 | 18 | 11 | 0.61 [0.386, 0.797] |
| S1 home | 0.9–1.0 | 126 | 64 | 0.51 [0.422, 0.594] |
| S1 desk | 0.2–0.3 | 1 | 0 | 0.00 [0.000, 0.793] |
| S1 desk | 0.5–0.6 | 2 | 0 | 0.00 [0.000, 0.658] |
| S1 desk | 0.7–0.8 | 1 | 0 | 0.00 [0.000, 0.793] |
| S1 desk | 0.8–0.9 | 3 | 0 | 0.00 [0.000, 0.562] |
| S1 desk | 0.9–1.0 | 49 | 32 | 0.65 [0.513, 0.771] |
| S0 home | 0.4–0.5 | 3 | 1 | 0.33 [0.061, 0.792] |
| S0 home | 0.5–0.6 | 7 | 2 | 0.29 [0.082, 0.641] |
| S0 home | 0.6–0.7 | 10 | 2 | 0.20 [0.057, 0.510] |
| S0 home | 0.7–0.8 | 6 | 2 | 0.33 [0.097, 0.700] |
| S0 home | 0.8–0.9 | 15 | 11 | 0.73 [0.480, 0.891] |
| S0 home | 0.9–1.0 | 140 | 77 | 0.55 [0.467, 0.630] |
| S0 desk | 0.3–0.4 | 1 | 0 | 0.00 [0.000, 0.793] |
| S0 desk | 0.4–0.5 | 1 | 0 | 0.00 [0.000, 0.793] |
| S0 desk | 0.5–0.6 | 10 | 2 | 0.20 [0.057, 0.510] |
| S0 desk | 0.6–0.7 | 6 | 2 | 0.33 [0.097, 0.700] |
| S0 desk | 0.7–0.8 | 1 | 0 | 0.00 [0.000, 0.793] |
| S0 desk | 0.8–0.9 | 2 | 1 | 0.50 [0.095, 0.905] |
| S0 desk | 0.9–1.0 | 41 | 25 | 0.61 [0.457, 0.743] |

- S1 home: AUROC 0.550 over 179 returned bundles (85 correct, 94 wrong)
- S1 desk: AUROC 0.810 over 56 returned bundles (32 correct, 24 wrong)
- S0 home: AUROC 0.586 over 181 returned bundles (95 correct, 86 wrong)
- S0 desk: AUROC 0.669 over 62 returned bundles (30 correct, 32 wrong)

The three claims kept apart: the scores are not numerically reliable (the 0.9-1.0 bin holds 126 home bundles and
51% of them are right); they barely rank home mistakes (AUROC 0.55) and rank desk ones better (0.81, over only 56
bundles); and a gated app could not be configured to meet the ceiling on calibration, which the test does not
contradict.

## 7. Contamination canary on test (FREEZE §7)

Accuracy on crowd phrasings (P1) minus fresh phrasings (P2), paired within family, bootstrapped by family within
cells; the signal is the gap minus K0's gap (K0's triggers were written from the schema alone).

| arm (S1) | families | acc P1 (crowd) | acc P2 (fresh) | gap P1 − P2 [95% CI] | gap minus K0's gap [95% CI] |
|---|---|---|---|---|---|
| needle | 300 | 0.547 | 0.543 | +0.003 [-0.047, +0.053] | -0.040 [-0.113, +0.030] |
| llm-a | 300 | 0.763 | 0.787 | -0.023 [-0.060, +0.013] | -0.067 [-0.133, +0.000] |
| llm-named | 300 | 0.723 | 0.687 | +0.037 [-0.007, +0.083] | -0.007 [-0.077, +0.063] |
| K1 | 300 | 0.517 | 0.460 | +0.057 [-0.007, +0.117] | +0.013 [-0.053, +0.080] |
| K0 | 300 | 0.577 | 0.533 | +0.043 [-0.013, +0.100] | +0.000 [+0.000, +0.000] |
| hassil | 150 | 0.573 | 0.567 | +0.007 [-0.047, +0.060] | -0.007 [-0.087, +0.073] |

No arm shows a gap over K0's that excludes zero. llm-a's upper bound sits at 0.000, and its gap goes the other way
(it does slightly better on the fresh phrasings). A clean canary is weak evidence of cleanliness and is reported as
that.

## 8. Band F, the HN requests (FREEZE §8)

S1, scored against the custodian's band F gold under CONTRACT v1.1, one row per request; never pooled, no interval,
no rate. ✓act = correct call, ✓none = correct non-action, ✗call = a call where none belongs or a wrong call,
✗refuse = nothing where a call belongs, tech = technical failure. hassil is home only.

| id | app | request | gold | needle | llm-a | llm-named | K0 | K1 | K1-firstbank | K1-firstbank-none | hassil |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n3-1af6aade53 | desk | 25 minute timer | nothing | tech | ✗call | ✗call | ✓none | ✓none | ✓none | ✓none |  |
| n3-1910385144 | desk | Check mail | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-6fac117b49 | desk | add five minutes to the pasta timer | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-5c44b2a544 | desk | check email | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-09411648f4 | desk | open email | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-ea5a0e3d75 | desk | open mail | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-d4a4f84176 | desk | play some jazz | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-c7e934f36d | desk | remind me in 20 minutes | nothing | tech | ✗call | ✗call | ✓none | ✓none | ✓none | ✓none |  |
| n3-c72732acc2 | desk | take off the last one | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |  |
| n3-ec32c4592e | desk | take the paper towels off the list | nothing | ✓none | ✗call | ✗call | ✓none | ✓none | ✓none | ✓none |  |
| n3-2d00bd79bc | desk | twelve minutes | nothing | ✓none | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none |  |
| n3-614dc22c19 | desk | wake me up at 6 30 | nothing | ✓none | ✗call | ✗call | ✗call | ✗call | ✗call | ✓none |  |
| n3-bab4a8336c | home | Harden perimeter | nothing | ✓none | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-b4311aec4a | home | I need a wee | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-667864d577 | home | I need a wee wee | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-d7131cc7a3 | home | I'm going to the toilet | nothing | ✗call | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-396ad3ca0a | home | I'm going to the toilet and can't see | light_power(room=here, state=on) | ✗call | ✗call | ✗call | ✗refuse | ✗refuse | ✗refuse | ✗refuse | ✗refuse |
| n3-44447edfdf | home | I'm going to the toilet and can't see where I'm going | light_power(room=here, state=on) | ✗call | ✗call | ✗call | ✗refuse | ✗refuse | ✗refuse | ✗refuse | ✗refuse |
| n3-a8631b78d7 | home | I'm going to the toilet and can't see where I'm going because it is too dark | light_power(room=here, state=on) | ✗refuse | ✗call | ✗call | ✗refuse | ✗refuse | ✗refuse | ✗refuse | ✗refuse |
| n3-d869f681b8 | home | My car crashed I need help | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-b8353afad0 | home | The cat puked near the refrigerator | nothing | ✓none | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-bb29d43ca3 | home | Turn the kitchen to 230°C | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-829f327edd | home | both doors should be locked | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-3fa15dc4e5 | home | burn us all alive | nothing | tech | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-bcf6bf795b | home | close the garage door and turn the car on | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-ba9b1b709b | home | if blinds are open, open back door | nothing | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-0322c1a57b | home | it's cold | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-1a55c6a523 | home | it's too cold | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-a2a17023ee | home | it's too dark in the bathroom | light_power(room=bathroom, state=on) | ✗refuse | ✓act | ✓act | ✗refuse | ✗refuse | ✗refuse | ✗refuse | ✗refuse |
| n3-d3c0a30757 | home | less light | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-867fb797ba | home | make it hot | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-b968d302ee | home | more light | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-36651e0dbc | home | sleepy time | nothing | ✗call | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-794737cb00 | home | turn all the lights off | light_power(room=whole house, state=off) | ✗call | ✓act | ✓act | ✓act | ✓act | ✓act | ✗refuse | ✓act |
| n3-040bbb5403 | home | turn all the lights on | light_power(room=whole house, state=on) | ✗call | ✓act | ✓act | ✓act | ✓act | ✓act | ✗refuse | ✗refuse |
| n3-9e8085d62c | home | turn it up | nothing | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none | ✓none |
| n3-705663fe0f | home | warm the house | nothing | ✗call | ✓none | ✓none | ✗call | ✓none | ✓none | ✓none | ✓none |
| **counts** | | | | ✓none 18, ✗refuse 2, tech 3, ✗call 14 | ✓act 3, ✓none 27, ✗call 7 | ✓act 3, ✓none 22, ✗call 12 | ✓act 2, ✓none 29, ✗refuse 4, ✗call 2 | ✓act 2, ✓none 30, ✗refuse 4, ✗call 1 | ✓act 2, ✓none 30, ✗refuse 4, ✗call 1 | ✓none 31, ✗refuse 6 | ✓act 1, ✓none 19, ✗refuse 5 |

Answering the one question band F asks (does it still fail on these when the schema is held fixed?): yes. Needle
makes a wrong call on 14 of the 37 (and three are technical failures), among them the thread's own
examples ("My car crashed I need help" → vacuum stop, "Turn the kitchen to 230°C" → kitchen lights on). The LLM arms
fail differently: they turn "25 minute timer" and "remind me in 20 minutes" into alarms and reminders the contract
rules out, and put "can't see" requests in the bathroom (see §11.2 for that gold).

## 9. Diagnostics (FREEZE §8; not in the headline)

One thing varied at a time against S1 on the same items (V-BASE, the S1 run on the anchors, is the reference).
V-REL and V-ROOMREQ run on every home item of test and the anchors whose key carries that variant's gold (359); the
count and timer variants on the anchors whose key carries them; rename, dispatch, triggers, forced and
contract-in-prompt on all 127 unambiguous anchors with main gold. Counts, not rates: these are small and not
resolved statistically.

| diagnostic | arm | items | correct under the variant | same items under S1 (main gold) | right only under variant / only under S1 | technical failures |
|---|---|---|---|---|---|---|
| V-REL | needle | 359 | 125 | 194/359 | 16 / 85 | 56 |
| V-REL | llm-a | 359 | 302 | 285/359 | 36 / 19 | 0 |
| V-REL | llm-named | 359 | 293 | 281/359 | 40 / 28 | 0 |
| V-ROOMREQ | needle | 359 | 253 | 194/359 | 66 / 7 | 17 |
| V-ROOMREQ | llm-a | 359 | 247 | 285/359 | 22 / 60 | 0 |
| V-ROOMREQ | llm-named | 359 | 279 | 281/359 | 28 / 30 | 0 |
| V-COUNT-6 | needle | 127 | 56 | 60/127 | 3 / 7 | 10 |
| V-COUNT-10 | needle | 127 | 48 | 60/127 | 3 / 15 | 17 |
| V-COUNT-20 | needle | 127 | 54 | 60/127 | 10 / 16 | 20 |
| V-RENAME | needle | 127 | 59 | 60/127 | 10 / 11 | 4 |
| V-RENAME | llm-a | 127 | 89 | 95/127 | 0 / 6 | 1 |
| V-RENAME | llm-named | 127 | 84 | 81/127 | 6 / 3 | 0 |
| V-DISPATCH | needle | 127 | 41 | 60/127 | 7 / 26 | 6 |
| V-DISPATCH | llm-a | 127 | 91 | 95/127 | 3 / 7 | 0 |
| V-DISPATCH | llm-named | 127 | 75 | 81/127 | 7 / 13 | 0 |
| V-TIMER-S | needle | 68 | 35 | 33/68 | 5 / 3 | 1 |
| V-TIMER-S | llm-a | 68 | 49 | 48/68 | 1 / 0 | 0 |
| V-TIMER-S | llm-named | 68 | 38 | 35/68 | 9 / 6 | 0 |
| V-TIMER-U | needle | 68 | 36 | 33/68 | 8 / 5 | 3 |
| V-TIMER-U | llm-a | 68 | 49 | 48/68 | 1 / 0 | 0 |
| V-TIMER-U | llm-named | 68 | 37 | 35/68 | 10 / 8 | 0 |
| V-VENDOR | needle | 59 | 45 | – (different gold) | – | 0 |
| V-VENDOR | llm-a | 59 | 39 | – (different gold) | – | 0 |
| V-VENDOR | llm-named | 59 | 48 | – (different gold) | – | 0 |
| V-TRIGGERS (anchors) | needle | 127 | 57 | 60/127 | 3 / 6 | 6 |
| V-CONTRACT-IN-PROMPT | llm-a | 127 | 110 | 95/127 | 22 / 7 | 0 |
| V-CONTRACT-IN-PROMPT | llm-named | 127 | 96 | 81/127 | 27 / 12 | 0 |
| V-FORCED | needle | 127 | 52 | 60/127 | 2 / 10 | 7 |
| S1 on the anchors (reference) | needle | 127 | 60 | – | – | 7 |
| S1 on the anchors (reference) | llm-a | 127 | 95 | – | – | 0 |
| S1 on the anchors (reference) | llm-named | 127 | 81 | – | – | 0 |

What each one shows, in counts:
- **V-REL** (a relative light tool in place of the plug): Needle falls from 194 to 125 of 359, 56 of them
  `truncated`; the LLM arms gain (llm-a 285 → 302).
- **V-ROOMREQ** (room required, no default): Needle rises from 194 to 253, because it stops being charged for
  inventing rooms on roomless requests; llm-a falls (285 → 247).
- **V-COUNT** (6, 10, 20 tools): Needle 60 at five tools, 56, 48 and 54 with distractors; technical failures grow
  (10, 17, 20). No retrieval was observed above five tools (D3), so this reads as "all tools in the prefix".
- **V-RENAME** (tool names absent from Needle 1/2's training list): 59 against 60; the familiar names were not what
  Needle was relying on.
- **V-DISPATCH** (one dispatcher tool): Needle 41 against 60, home 9 of 59.
- **V-TIMER-S / V-TIMER-U** (seconds vs amount + unit): Needle 35 and 36 of 68 against 33 under S1.
- **V-VENDOR** (the vendor's own smart_home tools and, for Needle, its own system text; the LLM arms get their frozen
  system paragraph, an asymmetry declared in the addendum): Needle 45 of 59, llm-a 39, llm-named 48. Gold is
  written for that environment, so there is no S1 reference on the same gold.
- **V-TRIGGERS** (K0's blind phrases as Needle triggers): on the anchors 57 against 60; on the whole test
  0.495 (act 0.443, no-act 0.547; outcomes {'correct_action': 133, 'correct_nonaction': 164, 'wrong_call': 180, 'needless_refusal': 94, 'technical_failure': 29}), against needle S1 0.545: difference -0.050 [-0.082, -0.020]. Triggers make Needle call more and be right less.
- **Contract in the prompt** (LLM only): llm-a 95 → 110 of 127, llm-named 81 → 96. Information parity cost the LLM
  arms about 15 anchors each; with the contract text they would be further ahead.
- **V-FORCED**: Needle 52 against 60.

## 10. Repeats and latency (FREEZE §8)

Repeats: 30 test items per app (drawn by item, the stated deviation), S1, run twice more.

| arm / app | items | identical output all three runs | largest confidence move |
|---|---|---|---|
| needle/home | 30 | 30 | 0.0 |
| llm-a/home | 30 | 27 | – |
| llm-named/home | 30 | 23 | – |
| needle/desk | 30 | 30 | 0.0 |
| llm-a/desk | 30 | 27 | – |
| llm-named/desk | 30 | 21 | – |

Needle is deterministic on the pinned class (identical calls and identical confidence). The LLM arms at temperature 0
are not: llm-a changed its output on 6 of 60 items, llm-named on 16.

Latency, separate from the scored passes. Rented Modal CPU, hard `cpu=(n, n)`, Intel model 85, 20 warm-up requests
discarded, the app's 300 S1 test items serially, timed to a parsed, schema-validated decision; the LLM client ran in
one Modal container in us-east, serially, one arm at a time, on 200 items.

| system | app | cores | call-producing p50 / p95 / max (s) | refusing p50 / p95 / max (s) | other |
|---|---|---|---|---|---|
| needle | home | 1 | 8.097 / 8.736 / 9.205 (n 179) | 8.088 / 8.575 / 9.816 (n 97) | prefill p50 72 tok/s, decode p50 89 tok/s, peak RAM max 101 MB; 24 technical failures timed apart |
| K0 | home | 1 | 3.11 / 5.62 / 9.79 ms (n 181) | 3.02 / 4.23 / 4.30 ms (n 119) |  |
| K1 | home | 1 | 3.10 / 6.02 / 7.31 ms (n 140) | 3.10 / 4.23 / 6.20 ms (n 160) |  |
| hassil | home | 1 | 4.75 / 5.83 / 6.35 ms (n 21) | 2.98 / 5.31 / 59.82 ms (n 279) | grammar load 101.3 s |
| needle | home | 4 | 2.589 / 2.863 / 3.219 (n 179) | 2.584 / 2.809 / 3.472 (n 97) | prefill p50 232 tok/s, decode p50 206 tok/s, peak RAM max 107 MB; 24 technical failures timed apart |
| K0 | home | 4 | 3.03 / 4.89 / 7.17 ms (n 181) | 2.99 / 4.12 / 4.25 ms (n 119) |  |
| K1 | home | 4 | 3.02 / 5.83 / 7.12 ms (n 140) | 3.03 / 4.12 / 6.05 ms (n 160) |  |
| hassil | home | 4 | 4.87 / 6.10 / 6.41 ms (n 21) | 3.12 / 5.50 / 52.03 ms (n 279) | grammar load 3.6 s |
| needle, cold start (first request in a fresh container) | home | 1 | 8.199 / 9.334 / 9.424 (n 10) | | |
| needle | desk | 1 | 7.987 / 8.833 / 8.982 (n 56) | 7.892 / 8.659 / 9.425 (n 227) | prefill p50 75 tok/s, decode p50 94 tok/s, peak RAM max 102 MB; 17 technical failures timed apart |
| K0 | desk | 1 | 0.70 / 2.26 / 2.42 ms (n 204) | 0.49 / 1.22 / 2.18 ms (n 96) |  |
| K1 | desk | 1 | 0.71 / 1.47 / 2.41 ms (n 221) | 0.41 / 1.23 / 1.50 ms (n 79) |  |
| needle | desk | 4 | 2.808 / 3.445 / 4.679 (n 56) | 2.755 / 3.132 / 4.958 (n 227) | prefill p50 240 tok/s, decode p50 192 tok/s, peak RAM max 102 MB; 17 technical failures timed apart |
| K0 | desk | 4 | 0.66 / 2.08 / 2.34 ms (n 204) | 0.45 / 1.22 / 2.13 ms (n 96) |  |
| K1 | desk | 4 | 0.68 / 1.42 / 2.37 ms (n 221) | 0.40 / 1.17 / 1.40 ms (n 79) |  |
| needle, cold start (first request in a fresh container) | desk | 1 | 8.168 / 8.954 / 9.197 (n 10) | | |
| llm-a (Modal us-east, serial) | both | – | 1.221 / 2.037 / 2.686 (n 130) | 0.759 / 1.613 / 1.969 (n 70) | time to first token 0.734 / 1.582; network floor p50 0.450 s before, 0.405 s after; served 200/200 |
| llm-named (Modal us-east, serial) | both | – | 3.630 / 5.912 / 8.999 (n 132) | 2.912 / 5.373 / 6.620 (n 68) | time to first token 0.891 / 1.506; network floor p50 0.878 s before, 0.848 s after; served 200/200 |

On one rented core a Needle decision takes about 8 s (fresh process per request, the tool prefix re-prefilled each
time), about 2.6-2.8 s on four; the keyword arms take milliseconds; llm-a takes about 1.2 s over the network. These
are server numbers; they say nothing about a phone, a Pi or energy (DESIGN §11). At one core the container reported
`ncpu 2` (Modal counts a physical core as two vCPUs); the hard limit held Needle to `--threads 1`.

## 11. Findings from the reading and the audit (nothing was changed or retuned)

1. **Key adapter field-name fix** (FREEZE-ADDENDUM §2.12): the sealed keys hold gold as `{"main": …, "V-REL": …}`;
   `score_test.py` was fixed to read `gold["main"]` before it first ran (commit `0f60ffac`). No rule changed; the
   variant golds were already read by the adapter.
2. **A strict contract reading on band F.** Three requests about going to the toilet and not being able to see
   have gold `light_power(here, on)`: CONTRACT R6 declares "can't see" → `light_power(on)`, and an omitted room is
   the default `here`. Both LLM arms answer `bathroom` and score as wrong calls. Whether "going to the toilet" names
   the room to light is the annotators' judgment under the contract, not a scorer error; it touches band F only
   (never pooled) and is listed so a viewer can weigh it.
3. **hassil's executed row** (§5): our renaming of hassil's canonical output into S1 names renames keys, not values,
   so `room: here` reaches the validator un-renamed. This is our harness, found after unblinding, left as scored and
   reported; hassil's proposal row, which is what the design compares, is unaffected.
4. **The one LLM technical failure** (llm-a, V-RENAME desk): the reply repeats `wake_bell_add` / `wake_bell_drop`
   until the 600-token cap and the JSON never closes. Classified as a technical failure, correctly.
5. **K1's bank** (§4.3): the bank D8 chose was the weakest of the three on test.
6. **Comparisons 2 and 5** are resolved by the interval rule at a margin of three thousandths and not by the
   sign-test cross-check (§4.1).
7. **Latency containers at one core report two vCPUs** (§10); the scored passes are unaffected.
8. FREEZE itself was not changed; nothing in the run tempted a change to it.

## 12. What this cannot settle

Everything in DESIGN §11 stands: one untuned model as shipped, two invented five-tool apps, English text, single
turns; a balanced test is not real traffic; the hosted LLMs are one host on one day; server CPU latency only. The
depth curve was dropped at preflight (D1). The vendor's tuned-deployment claim is neither confirmed nor refuted.

## Files

`runs/sealed/out/` (every raw output, failures included), `runs/sealed/logs/`, `runs/sealed/spend-ledger.jsonl`,
`results/SCORES.json`, `results/EXAMPLES.json`, `results/AUDIT-SAMPLE.md`, `results/score_test.stdout.txt`.
`runs/sealed/inputs/` (the request files split by app) stays out of git with the rest of the sealed material until
publication.
