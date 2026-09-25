# Needle 3: FREEZE (DESIGN §10 step 8)

**Accepted by m37-lead, 2026-09-22 18:0x.** Review: raw calibration calls read against gold and re-scored with the frozen scorer; the scorer applies defaults correctly (an omitted room scores as the whole house), and the wrong calls are genuine (invented rooms; acting on negations and on bare "turn off"). Accepted with its stated deviation (repeats drawn by item). §12's addendum must still be committed and hashed before any sealed input is opened.

Drafted 2026-09-22 by a worker for m37-lead (session f22be2f5, Opus 5), before any sealed item was read,
sent or scored. This file fixes everything the sealed run (step 9) and the single scoring (step 10) use.
The commit that adds it must precede every file under `runs/sealed/` and `results/`; `git log` is the
check. Every decision below was made on config-side material only (dev, selection, calibration, lexical
bank: `partitions/gold.jsonl`). Config-side numbers appear here only as the basis of a decision, never as
results.

If anything in the sealed run tempts a change to what is written here, the change is not made. It is
recorded as a finding in `RESULTS.md`. A scorer or gold bug found after unblinding is corrected in a new
version, and both numbers are published (DESIGN §3.6).

## 1. The sealed inputs (named, not read)

Commitment **v2** `f73c32e4807e793ab0be3bd1a943a01f4f9239a79fae1094ac9dda0e7ced55fe` (179 files, sealed
2026-09-22 15:23 CEST, labelled under CONTRACT v1.1; `custodian/COMMITMENT.md`, custodian log). v1
(`96d2bc70…`) is superseded and not used. Paths, from the custodian's hand-over (this worker did not open
them):

| role | path | read when |
|---|---|---|
| runner input, test (600 items: 2 apps × 6 strata × 25 families × P1/P2) | `~/temp/m37-needle3-sealed/sealed-v2/test-requests.jsonl` | step 9, after this file is accepted |
| runner input, diagnostic anchors | `~/temp/m37-needle3-sealed/sealed-v2/diagnostics-requests.jsonl` | step 9 |
| runner input, band F (HN requests) | `~/temp/m37-needle3-sealed/sealed-v2/bandF-requests.jsonl` | step 9 |
| gold keys (CONTRACT v1.1, canonical form; home keys carry V-ROOMREQ and V-REL; anchors carry V-VENDOR, V-TIMER, V-COUNT) | `~/temp/m37-needle3-sealed/sealed-v2/*-key.jsonl` | step 10 only, after every arm has finished |
| salt | `~/temp/m37-needle3-salt/salt-v2.hex` | publication |

Request files carry `id, app, text` only. The runner reads nothing else. Nothing from the key files is
read until step 10.

## 2. Needle 3, the subject

| pin | value | source |
|---|---|---|
| HF revision | `Cactus-Compute/needle3` `b274efcb211a9eef48c9a88da4b43bd569696a39` | `snapshot/MANIFEST.md` |
| weights | `needle3.cact` sha256 `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38`, 35,335,380 bytes | same |
| native runner | `linux-x86_64/needle` sha256 `5eb163c5ed33bd914c103ef8eba2134c7bb2d97bafafdd69f410a4a3100e8c37` (no version string exists; pinned by hash) | same |
| Python package (vendor harness, known-answer control only) | `cactus-needle` git `f189b23e`, reports 3.0.1 | same |
| image and driver | `modal/needle_modal.py` sha256 `992199b5fa2585787b7944b766505bec0f0740d37453920103612f35239a21d1`; Modal app `m37-needle3`; `HF_HUB_OFFLINE=1`, `NEEDLE_TELEMETRY=0`, `DO_NOT_TRACK=1` | |
| **CPU class** | **`require_cpu = "GenuineIntel fam 6 model 85"`** asserted in every container; a chunk that starts on another class is turned away and re-landed; partial results are saved and resumed (D2) | PREFLIGHT item 5 |

**Invocation, one fresh process per request:**
`needle --model needle3.cact --tools <schema>.json [--system "date: 2026-06-10 Wed 14:30; locale: en-US"] --threads 1 --fail-input-overflow --prompt "<request>"`.
The fact line goes to the desk app only; home sends no system turn. **No `--depth`** (D1: the flag has no
effect in this build, so the arm is the runner's default, the full archive; the depth curve is dropped and
nothing replaces it). **No `--forced`** and **no triggers** except in the V-FORCED and V-TRIGGERS
diagnostics. **No `--tool-index`** (D3). Output config for the scored passes: `cfg = {"threads": 1,
"forced": false, "overflow_flag": true, "require_cpu": "GenuineIntel fam 6 model 85", "depth": null}`, the
same config that produced every config-side Needle output (`runs/needle_config/out_*.json`, 2,555
responses, all on that class).

**What the app receives** (primary, both scoreboards): `harness/score.py needle_calls()`: the
`function_calls` of a well-formed envelope, with a bundle the engine's `validation` flags (ungrounded or
negation) withheld, as the vendor harness does. The three kinds of empty (model empty, engine-suppressed,
validation-flagged) are logged apart (`empty_kind`). A response with `success: false` and an error
(including `truncated`, D4, and `context_overflow`), a non-zero exit, unparseable stdout or a timeout is a
**technical failure**, never a refusal.

**Secondary row, declared here, computed from the same stored outputs:** "validation-flagged calls counted
as returned". Why: on the calibration partition the validation flag withholds most desk calls (64 of 108
desk items came back flagged under S1), including correct ones: "i wanna get up at six am" returns
`set_alarm(06:00)` at confidence 0.97, flagged `ungrounded: set_alarm.time` because 06:00 is not a
substring of the request. The same flag also withholds far more wrong calls than right ones (under S1
desk, counting flagged calls as returned turns 2 correct calls into 5 and 1 wrong call into 62), so the
primary reading stands, and the row lets a viewer see what the flag does. It is labelled as a reading of
the engine's output, not as another arm.

## 3. The arms

Every arm runs both full-test schemas, S0 and S1 (DESIGN §5.1), on the 600 test items and band F.

| arm | what | configuration (frozen) | source |
|---|---|---|---|
| **needle** | §2 | §2 | |
| **llm-a** (advanced frontier arm) | `deepseek/deepseek-v4-flash-0731` | OpenRouter, host **Sail Research** (listed quantisation **fp4** in the snapshot's endpoint record), strict JSON-schema contract, `temperature: 0`, `reasoning: {"enabled": false}`, `max_tokens: 600`, `provider: {"order": ["Sail Research"], "allow_fallbacks": false, "require_parameters": true}`, `lite: false` | `FRONTIER.md` (fills both rule slots) |
| **llm-named** (the vendor's named model) | `deepseek/deepseek-v4-flash` (April snapshot) | OpenRouter, host **OpenInference** (fp8), native `tools` + `tool_choice: "auto"`, same sampling, reasoning, token cap and provider settings | `FRONTIER.md` §4.2 step 6 |
| **K0** | schema-only BM25 + rule-based extractor | S1: k=1, μ=1, τ home 1.4599353075027466, desk 1.7199054956436157. S0: k=1, μ=1, τ home 1.8894966840744019, desk 2.103935718536377 | `baselines/DEV-RESULTS.json` |
| **K1** | example-fed BM25 (the D8 bank) + the same extractor | S1: k=1, μ=1, τ home 1.9272738695144653, desk 2.8494081497192383. S0: k=3, μ=1, τ home 2.4260263442993164, desk 3.3841421604156494 | same |
| K1-firstbank, K1-firstbank-none (reported beside K1, never as the arm; see §9, D8) | the two rejected indexings | the tuned values in `DEV-RESULTS.json` under those names | same |
| **hassil** (home only) | Home Assistant's English templates, unmodified | OHF-Voice/intents `f8cdbb0b6601cde140b9a40c297363c6137d219d`, hassil 3.12.1, PyYAML 6.0.3, `baselines/hassil/mapping_table.json`; schema-independent, reported once | `baselines/hassil/PINS.md` |
| **always-decline** | returns nothing | | |

The embedding router is not an arm (dev: +0.051 over K1, interval [-0.009, +0.108]; `BASELINES.md`).

**LLM prompts.** The system turn is one fixed, task-neutral paragraph (information parity, DESIGN §4.2),
plus the desk fact line on desk; the tools are the same S0/S1 files Needle gets.

| component | sha256 |
|---|---|
| schema-contract system paragraph (`llm_arm.SYSTEM_SCHEMA`) | `14fbbd3df420e8ad41d028f3fbde08e0d24f4e05dbf292803d7248ef9220fe28` |
| native-contract system paragraph (`llm_arm.SYSTEM_NATIVE`) | `5e53dc7396f815e555dbd87c503da1a823de551b11c50a093135f8ca0a901433` |
| desk fact line | `14870f8400c3187aba980eba6bbac070e1e945886671b0b9ce778451d4ea99a6` |
| strict response schema, S1-home / S1-desk | `e3c1d57a…5684d` / `f78c7503…4cda` (full: `calibration/HASHES.txt`) |
| strict response schema, S0-home / S0-desk | `c65fb12e…52fa` / `70cc1f61…8da8` |

Every call also records the sha256 of its own request body (`request_sha256`), so any call can be checked
against a rebuild. Under the schema contract, empty content plus native tool calls is read as the answer,
and a null argument is read as omitted (`FRONTIER.md`, harness findings).

**LLM failures.** Up to 4 attempts per call (`llm_arm.py`: backoff on 408/429/5xx). A call that still
fails, or whose output does not parse into calls, is a technical failure. An **unserved** call (HTTP 429
from the host's upstream pool on every attempt) is not the model's failure: unserved items are re-sent in
up to three later passes; any still unserved are excluded and counted apart, and if more than 2% of an
arm's test items end unserved, every number for that arm carries that flag in RESULTS. A call served by
any host other than the pinned one is treated as unserved.

## 4. Contract, schemas, scorer

| file | sha256 |
|---|---|
| `contracts/CONTRACT.md` (v1.1) | `a92db14b35cb725f7d824460a723b6e3583100f74e03ebc3ebd60f0dc4f84675` |
| `contracts/mapping.py` | `c556c728b6589c2e2b9d6746baf6a8e5dab65d9e6aaeae3974a157743f680420` |
| `contracts/S1/home.json`, `S1/desk.json` | `5a7a956d…8d62`, `efc2d5b9…85c8` |
| `contracts/S0/home.json`, `S0/desk.json` | `95213bf6…16ec4cf`, `89ca174a…bc` |
| `contracts/variants/*.json` (14 files) | `calibration/HASHES.txt` |
| **`harness/score.py`** (proposal scoreboard, all arms) | **`0c3a7d6f4702f66ac9d9417e8a19dd21c5f6cc9d549816d4055668ae4b908070`** |
| **`harness/execute.py`** (executed scoreboard, §5; new at this step) | **`67a1fb748fc1da07ef6ad6eb074fd87d92bd845f2fb66fb79c0d4308c1f2b051`** |
| `harness/test_score.py` (mutation tests: 54 + 515 mutants, 0 failures, re-run 2026-09-22 at this freeze) | `38c5da91…2b` |
| `harness/test_execute.py` (10 checks pass; every config S1 Needle bundle and both LLM arms' selection bundles validate) | `0dfc84c3…f6ac` |
| `harness/llm_arm.py` | `a3bfa5ca2a461ff6b504183182c56ca2ff53712c9a0efe7b9f2dd33d2ae7b296` |
| `baselines/bm25_arm.py`, `k0/extractor.py`, `k0/triggers_S{0,1}.json`, `k1_bank/bank.json`, `k1_bank/INTENT-TO-TOOL.json`, `hassil/hassil_arm.py`, `hassil/mapping_table.json`, `DEV-RESULTS.json` | `calibration/HASHES.txt` |

Scoring rule (DESIGN §7.1, as built): exact correctness of the canonical call multiset against any
acceptable gold answer (R7 is the only place with two), order-free, duplicates kept; deterministic
normalisation by `mapping.py` (R5); no LLM judge. Outcomes: correct action, correct non-action, wrong call,
needless refusal, technical failure; `ambiguous` gold leaves the headline and is reported with its count.
Diagnostics (tool match, argument precision and recall) are never absolution. The strata used for
reporting are the custodian's v1.0 frame (m37-lead's ruling at the v2 re-seal).

## 5. The two scoreboards

- **Proposal**: what the arm returned (for Needle, `needle_calls`), scored as above.
- **Executed** (`harness/execute.py`): what the app would do. A technical failure executes nothing and
  stays a technical failure. For Needle, a confidence gate (§6) defers the whole bundle when confidence is
  missing or below the threshold. Then every call must name a tool of the schema the arm was given and
  validate against that tool's `parameters` (JSON Schema 2020-12, formats checked, nulls read as omitted);
  if any call fails, nothing executes (the atomic rule applied by the app). Executed outcomes are scored by
  the same scorer, with deferrals counted separately: "executed n, got k wrong, deferred d".
- LLM arms have no confidence field (DESIGN §7.3): they are shown executed without a gate, which is how a
  builder would deploy them. "No native confidence" is a designed state in the graphics.

## 6. Calibration: Needle's confidence operating point

Rule (DESIGN §7.3, frozen before this step): per app, on the calibration partition only, the lowest
threshold (the most coverage) whose accepted set has at least 20 requests and an observed wrong-execution
rate (wrong executions / executed) of at most 5%. The 5% ceiling is ours, not a safety standard. Depth 20
only (D1). Computed from the existing config-side outputs, no new runs: `calibration/calibrate.py` (sha256
`4b7914d4…c3baa`) → `calibration/CALIBRATION.json` (full risk-coverage curves and reliability bins).
Calibration partition: home 120 items (A 36, N 84), desk 109 (A 18, N 90, 1 ambiguous).

| schema-app | returned a call | of those correct | wrong executions with no gate | lowest observed risk with ≥ 20 accepted | **operating point at 5%** | AUROC (correct vs wrong, among returned) |
|---|---|---|---|---|---|---|
| **S1-home** | 68 / 120 | 17 | 51 (75%) | 33 / 48 = 69% at ≥ 0.902 [Wilson 55%, 80%] | **none** | 0.57 |
| **S1-desk** | 3 / 108 | 2 | 1 | fewer than 20 calls returned | **none** | too few |
| S0-home | 63 / 120 | 21 | 42 (67%) | 14 / 22 = 64% at ≥ 0.9969 [43%, 80%] | **none** | 0.52 |
| S0-desk | 9 / 108 | 0 | 9 | fewer than 20 calls returned | **none** | too few |

**Finding: calibration offers no operating point for Needle at our ceiling, on either app or schema.** As
DESIGN §7.3 says, that is the finding, and the vendor's example threshold is not borrowed. On home, 48 of
the 68 returned bundles carry confidence ≥ 0.9, and 33 of those 48 are wrong. On desk the app receives
almost nothing to gate.

Two sensitivity readings, added after the primary result above was seen and never the rule of record
(both in `CALIBRATION.json` → `sensitivity`): counting validation-flagged calls as returned (lowest risk
with ≥ 20 accepted: S1-home 71%, S1-desk 80%, S0-desk 90%); and re-weighting the calibration strata to
the sealed test's balance of six equal strata (lowest weighted risk: S1-home 43%, S0-home 42%; desk still
under 20 calls). Neither reaches 5%. The finding does not depend on the calibration partition's no-act-heavy
mix.

**What therefore goes on the executed scoreboard for Needle** (on test, S0 and S1, per app):
1. **no gate** (execute every returned bundle; the engine's own 0.1 floor is already applied);
2. **the frozen operating point**: none, so the gated app executes nothing and defers every returned
   bundle. Shown as such, with the count of correct calls it forgoes;
3. a **descriptive grid declared now**, not operating points: thresholds 0.5, 0.9 and 0.99, each shown as
   "executed n, got k wrong, deferred d" with its Wilson interval. These three are fixed here so that no
   threshold is read off the test and presented as a choice;
4. the full risk-coverage curve on test, swept on stored outputs (no reruns), and the reliability diagram
   (ten fixed equal-width bins, counts and Wilson intervals, empty bins empty, whole-bundle correctness,
   no pooling of `None` with low confidence, no "off-topic probability" from an empty result's
   confidence) and the AUROC.

On screen the three claims stay apart (DESIGN §7.3): whether the scores are numerically reliable (the
diagram), whether they rank the mistakes (AUROC), and whether a gated app met the ceiling (it could not be
configured to on calibration). Never "above 0.9 is safe".

## 7. Primary comparisons and uncertainty

**Statistic of record**: exact correctness on the proposal scoreboard, macro-averaged over the twelve
(app × stratum) cells of the sealed test, ambiguous items excluded. Because the test is balanced (25
families per cell), this is close to plain accuracy; it is reported beside the act-side mean (A1-A3) and
the no-act-side mean (N1-N3), per app, and per cell, never alone (DESIGN §7.2). The D6 axis was a
config-side device only (§9) and is not used on the test.

**The five predeclared comparisons** (DESIGN §7.4), all on S1 unless named:
1. needle vs **llm-a**;
2. needle vs **K1**;
3. needle vs **K0**;
4. needle S0 vs needle S1;
5. the S0-to-S1 gain for needle vs the same gain for **llm-a** (a difference in differences).

Everything else (llm-named, hassil, always-decline, the executed scoreboard, band F, diagnostics, the
canary) is reported, not ranked. llm-named is shown beside llm-a and labelled "the model the vendor's claim
names, April snapshot as served by OpenInference".

**Intervals**: paired, stratified, family-clustered bootstrap: 10,000 resamples; within each (app ×
stratum) cell, families are resampled with replacement and both phrasings of a drawn family go together;
percentile 95% intervals; RNG `numpy.random.default_rng(20260922)`. **Cross-check**: an exact two-sided
sign test at the family level (per family, which arm got more of its two phrasings right; ties dropped),
the family-level form of McNemar. Holm-adjusted across the five comparisons; intervals are shown
unadjusted. A difference is described as a difference only when its interval excludes zero; otherwise it
is unresolved, never a winner. Zero observed errors in a cell also get the one-sided 95% binomial bound.
Resolution stated up front: about ±4 points for an arm's overall rate, ±6 per app, ±12 per cell; the
script ranks nothing finer.

**Contamination canary on test** (DESIGN §6.2): per arm, accuracy on P1 (crowd) minus accuracy on P2
(fresh), paired within family, bootstrapped as above; the signal is the difference in differences against
**K0**, whose triggers were written from the schema alone and cannot have memorised the crowd corpora. A
gap goes on screen; a clean result is weak evidence of cleanliness and is reported that way.

## 8. Band F, diagnostics, repeats, latency

**Band F (the HN requests)** is its own scored band: every arm, S1 only, scored against the custodian's
band F gold under CONTRACT v1.1. Reported alone, per request (the whole band is small enough to list),
with counts per outcome and n shown. Never pooled into any other number, never given an interval or a
rate claim (the maker retuned the demo against these requests, so they cannot estimate a rate). They
answer one question: does it still fail on these when the schema is held fixed?

**Diagnostics** (DESIGN §5.2-5.3), on the sealed anchors, one thing varied at a time, proposal scoreboard,
gold from the anchor keys (or main gold where CONTRACT §4 says the variant does not change it). One anchor
is ambiguous under v2 and stays out of its diagnostic's headline. Needle runs all of them; the LLM arms
run the schema-only ones. Priority order
for firing (budget, §10): V-REL, V-ROOMREQ, V-COUNT-6/10/20 (Needle only), V-RENAME, V-DISPATCH,
V-TIMER-S/U, V-VENDOR, V-TRIGGERS (Needle, triggers compiled from `k0/triggers_S1.json`), LLM with the
contract in its prompt (LLM only), V-FORCED (Needle only). The contract-in-prompt system text is written
and hashed in an addendum to this file before it fires, and adds only CONTRACT text.

**Repeats** (DESIGN §8, stability, never calibration): 60 test items, 30 per app, the ones with the
smallest `sha256("needle3-repeat-2026-09-22:" + id)` within each app, run twice more on needle, llm-a and
llm-named under S1. Needle's repeats run in fresh containers on the pinned class. Deviation from the
design, stated: DESIGN says 30 families, but family membership is in the key files, which are not read
before scoring, so the sample is drawn by item. Reported as identical-output rate and confidence movement.

**Latency** (DESIGN §8), separate from the scored passes, never mixed with them:
- needle, K0, K1, hassil: one Modal container per (app × core count) with `cpu=(n, n)` and `--threads n`
  for n = 1 and 4, pinned class, CPU identity recorded, 20 warm-up requests discarded, then the 300 S1 test
  items of that app serially, timed from request to parsed, validated decision; plus the engine's
  `prefill_tps`, `decode_tps`, `peak_ram_mb`; cold start over 10 fresh containers. p50/p95/max, with
  call-producing and refusing requests reported separately. The existing driver requests `cpu=1.0`
  (soft limit, can burst); the latency function must set the hard limit.
- llm-a, llm-named: a client in a Modal container in one fixed region, serial, one arm at a time, on 200
  test items (100 per app, smallest `sha256("needle3-latency-2026-09-22:" + id)`), total time to a
  parsed decision and time to first token; network floor from 50 minimal requests to the same pinned host
  before and after.
- Rented-server CPU numbers only; not device, Pi or energy figures (DESIGN §11).

## 9. Design changes D1-D8 and how each bears on the primary comparisons

- **D1, depth curve dropped** (preflight, before any arm was configured). "Needle-20" in DESIGN §7.4 is the
  runner's default full archive. No comparison involves depth. On screen: the flag changed nothing in our
  runs of this build, and nothing more.
- **D2, one CPU class.** Every Needle number, config and sealed, comes from Intel family 6 model 85.
  Needle's outputs are a property of that class; the cross-class difference measured in preflight (calls on
  2-3 of 29 items) is reported once and never mixed into a headline. It bears on every Needle comparison
  only as scope.
- **D3, no retrieval observed above five tools.** Bears only on V-COUNT, read as "all tools in the prefix".
- **D4, engine runtime failures are technical failures.** Bears on every Needle comparison: a `truncated`
  response scores as a technical failure (wrong on an act item, and not a correct non-action on a no-act
  item), where the vendor harness would count some of them as refusals. Wherever a no-act stratum is
  reported, its `truncated` count is shown beside the correct non-actions. Config side: 8 of 120 home and 5
  of 108 desk calibration items were technical failures under S1.
- **D5, outcome-blind LLM pool rule** (before any LLM call). llm-a is the best of the screened range, not of
  every cheap model: 55 models above the screen budget were not screened (`FRONTIER.md`). Comparison 1 and 5
  are scoped to "the cheap-LLM frontier as screened on 2026-09-22".
- **D6, the config-side accuracy axis** (corrected once, after the always-decline control and a refusal-only
  tuning showed the first form was wrong, before any LLM score was read). It chose llm-a and tuned K0's and
  K1's τ, so comparisons 1, 2 and 3 compare Needle with arms selected and tuned to weight acting and not
  acting equally, which is the sealed test's balance. Needle itself was not tuned on anything. It does not
  touch the test statistic (§7), which uses the test's own balanced cells.
- **D7, frontier window widened from 5 to 10 points after the screen was seen.** The 5-point rule picks the
  same arm (`FRONTIER.md`, sensitivity), so comparisons 1 and 5 are unchanged by it. Recorded as a
  post-hoc change.
- **D8, K1's bank rebuilt twice after its dev numbers were seen.** This is a choice among three banks made
  with results in view, which favours K1 in comparison 2. Two things bound it: the chosen bank still scored
  below K0 on dev (0.529 vs 0.619), and the two rejected indexings run on the sealed test too and are
  reported beside K1 (§3), so the reader sees what the choice was worth on data no one had seen. If K1
  beats Needle on test while a rejected bank does not, RESULTS says so.

Changes made at this step, recorded as such: the executed-scoreboard validator (`harness/execute.py`,
written here because DESIGN §7.1 names schema validation and no code implemented it; it reads nulls as
omitted after the first check on selection outputs flagged 21 llm-a desk bundles whose `date` was `null`);
the secondary validation-flagged row (§2); the two calibration sensitivity readings (§6); the repeats drawn
by item (§8).

## 10. Budget, worst case first

Episode cap $5 (paid API + Modal, one number). Spent to the end of step 7: **$1.271** (OpenRouter $0.617 +
Modal $0.654; `BUILD-LOG.md`). Remaining under the cap: **$3.729**. OpenRouter's key `m37-needle3` carries a
$4.00 provider-side limit (about $3.38 left on it); Modal has no per-app limit, so Modal spend is read with
`modal/modal_spend.py` before each tier. Labour (subscription quota, cc-zen) is not in the $5.

Worst-case rates: LLM calls at list price with no caching, 3,000 prompt tokens and the full 600-token cap
(llm-a $0.000444, llm-named $0.00042 per call; observed at the frontier stage about a seventh of that).
Needle at $0.30 per 1,000 five-tool requests, about three times the preflight's CPU-only figure, to cover
containers turned away from the wrong CPU class and retries; 20-tool requests at 2.6 times that.

| tier | what | worst case | cumulative worst |
|---|---|---|---|
| **1, reserved first** | llm-a and llm-named, 600 × S0/S1 (2,400 calls) | $1.04 | |
| | both LLM arms, band F × S1 (≤ 160 calls with a 40-item bound) | $0.07 | |
| | needle, 600 × S0/S1 plus band F (≤ 1,280 requests) | $0.38 | |
| | K0, K1 (+ first-bank rows), hassil, always-decline | $0.00 (local BM25, no model inference) | |
| | contingency: one LLM arm's main pass re-run | $0.53 | **$3.29** |
| 2 | latency: needle and baselines at 1 and 4 cores (4-core priced with no speed-up); both LLM arms' 200-item serial pass and network floors | $1.10 | |
| | repeats (60 items × 2 × 3 arms) | $0.15 | $4.54 |
| 3 | diagnostics, in the §8 priority order | per variant, projected before firing | |

**Rules.** Tier 1 fires first. Before each later stage, observed cumulative spend plus that stage's worst
case must be at most **$4.75**; otherwise the stage does not fire and RESULTS names it as not run. The
$0.25 below the cap covers billing lag. The contract variable and band F are never the thing cut. A stage
that fails is re-run from its saved partial results, not from scratch.

**Dropped, and not replaced:** the depth curve and every per-depth reliability diagram, operating point
and latency axis (D1).

## 11. Display rule for examples

Examples shown on screen or in the write-up are drawn, not picked. Within each (arm × schema × app ×
outcome) cell, items are ordered by `sha256("needle3-display-2026-09-22:" + id)` and the first three are
shown (all of them if the cell holds fewer), each labelled with its cell's denominator: "one of the n
wrong calls needle made on home requests", with n filled in. A longer sequence takes the next ones in the same order. An
example chosen by hand for the story (the HN opening, a band F request) is labelled "chosen" and carries
the same denominator. Technical failures are shown with the engine's own error text.

## 12. Before step 9 (to be committed and hashed in an addendum to this file, before the sealed inputs are opened)

1. `runs/sealed/run_sealed.sh`: the exact commands for every tier, reading only the three request files,
   writing raw outputs only, printing no request text to logs.
2. The latency function (hard CPU limit) and the LLM latency client in Modal (§8).
3. The contract-in-prompt system text (§8).
4. `results/score_test.py`: applies §4-§7 and fits nothing on test; it runs once, after every arm has
   finished. Before any aggregate is read, raw outputs are read end to end (DESIGN §10 step 10).

## 13. Not settled by this freeze

- The calibration partition is small on the act side (home 36 act items, desk 18) and its desk act items
  are nearly all A3; "no operating point" rests on it and on two sensitivity readings, not on a large sample.
- llm-a's host is one host on one day; FRONTIER.md's verdict line says "fp8" for Sail Research while its
  serving table and the snapshot's endpoint record say fp4. This freeze records fp4, from the snapshot;
  m37-lead should correct FRONTIER.md.
- The stored config-side outputs were produced before this file existed; they are the calibration
  evidence, not test outputs, and nothing in them is re-used on test.
- Everything in DESIGN §11 and §12.
