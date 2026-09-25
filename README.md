# Needle 3 tool-calling test

This repository holds everything behind our test of Needle 3, Cactus Compute's 121M-parameter tool-calling
model: the code, the 600 test requests, every system's raw answers, the scoring and the results. We tested it
because it is sold as a small model an app can ship to turn what a user says into function calls, and we wanted
to know how often it picks the right call, how often it correctly does nothing, and how that compares with a
cheap hosted LLM and with keyword matching. The video is here: TO-FILL-ON-PUBLISH. We publish the material so
anyone, Cactus included, can check the numbers or rerun them.

The headline, from `RESULTS.md` §0: on the 600 sealed requests, Needle 3 scores 0.545 [0.505, 0.585] on exact
correctness, a hosted DeepSeek V4 Flash scores 0.775 [0.740, 0.810], and a keyword baseline built from the tool
descriptions alone scores 0.555. Always declining scores 0.500 by construction.

## What was tested

Two invented apps with five tools each:

- **home**: `set_lights_power`, `set_lights_brightness`, `set_lights_color`, `control_vacuum`, `set_plug_power`
- **desk**: `set_alarm`, `remove_alarm`, `add_list_item`, `remove_list_item`, `create_reminder`

The 600 test requests are 300 families, 25 per (app × stratum). Strata A1 to A3 are requests the app should act
on, N1 to N3 are requests it should not (unsupported, negated, quoted, hypothetical and similar). Each family has
two phrasings: P1 is a real request from a public intent dataset (MASSIVE, HWU64, CLINC150), sometimes minimally
edited, and P2 is a new phrasing written for this test so it cannot have been seen in training.

Every system got the same tool list. S1 is a tool list written following Cactus's guide; S0 is a plainer one. The
systems scored are:

| arm | what it is |
|---|---|
| needle | Needle 3, pinned build, one fresh process per request on one rented CPU class |
| llm-a | `deepseek/deepseek-v4-flash-0731` via OpenRouter, pinned to the host Sail Research, strict JSON schema |
| llm-named | `deepseek/deepseek-v4-flash` via OpenRouter, pinned to OpenInference, native tool calling |
| K0 | BM25 over the tool descriptions plus a rule-based argument extractor |
| K1 | BM25 over a bank of labelled example requests plus the same extractor |
| hassil | Home Assistant's own English intent templates (home app only) |
| always-decline | returns no call for anything |

A further 37 requests (band F) are requests people posted in the Hacker News thread about Needle 3, each linked to
its comment. They are scored one by one and never pooled into a rate. 128 diagnostic requests vary one thing at a
time (tool count, renamed tools, units, the vendor's own tool list and so on).

## The scoring contract

The test was designed before any test request was run, and the design was frozen in writing:

- `DESIGN.md`: the measurement design, with the questions it has to answer.
- `FREEZE.md` and `FREEZE-ADDENDUM.md`: every pin, arm configuration, hash, statistic and budget rule, committed
  before the sealed requests were opened.
- `contracts/CONTRACT.md` (v1.1): what counts as the correct call for each kind of request.
- `RESULTS.md`: the single scoring run, with every number copied from `results/SCORES.json`.

These documents are published exactly as written during the work. They mention internal session ids, a video
channel and folders on our machine, and some sentences describe plans that later changed (RESULTS.md says nothing
would be published; that was decided afterwards). Where a document names `~/temp/m37-needle3-sealed/sealed-v2/`,
the files are in `sealed-v2/` here.

## Checking the sealed-test commitment

Before any system saw a test request, the test's custodian sealed the requests, the gold answers and the record of
how they were built, and committed to them with a salted hash (`custodian/COMMITMENT.md`, committed to our working
repository on 2026-09-22). The commitment is `sha256(salt + "\n" + manifest)`, where the manifest lists every sealed
file as `<sha256>  <bytes>  <path>`, one per line. The salts and manifests were kept private until the results were
final and are now in `custodian/reveal/`.

To check the commitment that the scored test used (v2), run from the repository root:

```sh
(printf '%s\n' "$(cat custodian/reveal/salt-v2.hex)"; cat custodian/reveal/MANIFEST.sealed-v2.txt) | shasum -a 256
```

It must print `f73c32e4807e793ab0be3bd1a943a01f4f9239a79fae1094ac9dda0e7ced55fe`, the v2 commitment in
`custodian/COMMITMENT.md`. v1, the first seal, was replaced before any system ran because the correctness contract
changed; its salt and manifest are revealed too, and the same command with `salt.hex` and `MANIFEST.sealed.txt`
must print `96d2bc70bbf917bbfdf1d2da8d1044a278fd4b8caf3f7c1596a96c3a2cb26367`.

`python3 custodian/reveal/verify_commitment.py` checks both commitments and also checks every file in `sealed-v2/`
(the request files, the gold-answer files and `SEALED-RECORD-v2.md`) against its own line in the v2 manifest. The
other 172 lines of that manifest name the custodian's working files (writer prompts, annotation passes, overlap
scans), which are not published; for those, the manifest records what was sealed.


## Layout

| path | contents |
|---|---|
| `requests/` | the test, diagnostic and band F requests, one JSON line each, with dataset, source id and licence per item |
| `sealed-v2/` | the sealed files as scored: request files (`id, app, text` only, what the runners read) and key files with the gold answers |
| `contracts/` | the correctness contract, the S0 and S1 tool lists per app, the diagnostic variants, `mapping.py` (normalisation) |
| `harness/` | `score.py` (proposal scoreboard), `execute.py` (what an app would execute), `llm_arm.py` (the hosted LLM client), and their tests |
| `modal/` | the Modal image and driver that runs Needle 3 (`needle_modal.py`) |
| `runs/sealed/` | the run script, spec builder, inputs, every raw output (`out/`), run logs and the spend ledger |
| `runs/needle_config/` | Needle's outputs on the configuration partitions, used for calibration |
| `results/` | `score_test.py`, `SCORES.json`, `EXAMPLES.json`, the audit sample read before scoring |
| `calibration/` | how Needle's confidence threshold was chosen (no threshold met the ceiling) and the hash list |
| `baselines/` | K0, K1 and hassil: code, tuned parameters, the example bank |
| `partitions/` | the dev, selection, calibration and lexical-bank partitions, built only from non-test data |
| `frontier/`, `FRONTIER.md` | the screen of cheap hosted models that chose llm-a, with every screened model's raw answers |
| `preflight/` | checks run on the engine before configuring anything (determinism, known-answer controls) |
| `canary/` | the contamination check (crowd phrasings against fresh ones) |
| `custodian/` | the sealing record, overlap scans, and in `reveal/` the salts and manifests behind the commitment |
| `snapshot/` | pinned hashes of the Needle 3 files, the OpenRouter endpoint records on the day, the engine's `--help` |
| `sources/` | the MASSIVE and CLINC150 files the configuration partitions were drawn from |
| `docs/PATH-REWRITES.md` | the lines changed for publication, and how to check the frozen hashes |

## Reproducing the scoring

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/). This recomputes every number in `RESULTS.md` from the
stored raw outputs, with no model calls and no cost:

```sh
uv run --no-project --with numpy --with jsonschema==4.26.0 python results/score_test.py
```

It writes `results/SCORES.json`, `results/EXAMPLES.json` and prints the tables. Set `NEEDLE3_RESULTS_DIR` to write
somewhere else and compare. Every point estimate and every drawn example reproduces exactly. The bootstrap
intervals can differ in the third decimal (by at most 0.0033 in our reruns) because the family resampling iterates
a Python set, whose order depends on the interpreter's hash seed. `PYTHONHASHSEED=0` makes a rerun repeatable,
though the published intervals came from an unseeded run.

The scorer's own tests:

```sh
uv run --no-project --with jsonschema==4.26.0 python harness/test_score.py
uv run --no-project --with jsonschema==4.26.0 python harness/test_execute.py
```

## Rerunning the models

Rerunning the arms costs money and needs your own accounts. Our whole run, including configuration, diagnostics,
repeats and latency, came to $2.56 (OpenRouter $0.99, Modal $1.57).

**Needle 3.** The engine is pinned to Hugging Face `Cactus-Compute/needle3` at revision
`b274efcb211a9eef48c9a88da4b43bd569696a39` and GitHub `cactus-compute/needle` at `f189b23`, engine 3.0.1.
`modal/needle_modal.py` builds a Modal image that downloads exactly those files and checks their hashes (listed in
`FREEZE.md` §2 and `snapshot/`). The weights are not in this repository; the image fetches them from Hugging Face.
Each request runs as its own process:

```sh
needle --model needle3.cact --tools <tools>.json [--system "date: 2026-06-10 Wed 14:30; locale: en-US"] \
       --threads 1 --fail-input-overflow --prompt "<request>"
```

The fact line goes to the desk app only. `--max` is left at the engine's default of 512 response tokens, and
`--depth`, `--forced` and `--tool-index` are not used. Some responses stop with `truncated` at that limit; the
scorer counts those as technical failures, not refusals (FREEZE.md §9, D4).

Needle's output differs between CPU types. On Modal we found at least four classes, and changing class changed the
calls on 2 to 3 of 29 items. Every scored Needle output comes from `GenuineIntel fam 6 model 85`; the driver checks
this inside each container and re-runs any batch that starts on another class (`preflight/PREFLIGHT.md` item 5). To rerun,
set up Modal (`pip install modal`, `modal token new`), then:

```sh
uv run runs/sealed/make_specs.py                 # builds runs/sealed/inputs and specs from sealed-v2/
cd modal && uv run needle_modal.py native --in ../runs/sealed/specs/needle_S1_home_test.json \
    --out ../runs/sealed/out/needle/needle_S1_home_test.json --chunks 20
```

**The hosted LLM arms** are called through OpenRouter with the host pinned and fallbacks off, temperature 0,
reasoning disabled, a 600-token cap, and `require_parameters: true` (FREEZE.md §3). Every call stores the sha256 of
its request body, so a rebuilt request can be checked against ours. Export your own key first:

```sh
export OPENROUTER_API_KEY=...
uv run harness/llm_arm.py --model deepseek/deepseek-v4-flash-0731 --host "Sail Research" --contract schema \
    --schema S1-home --items runs/sealed/inputs/test-home.jsonl --out /tmp/llm-a-S1-home.jsonl --reasoning off
```

Hosts and their quantisation change over time, so a rerun on a later day may not be served by the same weights.

**The keyword arms and hassil** run locally with no model. hassil needs Home Assistant's intent templates at the
pinned commit (`baselines/hassil/PINS.md`):

```sh
git clone https://github.com/OHF-Voice/intents.git /tmp/needle3-intents
git -C /tmp/needle3-intents checkout f8cdbb0b6601cde140b9a40c297363c6137d219d
NEEDLE3_INTENTS_DIR=/tmp/needle3-intents uv run runs/sealed/baselines_sealed.py
```

`runs/sealed/run_sealed.sh` holds the exact order of every stage we ran, including the budget gate
(`runs/sealed/spend.py` reads Modal billing and the OpenRouter key's spend counter).

## How scoring works

A system's answer is the list of calls it returned. It is correct when that list, normalised by
`contracts/mapping.py`, equals an accepted gold answer exactly: same tools, same arguments, order ignored,
duplicates counted. Returning no call is correct only where the gold is no call. No LLM judges anything.

Each answer is scored as one of five outcomes: correct action, correct non-action, wrong call, needless refusal, or
technical failure (a crash, timeout, unparseable output or engine error). The statistic of record is exact
correctness averaged over the twelve app × stratum cells. Intervals come from a family-level bootstrap (10,000
resamples, seed 20260922) with a sign test as a cross-check.

For Needle, the engine withholds calls it flags as ungrounded or negated; we score what the app receives after that
filter, and report the unfiltered reading separately. A second scoreboard (`harness/execute.py`) scores what an app
would actually execute after checking each call against its tool's JSON schema and, for Needle, a confidence
threshold. FREEZE.md §4 to §7 give the full rules.

## Licences

- **Code** (everything under `harness/`, `modal/`, `runs/`, `results/`, `baselines/`, `contracts/`,
  `calibration/`, `partitions/`, `frontier/`, `canary/`, `preflight/` that is a program): MIT, copyright 9592
  Solutions UG (haftungsbeschränkt). See `LICENSE`.
- **Our data and writing** (the P2 requests we wrote, gold labels, tool lists, results, documents): CC BY 4.0,
  9592 Solutions UG (haftungsbeschränkt).
- **Third-party requests** keep their own licences, marked per item in `requests/`: MASSIVE 1.1 (CC BY 4.0,
  Amazon), HWU64 (CC BY 4.0) and CLINC150 (CC BY 3.0). Edited items are adaptations under the same terms.
- **Band F** quotes short requests from public Hacker News comments and links each one to its source. They are not
  relicensed.
- **Needle 3** (weights, runner and Python package) is Cactus Compute's, under Apache-2.0, and is not included here.

Attribution, sources and licence links: `LICENSE-DATA.md`.
