# Needle 3 preflight (DESIGN §10 step 4)

Run 2026-09-22 by the configuration lead (session 2537465c) on Modal (app `m37-needle3`, image in
`../modal/needle_modal.py`, artifacts pinned in `../snapshot/MANIFEST.md`). Inputs were vendor
material (the six environment suites, used only as a calibration of our apparatus) and 48 MASSIVE
**train** utterances (`pf_prompts.json`) plus ten hand-written probes. No test material. Every raw
engine response is kept in `out/` and the `kac_*` files.

## Verdict per item

| # | item | result | consequence |
|---|---|---|---|
| 1 | Response shape | **pass**. One JSON envelope per call on stdout, the fields llms.txt lists (`type, success, error, error_code, reason, function_calls, suppressed_calls, reasoning, confidence, prefill_tps, decode_tps, peak_ram_mb, validation`). The native runner emits `validation` itself; it is not only a Python-side annotation. | scorer reads `function_calls`, withholds a call flagged by `validation` (as the vendor harness does), logs all three kinds of empty |
| 2 | One process per request | **pass**. Each item runs as a fresh `needle --prompt` process; on the same CPU class its outputs equal the Python package's reset-per-case outputs byte for byte (item 9) | kept as designed |
| 3 | `--depth` selects the ladder | **FAIL**. Depths 20, 16, 8, 4, 2 and 3 return the same calls as the default on 27-29 of 29 items per app (the residue is CPU-class noise, item 5); median decode speed is flat (111, 112, 115, 94, 127, 123 tok/s) where a 2-of-20-block slice should run several times faster; `--depth 1` and `--depth 99` are accepted with no error and change nothing (`out/depth_*`, `out/depthbad*`). The flag is parsed and has no observable effect in this runner build. | **depth curve dropped** (DESIGN change D1). No substitute, as the design requires. |
| 4 | `--fail-input-overflow` | **pass**. A 79k-character turn: with the flag, `error_code: context_overflow` ("17514 tokens, 6924 available"); without it, the turn is silently trimmed and the output is unrelated to the request (`out/overflow_big_*`). The S1 home prefix therefore takes about 1,268 of the 8,192 positions. | kept on for every Needle run |
| 5 | Determinism | **conditional pass**. Within one container, three repeats of 24 desk items are byte-identical (calls and confidence). Across CPU classes they are not: Modal serves at least four (Intel fam 6 model 85 AVX-512; Intel model 106; AMD fam 175 models 1 and 17, AVX2), and runs on different classes changed the calls on 2-3 of 29 items and the confidence on up to half (`out/det_desk.json`, `threads*`, `depth_def`). | **CPU class pinned** (DESIGN change D2): every Needle run asserts Intel fam 6 model 85 per container and re-lands a chunk that starts elsewhere |
| 6 | Confidence present | **pass** on every successful call (0.1569 to 1.0 in the vendor suites); `0.0` on a context overflow | as designed |
| 7 | Above five tools | **observed, no retrieval**. With 6, 10 and 20 tools (S1 plus distractors) every tool stays reachable (calls to tools #10, #13 and #15 of 20), no field or stderr line mentions retrieval, and median wall time grows with the tool count (home 6.2 s at 5 tools, 6.6 at 6, 9.4 at 10, 15.9 at 20). That is consistent with every tool entering the prefix (the porting guide) and not with a top-5 retrieval head (the Python docs); the runner's own string says retrieval needs `--tool-index`, which we do not pass. | DESIGN change D3: the tool-count diagnostic runs as designed; attribution is stated as "all tools in the prefix, no retrieval observed" |
| 8 | Triggers path | **pass, works as documented**. A trigger on `set_lights_power` forces a call on "are the lights on or off?" (a question) and on "my friend said turn the lights off" (reported speech), and three calls on "lights on and make coffee"; a negated request is still withheld into `suppressed_calls` (`out/triggers_home.json`) | diagnostic arm as designed |
| 9 | **Known-answer control** | **pass**. The six vendor suites (192 cases) through OUR runner wrapper reproduce the vendor harness exactly on the pinned CPU class: 172/192 passes both ways, identical calls on 192/192, identical confidence on 192/192 (`kac_compare_pinned.py`). Through OUR scorer: 169/192, agreeing on 189/192; the three differences are the finding in item 10, a declared rule, not a harness bug (`kac_ourscorer_pinned.py`). | harness and scorer believed |
| 10 | Technical failures | **finding**. Three vendor cases the vendor harness counts as correct refusals of out-of-range values ("get the oven up to 300 degrees", "turn the fridge down to 3 degrees", "log my weight as 500 kg") are engine runtime failures: `success: false`, `error: "tool call truncated: token budget exhausted"`, `reason: runtime_failure`, with a reasoning line that names the out-of-range value. The bounded grammar does not refuse the value; decoding runs out of budget. The same failure appears on our own S1 ("turn off the kitchen lights" → reasoning "'turn off' -> brightness 0" → truncated). | DESIGN change D4 records how both counts are reported |
| 11 | Scorer mutation tests | **pass**: 54 mutants of the canonical examples and 515 of the vendor suites' positive and parallel cases (swapped arguments, changed units and am/pm, extra calls, dropped fields, flipped polarity) all score wrong; every unmutated control scores right; a technical failure is never a refusal; the declared default equivalences hold. The test can fail: a scorer that ignores arguments fails 308 of them (`../harness/test_score.py`). | scorer frozen for dev use |
| 12 | Cost metering | **pass**. Modal: per-app cost read back with `../modal/modal_spend.py` (billing report API, tag `episode=needle3`). OpenRouter: `usage.cost` on three calls equals `/generation`'s `total_cost` to the digit (Sail Research ×2, Novita), and the key's own usage counter moves with the sum. | |

## Numbers for planning

- Wall time per Needle request on one Intel model-85 core, fresh process: median 5.6-6.2 s with 5
  tools (the tool prefix is re-prefilled every time at about 100 tok/s under gVisor). Roughly
  $0.0001 of CPU per request; the full sealed run (~3,000 Needle requests) is about 5 core-hours.
- Modal spend to the end of preflight: **$0.198** (59 app runs including image builds, retries onto
  the pinned CPU class and this whole grid).

## Things seen in passing (not preflight items; not tuned on)

- "start a 25 minute timer" under the 6-tool desk variant returned `start_timer(duration_seconds: 25)`,
  the HN thread's number-copying failure (viccis), on a config-side probe.
- "set the heating to 21 degrees" under S1 home (no thermostat) returned
  `set_lights_brightness(living room, 21)`, and "feed the cat two portions" returned a vacuum start.
