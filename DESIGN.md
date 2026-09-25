# Needle 3: measurement design

Written 2026-09-21 by the needle-3 design worker (session befa255c, account 5). **Paper only**:
nothing here was run, no model was loaded, no paid call was made, and no test material was read.
The build starts only after jev-2 clears Christo's review (RULINGS 2026-09-21, "Needle 3
(Recommended)"). Everything below is what the build freezes; where it is still a choice, it says
so and `OPEN.md` carries it.

Inputs this rests on, all in this directory:
- `research/needle3-facts.md`: Needle 3's training lineage, the vendor's evaluations, the engine's
  interface and its gotchas (every claim sourced and tagged).
- `research/request-sourcing.md`: where real, held-out, licence-clean requests come from.
- `research/arms-and-cost.md`: the comparator pool from live OpenRouter endpoints, the keyword
  baseline, Modal pricing, the statistics. Raw pulls in `research/raw/`.
- `pro/pro-answer.md`: a GPT-6 Pro run that designed its own experiment BEFORE this file existed
  (prompt committed first, `60f77fc3`). What it changed is recorded in `PROTOCOL-READ.md`; this
  file is the version after those changes.
- `../NEXT-SUBJECT.md` (the approved card Q and its Pro-judge repair) and jev-2's
  `trial/DESIGN.md`, `trial/FRONTIER.md`, `trial/FREEZE.md`, whose shape this follows.

## 0. The question, and what the measurement must be able to say

Approved question: **"What can Needle 3 actually do for an app, and which requests should the app
refuse?"** The payoff (Pro-judge repair, kept): the viewer can tell an unsupported request from a
correct refusal from a wrong call, recognise which app designs suit the model, and see its
measured reliability on phrasing it was never shown. **Not** a universal one-line rule.

So the unit of measurement is not "did Needle emit a plausible call". It is, per request:
**given this app's tools and the facts it has, did the system do exactly the permitted thing,
correctly do nothing, needlessly decline, or attempt a wrong action?** (Pro's framing, adopted.)
Every design choice below serves one of four things the video must show with a denominator:
1. outcome rates by request class, per app;
2. how much of that is the TOOL LIST rather than the model (the scout's "the tool list decides
   half the result", made a declared variable);
3. what an app gains or loses by gating on the confidence score (execute vs defer);
4. where a keyword matcher and a cheap LLM land on the same requests, and at what cost and latency.

The experiment must stay capable of producing any of these conclusions: a useful narrow
component; confirmation-first only; worse than a lexical parser; unsuitable for one app and fine
for another. If a design choice would make one of those impossible to reach, it is a defect.

## 1. What is under test, pinned

**System under test: "Needle 3 as shipped, untuned"**: the model plus Cactus's C++ engine, which
applies deterministic repair rules, grounding and negation gates and a 0.1 confidence floor before
anything is returned (`research/needle3-facts.md` §3). We measure the public output of that stack,
because that is what an app receives, and we say on screen that it is model-plus-engine, never
"the network alone". We do not claim to attribute errors between the network and the engine
rules; where the engine exposes a stage (`suppressed_calls`, `validation`), it is logged, not
interpreted as the raw model proposal.

Pins, recorded in the freeze and re-checked at run time:
- HF `Cactus-Compute/needle3` revision `b274efcb`; `needle3.cact` sha256
  `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38` (35,335,380 bytes;
  unchanged since the first commit on 2026-09-16, only engine binaries moved since).
- The `linux-x86_64/needle` native runner binary hash, the engine version string, the
  `cactus-needle` wheel version (PyPI shows 3.0.4, git main 3.0.1: pin whichever the runner
  reports and record both), and the runner's `--help` output.
- The package fetches weights from HF `main` without a revision: set `HF_HUB_OFFLINE=1` after a
  pinned download so nothing re-fetches.
- `NEEDLE_TELEMETRY=0`, `DO_NOT_TRACK=1` (telemetry is on by default).

**How it is called.** The native runner, one fresh process per request:
`./needle --model needle3.cact --tools <app>.json [--system <facts>.txt] --prompt "<request>"
--depth N --threads T --fail-input-overflow`. Reasons, each from a documented trap:
- `--depth N` slices the SHIPPED 2-bit archive at runtime, which is how the vendor's charts were
  made. `needle build --layers N` re-exports at 4-bit, and Python exposes no depth at all, so a
  Python depth sweep would silently compare quantisations (facts §3; Pro §1). No substitute is
  allowed: if `--depth` misbehaves in preflight, the depth comparison is dropped, not faked.
- One process per request: the engine keeps conversation state between calls, and `/reset` in
  `--serve` mode is reported not to clear the KV cache (issue #136). Leakage between unrelated
  requests was the Prompt Engineering video's gotcha #1.
- `--fail-input-overflow`: the default silently trims an oversized turn.
- No `--forced`. Forced mode "always dispatches a call", which removes the refusal path the
  question is about. A forced pass is run as a SECONDARY row only, so our numbers can be set
  beside the vendor's fine-tune chart, which was forced.
- `system` carries facts only (the vendor's documented contract); the home app sends none, the
  desk app sends a fixed `date:`/`locale:` fact so relative dates resolve identically on every
  run. The Python wrapper's auto-date is never in the path.
- **No `triggers` in any primary arm.** A matching trigger forces a call and bypasses the
  confidence floor, so a triggered Needle is partly a regex we wrote. Triggers get their own
  diagnostic arm (§5.4).

**Depths.** 20 is the arm of record. 16, 8, 4 and 2 are run as a curve (the vendor's own ladder;
compute is cents) and reported as a curve, not as five competing arms. **Dropped after preflight
(§13 D1): the runner's `--depth` has no effect.**

**Why untuned only.** The approved card excludes fine-tuning (card T is the natural second
piece, and the Pro judge advised against merging it). The blind Pro read proposed one local LoRA
run with a matched control; it is declined for this piece (`PROTOCOL-READ.md` R1). The claim is
therefore scoped: this measures the model as downloaded, which the vendor ships and demos but
does not present as its recommended production path. That scope goes on screen.

## 2. The apps: two, invented, each with a written contract

The pilot's measurement unit is an app, not a model. Two apps, deliberately different:

| app | tools (5, final list frozen at build) | what it stresses | request source |
|---|---|---|---|
| **Home** | lights on/off, light level, light colour, vacuum, smart plug; rooms as an enum | routing, polarity, closed sets, relative wording ("dim the lights" with no number) | MASSIVE `iot` crowd requests |
| **Desk** | set alarm, remove alarm, add to list, remove from list, create reminder | times and units ("25 minutes" is 1500 s, not 25), verbatim text, dates against a fixed date fact, identifiers | MASSIVE `alarm`, `lists`, `calendar_set` crowd requests |

Why these two and not the scout's single smart home: one app makes every finding a finding about
that app, and the Pro read's strongest structural point was that the video's claim is about app
design. The desk app is where the thread's number-copying failures live ("25 minute timer" →
`duration_seconds: 25` at confidence 1.0, viccis 49759084). Both are in the vendor's target
domains; that is the fair ground for "what can it do for an app", and it means a good result
cannot be dismissed as us testing it off-label. A third app outside the vendor's training
categories (the Pro read proposed an inventory ledger) is `OPEN.md` #1: it has no source of real
phrasing, so every request would be agent-written.

**Not used as a schema, anywhere: Cactus's own environments** (`needle/environments/*`), the demo
presets (either Wayback snapshot) or the playground presets. They are vendor material tuned
against their own cases. The vendor's `smart_home` environment appears once, as a labelled
home-turf contrast (§5.3).

**Each app has a behavioural contract, written before any request is labelled**: the tools as
JSON Schema, the valid entities, which arguments are required and what each optional one defaults
to, units, permitted normalisations (number words, "percent"), and the atomic rule: **a request
the app can only partly serve gets no action** (partial fulfilment is a separately labelled
diagnostic, never an undisclosed scoring choice). The contract is the ground truth; gold labels
derive from it, not from anyone's guess about what Needle ought to do.

**The biggest single lever is the required-argument policy, and it is fixed on principle before
any data, not tuned.** 79 of the 130 light requests in MASSIVE `iot` test name no room
(`research/request-sourcing.md` §6). If `room` is required, most of the home band turns into
correct refusals and the piece becomes a refusal test. The contract gives `room` an explicit
default ("the room the device is in", modelled as a declared default value) because that is how a
real home app behaves, and says so. The alternative contract (room required) is run as a
diagnostic on the same items so the viewer can see what that one line does.

## 3. Requests: where they come from

### 3.1 Principles
- **Real phrasing first.** The crowd corpora (MASSIVE en-US, which is SLURP's text; HWU64; CLINC150)
  were written by people told a goal, never a tool (HWU keeps its 21 `iot` elicitation prompts).
  All CC BY 4.0 / 3.0, so the whole set can be published with attribution.
- **Excluded as test material**, because Cactus evaluated on it or on its parent: Mobile Actions,
  DroidCall, BFCL v4 (and When2Call, built from BFCL), DSTC8/SGD, SNIPS; also xLAM/APIGen/ToolACE/
  Toucan/glaive (named in Needle's training lineage, `research/needle3-facts.md` §1). Licence
  excludes HomeBench (no licence), Snips SmartLights and Fluent Speech Commands (non-commercial),
  allenporter's HA datasets (no LICENSE file).
- **Authored text only where no real phrasing exists**, as minimal labelled edits of a real
  utterance (add a negation, push a value out of range, delete a required value, wrap it in a
  quotation), each with a `derived_from` id and reported as its own group.

### 3.2 Scenario families and two phrasings (the pairing that does three jobs)
A **family** is one scenario: an intent plus its slot values, under one app contract. Each test
family carries **two phrasings**:
- **P1, crowd**: the MASSIVE/CLINC utterance (or its minimal edit);
- **P2, fresh**: written for this build by a writer agent that sees only a plain-language scenario
  description (the HWU-style goal plus the slot values), never the crowd utterance, never the tool
  schema, never any model output. Two writer families (one Claude, one non-Anthropic model via
  cc-zen, which is labour and not in the $5), alternated by family, author id recorded.

The pairing gives, at once: (a) the Pro read's paired phrasings, so "generalises to unseen
phrasing" is measured within a family rather than across different scenarios; (b) the
contamination canary of §6.2, since P1 is public and P2 did not exist before the build; (c) a
register check, since P2 is written in an LLM's register and P1 is not, and an arm that gains on
P2 relative to the others is benefiting from register rather than from understanding.

Both phrasings of a family stay in the same partition, and every interval resamples whole families.

### 3.3 Strata (balanced by design; not a traffic estimate)
Six strata per app, three where the correct outcome is to act and three where it is to do nothing
(Pro's structure, adopted; it replaces the scout's bands, which were five refusal-type bands and one
act band and would have let an always-refusing system look good):

| stratum | correct outcome | P1 source |
|---|---|---|
| A1 direct, fully specified | the call(s) | MASSIVE test, supported intents with all required slots |
| A2 indirect, conversational, relative | the call(s), where the contract can represent it | MASSIVE test (`lightdim`/`lightup` with no number, "it's awfully dark here", "time to sleep") |
| A3 normalisation or explicit two actions | the call(s) | MASSIVE test (units, number words, times); two-action items as minimal joins of two real requests |
| N1 capability, entity or value the app does not have | nothing | MASSIVE `iot_coffee` (36 in test), CLINC `smart_home` requests for excluded devices, near-miss MASSIVE scenarios (volume, weather), CLINC `oos` |
| N2 missing required information or genuinely ambiguous | nothing | MASSIVE items lacking a required slot under the frozen contract, plus minimal deletions |
| N3 negation, quotation, reported speech, unsupported conditional | nothing | minimal edits of HWU `iot`/`alarm` rows that are NOT in MASSIVE (so an edit cannot shadow a P1 of another stratum) |

Whether a given A2 request is "act" or "nothing" is decided by the contract, not by a rule that
indirect wording must fail: "dim the lights" is supported by a contract with a relative level tool
and unsupported by one with only an absolute setter. That contrast is the tool-list variable of §5.

The HN requests (~30 real phrasings aimed at this model, `research/request-sourcing.md` §4) are a
**named band F, scored under our frozen schema and reported separately, never pooled**. The maker
retuned the demo's tools against exactly these requests, so they cannot estimate a rate; they can
answer "does it still fail on these when we hold the schema fixed?", and they are the natural
opening.

### 3.4 Size and partitions
| partition | size | from | used for |
|---|---|---|---|
| dev | 2 apps × ~150 | MASSIVE train/dev, CLINC train/val, HWU-not-MASSIVE | contract checks, prompt and schema rendering, scorer, parser, preflight |
| selection | 2 × ~150 | MASSIVE train/dev, CLINC val | the cheap-LLM Pareto frontier (§4.2) |
| calibration | 2 × ~120 | MASSIVE train/dev | confidence operating points (§7.3) |
| lexical bank | 2 × 200 | MASSIVE train | the example-fed keyword arm only (§4.3) |
| **test (sealed)** | **2 apps × 6 strata × 25 families × 2 phrasings = 600** | MASSIVE test, CLINC test, HWU-not-MASSIVE edits, fresh P2 | the numbers in the video |
| diagnostics (sealed) | ~144 anchors | test-like, separate families | tool-list and runtime counterfactuals (§5) |
| band F | ~30 | the HN thread | reported alone |

**Why 600 and not the scout's ~300.** At n = 300 one arm's accuracy carries about ±4.5 points at 80%
and a paired difference between two arms about ±3 to ±4.5 (`research/arms-and-cost.md` §2.3), so no
on-screen ranking could separate arms closer than about 5 points, and per-stratum claims (25
items) would be wider than any plausible effect. 600 roughly halves the variance at a few cents of
extra API. Even so, the effective unit is the family (300), which the intervals say. The home
app's supported MASSIVE test pool (184 items) is the binding ceiling on A1 to A3 crowd phrasing;
if a stratum cannot reach 25 families from real P1s, it is filled with minimal edits, labelled.

Near-duplicates are removed ACROSS partitions before sealing: normalised exact match, word and
character n-gram similarity, and an embedding-similarity threshold (short commands collide easily:
"dim the lamp" / "dim the lamps"). The rule and the drop list are published.

### 3.5 Gold labels
Two annotator agents, blind to each other and to every model output, each map every item to the
expected call multiset (or nothing) from the written contract. Disagreements are adjudicated by a
third pass with both drafts kept; an item still ambiguous after adjudication is labelled
`ambiguous`, excluded from the headline and reported. Agent agreement is not human validation, and
correlated interpretation errors are the realistic risk, so the scorer gets **mutation tests**
(swap two arguments, change a unit, add an extra call, drop a field, flip polarity) that must all
score wrong before the scorer is frozen (Pro §8).

### 3.6 Sealing
- A **test custodian** (one worker session) builds, labels and seals the test and diagnostics. No
  agent that configures an arm, writes a prompt, writes triggers or chooses a threshold can read
  them; configuration workers get dev, selection and calibration only.
- Before any arm touches test: publish a salted SHA-256 commitment of the sealed files in the
  repo, and a `FREEZE.md` (jev-2 pattern) whose commit precedes every file under `results/`.
  Salt and files are revealed with the results.
- The test runner writes raw outputs only; scoring runs once, after all arms have finished.
- If a scorer or gold bug is found after unblinding, the correction is versioned and both the
  original and corrected numbers are published; a changed criterion never passes as untouched
  confirmation.

## 4. The arms

### 4.1 Needle 3 (the subject)
As §1: shipped archive, native runner, depth 20 of record plus the depth curve, gate on, schema S1
(§5), one process per request. Primary outcome reads `function_calls`; `suppressed_calls`,
`validation`, `confidence`, `reasoning`, `prefill_tps`, `decode_tps`, `peak_ram_mb` all logged
raw.

### 4.2 The cheap LLM, chosen on a measured frontier (Christo: "something on the Pareto frontier")
Procedure (jev-2's, adapted; the rule is fixed before any number exists):
1. **Pool**: every model with a host reachable under the account's zero-data-retention setting
   that takes tool calls or a strict JSON schema, under a price ceiling of $0.50/M in and $2/M out
   (`research/arms-and-cost.md` §1.2 lists ~15 today). One host pinned per model, fallbacks off,
   `require_parameters: true`, `served_by` recorded on every call, temperature 0 sent explicitly
   (recorded where refused), reasoning off where the host allows.
2. **Output contract, the variable jev-2 showed matters most** (Ling: 66.5% without a schema,
   93.9% with one, `../../jev-2/trial/FRONTIER.md`): primary contract is a **strict JSON schema
   whose output is a list of calls, where the empty list is the refusal**, which is Needle's own
   output space. The native `tools` + `tool_choice: "auto"` contract is run on selection too, and
   each model keeps whichever scored better there (ties to the schema). `tool_choice: "required"`
   is never used: it cannot express a refusal. Both contracts get the same tool descriptions and
   the same app facts; no few-shot examples (Needle gets none).
   **Information parity.** Needle's system turn takes facts only, and "instructions placed there do
   not steer the model" (vendor docs). So an LLM system prompt must not carry contract knowledge
   Needle cannot receive (the atomic rule, the default policy, "refuse when unsure"): every rule a
   model needs lives in the tool descriptions, which both arms see byte-identically. The LLM
   system prompt is one fixed, published, task-neutral paragraph ("call the tools below for the
   user's request; return an empty list if none applies"), and the selection-stage prompt variants
   may change wording but add no contract knowledge. An app CAN tell an LLM more than it can tell
   Needle, which is a real advantage of the LLM; it is measured as a labelled diagnostic ("LLM with
   the contract in its prompt", §5.3), never folded into the primary comparison.
3. **Screen** on 100 selection items per app, every candidate, schema contract. **Frontier** on
   all ~300 selection items: every candidate not dominated at the screen plus any within 5 points
   of the best, both contracts.
4. **Axes**: exact contract accuracy (§7.1), macro-averaged over the two apps and six strata; and
   OBSERVED billed dollars per 1,000 requests (sum of `usage.cost`, spot-checked against
   `/generation`), never a rate card.
5. **Decide**: drop dominated candidates; advance (a) the **cheapest frontier candidate whose
   paired, family-clustered bootstrap interval for (best minus it) includes zero**, and (b) the
   **most accurate frontier candidate**, if different. Both are on the frontier; (a) answers "the
   cheap option a builder would pick", (b) "the best a cheap LLM does here". The whole frontier is
   published with the rule's sensitivity (jev-2's pick moved when a better arm was added).
6. **The named-claim arm.** The vendor's claim names "DeepSeek V4 Flash" without a snapshot; three
   are on OpenRouter. It runs in the final test regardless, labelled "the model the vendor's claim
   names, April snapshot as served by OpenInference", unless the snapshot is identified from
   Cactus's own benchmark page first. It is not the frontier arm unless the rule picks it.

Selection numbers are never the headline: the advanced arms are re-measured on the sealed test.

### 4.3 Keyword baselines: two data budgets, both declared
The thread proposed "a BM25 algorithm over an index of trigger phrases for each category, sitting
behind a majority-vote classifier" (potatoman22, 49760041); the founder said it is "not yet clear
how well, say, 8-30MB worth of regexs ... would do" (49759061). Nobody built it. A deliberately
weak handful of regexes would be a straw man, and agent labour is cheap, so the baseline is built
properly (Pro §4) and its data budget is stated, not hidden:
- **K0, schema-only**: a blind author agent writes up to 15 trigger phrases per tool from the frozen
  schema alone (the same information Needle gets), in one pass from a published prompt. BM25
  (`bm25s`, version pinned), lowercase + Snowball stemming, **no stop-word removal** ("on", "off",
  "up", "down" carry the meaning), top-5 majority vote, refuse below a score threshold τ or vote
  margin μ. Only τ, μ, k are tuned, on dev.
- **K1, example-fed**: the same machinery indexed on the 200-item labelled lexical bank per app,
  i.e. "an engineer with a few hundred labelled examples". This is the stronger baseline and it has
  data Needle untuned does not; every chart that shows it says so.
- **Shared argument extractor**, rule-based, written by the same author from the schema only:
  enum gazetteer from schema values and synonyms in the schema's own descriptions; numbers, number
  words and units with range validation (out of range refuses, never clamps); on/off verb lexicon;
  relative words mapped only when the schema has a relative tool; free text as the span after the
  trigger; conjunction split for two-action requests; **required argument unfillable → refuse**.
- **hassil**, Home app only: Home Assistant's own English templates from `OHF-Voice/intents`,
  UNMODIFIED, with a declared intent-to-tool table and our room and device lists, written before
  dev. It represents years of community template work, not an afternoon, and is labelled so; if
  our schema cannot be mapped without writing templates, the arm is dropped rather than authored.
- **Always-decline**: returns nothing for every request. It costs nothing and is the check that a
  refusal-heavy result is not mistaken for competence.

An embedding nearest-neighbour router is run on dev only as a diagnostic (jev-2 found it tied the
LLMs); it becomes an arm only if it beats K1 by more than the noise, and then as "labelled
examples" alongside K1.

## 5. The tool list as a declared variable

The scout found the tool list decides half the result, and the vendor says "describing them well
is the whole game". So the schema is a factor, not an accident, and every arm (Needle, the LLM arms,
K0, K1) runs under each full-test schema so the question "how much more does the small model depend
on the list" is answered as a difference of slopes.

### 5.1 Full-test schemas (on all 600)
- **S1, guide-written (primary)**: the app's tools written to the vendor's own published design
  rules (one tool per action, enum values in user words, no enum value hidden in a common word,
  formats in descriptions, bounds in the schema, sensible defaults). Using the vendor's rules is
  the fairness check: a schema that ignores them invites a fair rebuttal.
- **S0, first draft**: the same actions written as a typical developer first would, in OpenAI
  function style, by a blind author told nothing about Needle's guide; then S1 is produced from S0
  by applying the guide's checklist, both published with the diff. S0 vs S1 is "what the tool list
  alone buys".

### 5.2 The relative-tool contrast (Home, on the A2 families and matched N1 controls)
S1 with an absolute `set_light_level(room, percent)` only, versus S1 plus
`adjust_light_level(room, direction)` with an app-defined step. MASSIVE's `lightdim`/`lightup`
requests ("dim the lights", no number) are the natural test: under the first contract the correct
outcome is nothing, under the second it is a call. This is the card's "make it a little warmer"
bridge, measured on real phrasing rather than staged.
**Changed 2026-09-22 (configuration lead, session 2537465c), before any run:** the relative variant
is S1 with the smart-plug tool REMOVED and `adjust_light_level` added, so it stays at five tools.
"S1 plus" would be six tools, above the five-tool line where the vendor docs say retrieval engages
(§5.3), so the contrast would confound the relative tool with the tool count. The plug is removed
because it shares no vocabulary with light requests, and the variant is scored only on light items
(`production/needle3/contracts/CONTRACT.md` §4, V-REL).

### 5.3 Diagnostics (sealed, ~144 anchors, Needle-heavy; not in the headline)
One thing varied at a time around fixed anchors:
- **Tool count 5 / 6 / 10 / 20** with similar distractors. The vendor's docs contradict each other on
  whether a retrieval head selects five tools above five or every tool enters the prefix
  (`research/needle3-facts.md` §3). Preflight inspects the archive's head manifest and the engine's
  behaviour; if the selected subset is not observable, attribution between retrieval and generation
  is reported as unresolved, never inferred from wrong answers.
- **Argument representation**: `duration_seconds` vs `amount` + `unit`.
- **Specific tools vs one dispatcher tool**.
- **Tool order and aliases**, including **familiar vs unfamiliar tool names**: Needle 1/2's
  training set named 232 tools (`control_lights`, `set_thermostat`, `start_robot_vacuum`,
  `set_alarm`, ...; `research/needle3-facts.md` §1). S0/S1 tool names are checked against that list
  and the overlap is recorded in the freeze; the diagnostic renames the same tools to names absent
  from it, so "it knew the tool name from training" is measured rather than argued.
- **LLM with the contract in its prompt** (the information-parity diagnostic of §4.2).
- **Vendor home turf**: Home families re-annotated to Cactus's `smart_home` environment (5 tools,
  vendor-tuned), the best case the maker would choose.
- **Triggers**: S1 plus triggers compiled from K0's blind trigger list, so Needle and BM25 get
  identical keyword knowledge; scored on negations, quotations and two-action items as well,
  because a trigger that raises recall can also force false activations.
- **Required `room`**: the alternative contract of §2.
- **`--forced`**: for comparability with the vendor's fine-tune chart.

The LLM arms run the diagnostics that are schema-only (S0/S1 are already full-test); the
catalogue-size diagnostic is Needle-only, to keep the API bill bounded.

## 6. Contamination

What can honestly be claimed: **these requests and phrasing families were withheld from every step
that configured an arm, and we checked overlap against named public material.** Not: that neither
model ever saw anything similar. Needle's 360B-token training set is proprietary; its lineage
(Needle 1/2's card, in git history) includes Gemini-generated data over 232 on-device tools, Pleias,
Toucan and xLAM, and MASSIVE's text has been public since 2019 via HWU64 (192 of the 220 MASSIVE
`iot` test utterances are verbatim in HWU64).

### 6.1 Overlap scans (before sealing)
Every candidate test item against: Cactus's six environment test suites, both Wayback snapshots of
the demo, the playground presets, the fine-tuning guide's examples, and every other partition of
our own set. Near-duplicates are dropped. Run on the rented machine, not through a search service.

### 6.2 The canary, measured not argued
- **P1 vs P2 per arm** (§3.2): a memorising system does better on the public crowd phrasing than on
  a fresh paraphrase of the same scenario. Because P2 differs in register too, the signal is the
  **difference in differences across arms**, not one arm's gap: every arm pays whatever the register
  shift costs, and only an arm that has seen the corpus should pay extra on P2.
- **Partition gap** on non-test material: Needle and the frontier LLM on a difficulty-matched sample
  of MASSIVE `iot` train vs dev items (both public, so this only detects selective memorisation of
  one split; weak evidence, stated as weak).
- **Prefix completion** (jev-2's method, LLM arms only; Needle cannot produce free text): given the
  first half of a crowd utterance, does the model reproduce the rest verbatim?
A clean canary is weak evidence of cleanliness and is reported that way; a gap goes on screen.

## 7. Scoring, confidence and uncertainty

### 7.1 Two scoreboards (Pro §6, adopted)
- **Proposal**: what the system returned, against the contract.
- **Executed**: what the app would actually do after deterministic schema validation, the atomic
  rule and the chosen confidence policy. This separates "the model was right" from "the app caught
  it", in both directions.

**Exact correctness** (primary): every required call present with exactly correct arguments, no
extra call, order enforced only where the contract says order matters (otherwise compared as a
multiset, duplicates retained). Deterministic normalisation, declared before dev: case and
whitespace, int/float numeric equality, declared default equivalences, verbatim text preserved
where the contract says so. No LLM judge.

Every request lands in exactly one outcome:
| outcome | meaning |
|---|---|
| correct action | exact match on an act item |
| correct non-action | nothing on a no-act item |
| wrong call | a call on a no-act item, or a wrong call on an act item |
| needless refusal | nothing on an act item |
| technical failure | crash, timeout, malformed output, overflow, transport error: **never counted as a refusal** |

Diagnostics (not absolution): tool-selection accuracy, argument precision and recall. One right
call plus an unwanted call is an exact failure, and the extra call counts as a wrong action.
"Right tool, wrong recipient" never reads as a near-success.

Empty results are three things in Needle and are logged apart: the model returned `[]`; the engine
withheld a call into `suppressed_calls` (floor or gate); `validation` flagged it. The primary
outcome treats all three as "nothing", because that is what the app receives; the breakdown is
shown so a refusal by the engine's rules is not credited to the model's understanding.

### 7.2 What the video reports, never as one number
Per app and per stratum, with counts: exact success on act items; correct non-action on each no-act
stratum; wrong-call rate; wrong-execution rate after policy; needless-refusal rate; technical
failures. The macro-average over strata is reported, but an easy app or stratum may not hide a
hard one.

### 7.3 Confidence: tested, not assumed
The vendor calls the score calibrated; the thread shows 1.0 on "My car crashed I need help" →
`play_music`. So:
- Reliability diagram per depth for returned call bundles: ten fixed equal-width bins, mean
  predicted confidence on the x axis, counts and intervals shown, empty bins empty. Whole-bundle
  correctness. `None` is never pooled with low confidence. No "off-topic probability" is invented
  from the confidence attached to an empty result.
- Risk-coverage curve: sweep the threshold on the stored outputs (no reruns), plot share executed
  against wrong executions.
- **Operating point chosen on calibration only**, per app and depth, with a frozen rule: maximise
  coverage subject to an observed wrong-execution ceiling of 5% with at least 20 accepted requests.
  The ceiling is OUR declared requirement, labelled as ours, not a safety standard. Where
  calibration offers no such point, that is the finding; the vendor's example threshold is not
  borrowed.
- On screen: "at this threshold the app executed n, got k wrong and deferred d", with the interval.
  Never "above 0.9 is safe". Three claims kept apart, as in jev-2: that the scores are numerically
  reliable, that they rank the mistakes, and that the gated app met the ceiling.
- LLM arms: the schema contract carries no confidence field (asking for one changes the task and the
  price). They are shown on the proposal and executed scoreboards without a gate, which is how a
  builder would deploy them; "no native confidence" is a designed state in the graphics.

### 7.4 Uncertainty
- Family-clustered, stratified, paired bootstrap (10,000 resamples of families, both phrasings
  together); McNemar exact on family-level outcomes as a cross-check.
- Zero observed errors: also report the one-sided 95% binomial bound (zero in 100 still allows
  about 3%).
- **Predeclared primary comparisons** (in the freeze): Needle-20 vs frontier LLM (a), Needle-20 vs
  K1, Needle-20 vs K0, Needle-20 S0 vs S1, and the S0-to-S1 gain for Needle vs for the LLM. Everything
  else is diagnostic, and a difference inside its interval is described as unresolved, never as a
  winner.
- Resolution stated up front: about ±4 points for an arm's overall rate, about ±6 per app, about ±12
  per stratum. The script may not rank anything finer than that.

## 8. Latency

- **Needle, K0, K1, hassil**: same Modal image and container, `cpu=(n, n)` so the soft limit cannot
  burst past the request (Modal's default soft limit is 16 cores above it), `--threads n`, CPU model
  from `/proc/cpuinfo` recorded. 20 warm-up requests discarded, then **serial**, timed in-process
  from request to parsed, validated decision. Also Needle's own `prefill_tps`, `decode_tps`,
  `peak_ram_mb`. Cold start measured separately over 10 fresh containers (process start to first
  decision). Reported at 1 and 4 cores, per depth, p50/p95/max, **call-producing and refusing
  requests separately** (a fast refusal is not fast automation).
- **LLM arms**: client in a Modal container in a fixed region, serial, one arm at a time, total time
  to a parsed decision plus time to first token; a network floor from 50 minimal requests to the
  same pinned host, reported beside. jev-2 measured its latency six at a time at a load of ~670 and
  rated it weak evidence; this does not repeat that.
- **What it is not**: rented-server numbers, not Raspberry Pi, microcontroller or energy figures,
  and depth sliced at runtime from the full archive does not demonstrate an 8 MB deployment. The
  frame on screen is an app decision (on-device milliseconds, no network needed, vs a round trip),
  not a race.
- Determinism: greedy decoding should make a repeat byte-identical. 30 preselected test families
  are re-run twice on every finalist arm; a difference is a finding, and the repeat is reported as
  stability, never as calibration.

## 9. Where it runs and what it costs

No model inference on Christo's Mac (ruled 2026-09-21); rented CPU on Modal is allowed and counts
against the ≤$5 per video together with paid API, one number (ruled the same day). Labour (writers,
annotators, the custodian, trigger and schema authors) is subscription quota or cc-zen and is not
in the $5.

| item | expected | pessimistic (list prices, no caching, 3,000 in / 100 out tokens) |
|---|---|---|
| LLM smoke tests (~18 hosts × 5) | $0.01 | $0.03 |
| LLM screen (200 items × ~15 candidates, schema contract) | $0.25 | $0.75 |
| LLM frontier (300 items × ~6 candidates × 2 contracts) | $0.35 | $1.10 |
| LLM final (600 test × 2 schemas × up to 3 arms, + repeats + schema diagnostics) | $0.45 | $1.50 |
| LLM canary (prefix completion) | $0.02 | $0.05 |
| Modal: Needle (depth curve, both schemas, diagnostics, forced row, latency) + baselines | $0.30 | $0.70 |
| Contingency: one failed stage re-run | $0.30 | - |
| **Total** | **~$1.7** | **~$4.1** |

Controls: a per-episode OpenRouter key with a provider-side limit of $4 (api-key-provisioning;
`OPEN.md` #5); a Modal workspace budget to match; **the worst-case cost of the final test is
reserved first** and development stops at $3.00 cumulative (then the screen shrinks to the ten
cheapest candidates; the contract variable is never the thing cut). The BUILD-LOG reports both axes
(dollars observed per stage, and pool points).

## 10. Order of work (the test is touched at step 9 and not before)

1. **Snapshot** sources and artifacts: HF revision, archive and runner hashes, wheel, `--help`,
   the MASSIVE/HWU/CLINC releases, OpenRouter endpoint records. Commit the manifest.
2. **Contracts**: write both apps' contracts, S0, then S1 from S0 by the guide checklist. Freeze the
   required-argument policy.
3. **Test custodian** (separate session): assemble families, write P2s, minimal edits, run the overlap
   scans and near-duplicate removal, two blind annotators plus adjudication, seal; publish the salted
   commitment. Configuration workers never see this material.
4. **Preflight on dev** (Modal): response shape, one-process-per-request, `--depth` actually selects
   the ladder, `--fail-input-overflow`, confidence present, what the engine does above five tools,
   the triggers path, cost metering; scorer mutation tests. **Known-answer control for our own
   harness**: run the vendor's six environment suites (`needle/environments/*`, 32 cases each)
   through OUR runner wrapper and scorer and reproduce the pass counts the vendor's
   `_harness.run_tests` gets on the same pinned engine (it is deterministic, issue #121). A mismatch
   is a harness bug to fix before anything else is believed; this uses vendor material only as a
   calibration of our apparatus, never as test data. Any failed preflight item changes the
   design here, in writing, before step 5.
5. **Baselines**: K0 trigger author (blind, schema-only), K1 indexing, extractor, hassil mapping; tune
   τ, μ, k on dev.
6. **Frontier selection** on the selection partition; write `FRONTIER.md`.
7. **Canary** on non-test material (partition gap, prefix completion).
8. **Calibration**: confidence operating points; then `FREEZE.md`: every arm, host, contract, prompt,
   schema, threshold, scorer, the primary comparisons, the display rule for examples (fixed-seed
   sample within each outcome category, denominators shown). Commit.
9. **Sealed run**: every arm, serial latency passes, repeats. Raw outputs only.
10. **Score once. Before any aggregate is read, read raw outputs end to end**: at least three items
    from every (arm × outcome) cell, plus every technical failure, to confirm each is classified as
    what it is (a misclassified failure yields a confident rate, not an error). Then audit
    anomalies without retuning, write `RESULTS.md`, reveal the salt, publish
    everything: requests, gold, contracts, schemas, outputs including failures, scorer, prompts,
    authoring provenance, manifests, timing, the billing ledger.

A publication gate sits after step 10: an unresolved gold, scorer or artifact-identity error blocks
the headline claim it touches. An inconclusive run is published as inconclusive.

## 11. What this cannot settle (goes on screen)

- One untuned model as shipped, two invented apps of five tools, English text, single turns. Not
  speech input, other languages, long conversations, multi-step agents, or the vendor's recommended
  fine-tuned deployment; nothing here refutes or confirms the vendor's TUNED claim.
- Model and engine together; which part of a result the network earns and which the engine's rules
  earn is not separable from outside.
- Not a safety certification for irreversible actions: an observed error rate on a balanced test is
  not the rate in real traffic, whose mix of request types we did not measure.
- Not proof of non-contamination (proprietary training data); only named overlap checks and the
  canary.
- A hosted LLM on a given day and host; the local artifacts are frozen far more completely than any
  API.
- Server CPU latency, not device latency.

## 12. Known weak points, stated so the build does not rediscover them

- **Agent-written P2s carry an LLM register.** Mitigated by two writer families and read through the
  difference in differences, not removed.
- **MASSIVE labels were not made for our schemas.** Every item is re-annotated; MASSIVE's intent is
  a hint, not gold.
- **The home app's real-phrasing pool is small** (184 supported test requests). Strata that run short
  are filled with labelled minimal edits, which are less natural.
- **"Cheapest frontier point within noise" depends on the pool**; the whole frontier is shown, and
  the second advanced arm (most accurate) guards against a lucky cheap pick.
- **The data lane has no stage for a measurement** (jev-2's open question in PROCESS-V2 §7): this
  design is held by `FREEZE.md` and the ledger, not by the pipeline state machine.

## 13. Changes after preflight (2026-09-22, configuration lead, session 2537465c, before step 5)

Each change comes from a preflight item that failed or showed something the design did not expect
(`production/needle3/preflight/PREFLIGHT.md`, which holds the evidence). The design's own rule
applies: "any failed preflight item changes the design here, in writing, before step 5".

- **D1. The depth curve is dropped.** `--depth N` has no observable effect in the pinned runner:
  depths 20 to 2 return the same calls as the default (within CPU-class noise), decode speed is flat
  across them, and `--depth 1` and `--depth 99` are accepted silently. §1 already says "if `--depth`
  misbehaves in preflight, the depth comparison is dropped, not faked", so no 4-bit rebuild or other
  substitute is used. Consequences: §1 "Depths" is depth 20 (the shipped archive, default) only;
  §7.3's reliability diagrams and operating points are for depth 20 only; §8 reports latency
  without a depth axis. What may be said on screen: that the documented flag changed nothing in our
  runs of this build; not that sub-20 depths are worse or better, which we did not measure.
- **D2. One CPU class for every Needle run.** Outputs are byte-deterministic within a CPU class and
  differ across the classes Modal serves (calls on 2-3 of 29 items, confidence on many). Every
  Needle run (dev, selection, calibration, sealed test, repeats, latency) asserts Intel family 6
  model 85 (AVX-512) inside each container and re-lands any chunk that starts on another class
  (`modal/needle_modal.py`, `require_cpu`). §8's determinism check is run on that class; a
  cross-class difference is a known property, reported once with its size, and never mixed into a
  headline number. The known-answer control was re-run on that class and matches the vendor harness
  exactly.
- **D3. Above five tools, no retrieval was observed.** Every tool of 6, 10 and 20 stays reachable
  and wall time grows with the count, so the tool-count diagnostic (§5.3) is read as "all tools in
  the prefix" and never as retrieval misses. `--tool-index` stays unused (the vendor-shipped
  configuration).
- **D4. Engine runtime failures are technical failures, and both counts are shown.** Out-of-range
  values make the engine return `success: false`, `error_code: truncated` ("tool call truncated:
  token budget exhausted") rather than an empty call list. §7.1's rule stands: in the proposal
  scoreboard that is a technical failure, never a refusal. The vendor harness counts the same
  response as a correct refusal (3 of its 192 cases), so wherever the video reports a no-act
  stratum, the count of `truncated` responses in it is shown beside the correct non-actions, and
  the executed scoreboard notes that such a request executes nothing.
- **D5. The LLM pool is narrowed by a fixed, outcome-blind rule (before any LLM call).** §4.2's pool
  (ZDR host, tools or strict schema, at most $0.50/M in and $2/M out) is 129 models on 2026-09-22, not
  the ~15 §9 priced; screening all of them would cost about $5 at list price. Rule, applied to the
  snapshot `production/needle3/snapshot/openrouter/` and published with the list it produced
  (`pool_rule_p1p4.json`): (P1) no `:free` variants; (P2) no variants built for another job
  (vision-language, code, translation, finance/medical, moderation, speech, role-play fine-tunes,
  extraction-only, "thinking" variants, preview/experimental); (P3) the pinned host must accept
  the strict-schema contract or native tools with `tool_choice: auto`; (P4) host uptime over the last
  30 minutes at least 90% where reported. That leaves 88. (P5) The screen then takes candidates in
  ascending projected cost per call (1,500 prompt + 60 completion tokens at list price, uncached)
  until the projected screen spend reaches **$0.75**, the pessimistic screen line of §9. Candidates
  above that line are named in FRONTIER.md as not screened; a claim about "the cheap-LLM frontier"
  is scoped to the screened range. A candidate without a strict-schema host is screened on the native
  contract. The named-claim model (DeepSeek V4 Flash, April snapshot) falls inside the screened range.
- **D6. The selection-side accuracy axis pools the act strata (before any LLM or baseline score was read).**
  The config partitions come from the same crowd corpora as the test, and desk requests there nearly always
  carry a time or date to resolve, so desk act items fall almost entirely in A3 (selection: A1 6, A2 3, A3
  26). A macro over six strata would weight three items like seventy-three. For the frontier (§4.2 step 4)
  and for tuning the keyword baselines (§4.3) the axis is therefore: per app, one half the accuracy on all act
  items pooled and one half the mean over N1, N2 and N3, then the mean over the two apps. This keeps the
  design's balance of act against no-act (three strata each). **Corrected the same day, before any LLM score
  was read:** the first version averaged four cells (act pooled, N1, N2, N3), which weights doing nothing 3:1;
  the always-decline control scored 0.75 under it and the keyword tuning then chose settings that refuse
  everything, which is how the defect was caught (`baselines/DEV-RESULTS.json` history, commit log). Per-stratum numbers are still reported. The
  sealed test's balanced strata (25 families each) are unaffected; this concerns only the config side.
- **D7. The frontier stage takes candidates within 10 points of the screen's best, not 5 (made AFTER seeing the
  screen; recorded as such).** On the 200 screen items the D6 axis carries a 95% interval of roughly ±6
  points per candidate, so a 5-point window is narrower than the noise that decides membership, and the
  screen ran one contract per model while §4.2 wants each model judged on its better contract. The stage
  therefore takes every candidate undominated at the screen, plus any within 10 points of the best, plus the
  named-claim model (§4.2 step 6), each on both contracts where its host supports both, on the whole
  selection partition. This only adds candidates to the stricter stage; the pick rule (§4.2 step 5) is
  unchanged, and FRONTIER.md reports what the 5-point rule would have picked beside what this one picks.
- **D8. K1's lexical bank is rebuilt as 200 ACT examples per app, labelled by tool through a declared
  intent-to-tool table (after seeing K1's first dev numbers; recorded as such).** The first bank was drawn with
  the same no-act-heavy mix as the other config partitions (the configuration lead's choice, not §3.4's), so it
  held only ~40 act examples per app; indexed with a "none" class it was 78% "none" and refused most act items
  (dev, home: 41 needless refusals against 12 correct actions), and indexed on its act items alone it had too few
  examples to route (dev macro 0.53, below the schema-only K0's 0.62). Either way a straw man, which §4.3 forbids;
  §4.3 means "an engineer with a few hundred labelled examples" of the app's actions. The rebuilt bank draws 200
  rows per app from MASSIVE en-US train rows of the apps' action intents that the custodian's whole-supply scan
  marked clean and that no other config partition uses, labelled with the tool the intent names
  (`baselines/k1_bank/INTENT-TO-TOOL.json`, written before scoring). The label only routes: arguments come from
  the shared extractor, and refusal from τ/μ, exactly as in K0. The first bank's two indexings are reported on dev
  beside it, never as the arm.

