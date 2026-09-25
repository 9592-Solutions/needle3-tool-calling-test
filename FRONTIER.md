# Needle 3: the cheap-LLM arm, chosen on a measured frontier (DESIGN §4.2, §10 step 6)

Run 2026-09-22 by the configuration lead (session 2537465c) on the SELECTION partition only (342 items: home
170, desk 172; MASSIVE en-US train/dev, CLINC train/val, blind-authored edits; `partitions/`). No test item was
read, sampled or scored. Calls: `harness/llm_arm.py`; scoring: `frontier/score_frontier.py` with the shared
scorer (`harness/score.py`, `contracts/mapping.py`); raw per-call records in `frontier/screen/` and
`frontier/stage/`; computed tables in `frontier/screen_scored.json`, `frontier/stage_scored.json`.

Christo's constraint: the cheap generative comparator is "something on the Pareto frontier". The two axes are
accuracy on this task, measured here, and billed cost, observed here (sum of OpenRouter `usage.cost`,
spot-checked against `/generation` on three calls: identical to the digit). Neither comes from a table.

## Verdict

**Advanced arm: `deepseek/deepseek-v4-flash-0731`, host Sail Research (fp4; corrected 2026-09-22 from "fp8" to match the table and the snapshot, per FREEZE.md review), strict JSON-schema contract,
reasoning off, temperature 0.** D6-axis accuracy 0.795 on the selection partition at **$0.0597 per 1,000
requests**. The rule's two slots name the same model: it is the most accurate frontier point (b) and, because the
only cheaper frontier point is outside noise, also the cheapest frontier point within noise of the best (a).

**Named-claim arm (§4.2 step 6), runs regardless: `deepseek/deepseek-v4-flash`, the April snapshot, host
OpenInference (fp8), native tool-calling contract** (its better contract here: 0.726 native vs 0.646 schema), at
$0.0673 per 1,000. Labelled on screen as "the model the vendor's claim names, April snapshot as served by
OpenInference"; the vendor's snapshot is not identified.

The rule was fixed before any number (§4.2 step 5): drop dominated candidates; advance (a) the cheapest frontier
candidate whose paired, stratified bootstrap 95% interval for (best minus it) includes zero, and (b) the most
accurate frontier candidate. Accuracy axis: DESIGN §13 D6 (per app, half act accuracy and half the mean over
N1/N2/N3; then the mean over apps).

## The frontier stage (whole selection partition, both contracts where the host takes both)

| candidate (host) | contract | D6 accuracy | micro | $ / 1,000 (observed) | outcomes (correct act / correct none / wrong call / needless refusal) | status |
|---|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash-0731 (Sail Research) | schema | 0.795 | 0.806 | 0.0597 | 93 / 182 / 65 / 1 | **frontier; advanced** |
| google/gemma-4-26b-a4b-it (DekaLLM) | native | 0.727 | 0.701 | 0.0656 | 89 / 150 / 101 / 1 | dominated |
| deepseek/deepseek-v4-flash (OpenInference) | native | 0.726 | 0.716 | 0.0673 | 85 / 159 / 94 / 3 | named-claim arm (its better contract) |
| inclusionai/ling-3.0-flash (Novita) | native | 0.704 | 0.745 | 0.0098 | 69 / 185 / 60 / 27 | frontier (cheapest); gap to best +0.091 [+0.034, +0.149], outside noise |
| deepseek/deepseek-v4-flash-0731 (Sail Research) | native | 0.654 | 0.674 | 0.0761 | 80 / 150 / 110 / 1 | the model's weaker contract |
| nvidia/nemotron-3.5-lightning (Phala) | schema | 0.649 | 0.648 | 0.0901 | 87 / 134 / 119 / 1 | dominated |
| deepseek/deepseek-v4-flash (OpenInference) | schema | 0.646 | 0.648 | 0.0296 | 84 / 137 / 117 / 3 | the model's weaker contract |
| nvidia/nemotron-3.5-lightning (Phala) | native | 0.622 | 0.581 | 0.0674 | 87 / 111 / 142 / 1 | the model's weaker contract |

Every call was served by exactly its pinned host (fallbacks off, `require_parameters` on); zero technical
failures and zero unserved calls in the stage.

**Sensitivity.** The design's own window (undominated at the screen, or within 5 points of the best) would have
sent only deepseek-v4-flash-0731 and ling-3.0-flash (plus the named-claim model) to this stage and picked the
same arm. The window was widened to 10 points AFTER the screen was seen (DESIGN §13 D7) because the screen's own
per-candidate interval is about ±6 points; widening added three candidates and changed nothing.

## The screen (100 selection items per app, one contract per model)

Pool rule: DESIGN §13 D5 (outcome-blind, written before any call): 129 models met §4.2's rule, 88 after P1-P4,
and the 33 cheapest by projected cost fit the $0.75 projected screen budget. Contract: strict JSON schema where
the host takes it, else native tools.

| candidate (host) | contract | D6 accuracy | $ / 1,000 | technical failures | dominated by (count) |
|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash-0731 (Sail Research) | schema | 0.814 | 0.0597 | 0 | 0 |
| nvidia/nemotron-3.5-lightning (Phala) | schema | 0.728 | 0.0917 | 0 | 1 |
| google/gemma-4-26b-a4b-it (DekaLLM) | native | 0.726 | 0.0652 | 0 | 1 |
| inclusionai/ling-3.0-flash (Novita) | native | 0.725 | 0.0108 | 0 | 0 |
| google/gemma-4-31b-it (DeepInfra) | schema | 0.710 | 0.0662 | 5 | 3 |
| ibm-granite/granite-4.2-8b (CoreWeave) | schema | 0.709 | 0.0537 | 0 | 1 |
| deepseek/deepseek-v4-flash (OpenInference) | schema | 0.704 | 0.0284 | 0 | 1 |
| qwen/qwen3-30b-a3b-instruct-2507 (DekaLLM) | schema | 0.664 | 0.1019 | 6 | 7 |
| google/gemma-3-27b-it (DeepInfra) | schema | 0.657 | 0.0836 | 2 | 6 |
| microsoft/phi-4 (DeepInfra) | schema | 0.655 | 0.0719 | 1 | 6 |
| openai/gpt-oss-20b (AkashML) | schema | 0.640 | 0.0254 | 0 | 1 |
| inception/mercury-2.5 (Inception) | schema | 0.640 | 0.1180 | 21 | 11 |
| qwen/qwen3.5-9b (SiliconFlow) | schema | 0.639 | 0.1018 | 0 | 10 |
| qwen/qwen3-32b (DeepInfra) | schema | 0.634 | 0.0856 | 0 | 9 |
| qwen/qwen3-14b (NextBit) | schema | 0.633 | 0.1034 | 0 | 13 |
| mistralai/ministral-3b-2512 (Mistral) | schema | 0.616 | 0.0203 | 0 | 1 |
| nvidia/nemotron-3-super-120b-a12b (DekaLLM) | schema | 0.611 | 0.1078 | 7 | 15 |
| google/gemma-3-12b-it (DeepInfra) | schema | 0.592 | 0.0546 | 3 | 5 |
| upstage/solar-pro4 (Upstage) | schema | 0.564 | 0.1071 | 5 | 16 |
| qwen/qwen-2.5-7b-instruct (Phala) | schema | 0.558 | 0.1026 | 0 | 15 |
| mistralai/mistral-small-24b-instruct-2501 (DeepInfra) | schema | 0.545 | 0.0522 | 0 | 4 |
| mistralai/mistral-small-3.2-24b-instruct (DeepInfra) | schema | 0.536 | 0.0810 | 0 | 11 |
| mistralai/mistral-nemo (DekaLLM) | schema | 0.515 | 0.0192 | 0 | 1 |
| nvidia/nemotron-3-nano-30b-a3b (Crusoe) | schema | 0.500 | 0.0622 | 5 | 9 |
| openai/gpt-5-nano (Azure) | schema | 0.495 | 0.0466 | 2 | 5 |
| openai/gpt-oss-120b (AkashML) | schema | 0.486 | 0.0431 | 61 | 5 |
| z-ai/glm-4.7-flash (Venice) | schema | 0.472 | 0.0699 | 0 | 14 |
| google/gemma-3-4b-it (DeepInfra) | schema | 0.436 | 0.0524 | 0 | 8 |
| bytedance-seed/seed-1.6-flash (Seed) | native | 0.414 | 0.1008 | 0 | 21 |
| meta-llama/llama-3.1-8b-instruct (Groq) | native | 0.376 | 0.0227 | 58 | 3 |
| meta-llama/llama-3.2-3b-instruct (Parasail) | schema | 0.354 | 0.0931 | 43 | 22 |
| rekaai/reka-flash-3 (Reka) | schema | 0.301 | 0.1030 | 1 | 27 |
| z-ai/glm-5.3-flash (DeepInfra) | schema | not measured | | | **unreachable**: every call refused upstream (HTTP 429, shared pool) across the smoke test and four retry passes on 2026-09-22 |

**Not screened** (above the $0.75 projected screen budget of D5; a claim about "the cheap-LLM frontier" is
scoped to the screened range): `meta-llama/llama-4-scout`, `stepfun/step-3.5-flash`, `qwen/qwen3-235b-a22b-2507`, `meta-llama/llama-3.3-70b-instruct`, `google/gemini-2.5-flash-lite`, `bytedance-seed/seed-2.0-mini`, `openai/gpt-4.1-nano`, `qwen/qwen3-next-80b-a3b-instruct`, `qwen/qwen3.6-35b-a3b`, `deepseek/deepseek-v4.1-flash`, `qwen/qwen3-30b-a3b`, `xiaomi/mimo-v2.5`, `tencent/hy3`, `mistralai/ministral-8b-2512`, `tencent/hunyuan-a13b-instruct`, `z-ai/glm-4.5-air`, `openai/gpt-4o-mini`, `mistralai/mistral-small-2603`, `qwen/qwen3.5-35b-a3b`, `stepfun/step-3.7-flash`, `google/gemini-3.5-flash-lite`, `mistralai/ministral-14b-2512`, `meta-llama/llama-4-maverick`, `mistralai/mistral-saba`, `qwen/qwen3.8-27b`, `openai/gpt-5.6-luna`, `openai/gpt-5.4-nano`, `minimax/minimax-m3`, `deepseek/deepseek-v3.2`, `minimax/minimax-m2.7`, `inception/mercury-2`, `deepseek/deepseek-chat-v3.1`, `deepseek/deepseek-chat-v3-0324`, `minimax/minimax-m2`, `anthropic/claude-3-haiku`, `minimax/minimax-m2.5`, `deepseek/deepseek-v3.1-terminus`, `google/gemini-3.1-flash-lite`, `qwen/qwen3.5-27b`, `bytedance-seed/seed-2.0-lite`, `openai/gpt-5-mini`, `bytedance-seed/seed-1.6`, `z-ai/glm-4.6v`, `meta/muse-glimmer-30b`, `minimax/minimax-m2.1`, `deepseek/deepseek-chat`, `qwen/qwen-2.5-72b-instruct`, `z-ai/glm-5.3-flashx`, `google/gemini-3.6-flash`, `openai/gpt-4.1-mini`, `z-ai/glm-4.7`, `mistralai/mistral-medium-3.1`, `mistralai/mistral-medium-3`, `z-ai/glm-4.6`, `xiaomi/mimo-v2.5-pro`.

## Serving conditions, recorded per arm

| arm | host | quantisation (as listed) | contract | sampling | reasoning |
|---|---|---|---|---|---|
| deepseek/deepseek-v4-flash-0731 | Sail Research | fp4 | schema | temperature 0 | `reasoning.enabled=false` |
| deepseek/deepseek-v4-flash | OpenInference | fp8 | native | temperature 0 | `reasoning.enabled=false` |

Both contracts send the same S1 tool descriptions and the desk app's fact line; the system turn is the one fixed,
task-neutral paragraph of §4.2 (information parity). Strict-schema optional fields are rendered as required and
nullable (the strict-mode form), and nulls are dropped before scoring.

## Harness findings from reading raw outputs (before any number was believed)

- **Fixed (harness):** under the schema contract, the gpt-oss-20b host (AkashML) ignores `response_format` and
  returns the model's calls as native `tool_calls` with empty content. The parser read only content and scored 84
  well-formed answers as failures. Rule now: under the schema contract, empty content plus native tool calls is
  read as the answer (`harness/llm_arm.py`; stored responses re-parsed offline, `frontier/reparse.py`, originals
  kept as `pred_v1`). gpt-oss-20b went from 0.386 to 0.640; it stays dominated.
- **Left as model or host failures (counted wrong):** gpt-oss-120b and mercury-2.5 return a bare call or list
  instead of `{"calls": ...}` despite the strict schema; llama-3.1-8b calls tools that do not exist (Groq rejects
  them); one gpt-5-nano content-filter refusal.
- **Contract-dependent:** about 30 strict-schema replies (nemotron, qwen, gemma, phi, llama-3.2) run to the token
  cap on whitespace right after a required argument, where the strict form makes an optional field required and
  nullable. The frontier stage judged each model on its better contract, so no model was sunk by this alone.
- **Unserved calls** (HTTP 429 from a host's upstream pool) are excluded and counted apart, never scored as a
  model's technical failure; the frontier stage had none.

## Weak points

- The selection partition is the config side: crowd corpora plus blind-authored edits, its desk act items are
  mostly A3, and its strata are not balanced like the sealed test's (D6). The advanced arm is re-measured on the
  sealed test; these numbers are never the headline.
- One run per arm; no repeat. Prices move within a day (promotional `discount` fields on several hosts).
- Sail Research is the host that serves the July snapshot cheapest under the account's ZDR setting; the arm is
  that model as that host serves it.
