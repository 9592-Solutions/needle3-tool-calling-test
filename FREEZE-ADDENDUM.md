# Needle 3: FREEZE addendum (FREEZE.md §12), before step 9

Written 2026-09-22 by the step 9/10 worker (session 30002c39, Opus 5) for m37-lead, after FREEZE.md was accepted
(ea88a7c0) and **before any sealed input was opened**: no request file, key file or salt under
`~/temp/m37-needle3-sealed/` or `~/temp/m37-needle3-salt/` had been read, listed by content or counted when this
file was committed. The commit that adds this file precedes every file under `runs/sealed/out/`, `runs/sealed/inputs/`,
`runs/sealed/specs/` and `results/` other than the three scripts named below; `git log` is the check. FREEZE.md binds
everything here; where this file adds a choice FREEZE left open, the choice is declared below, with its reason, before
any sealed number exists.

## 1. Files, hashed

| file | role | sha256 |
|---|---|---|
| `runs/sealed/run_sealed.sh` | the exact commands for every tier (FREEZE §12.1): `prep`, `tier1`, `latency`, `repeats`, `diag` | `231c24326fbe91bfbdc1be161c677598bf01fc566f004178f69ddef6f3da4848` |
| `runs/sealed/make_specs.py` | reads the three request files only (asserts they carry `id, app, text` and nothing else), writes the runner inputs | `15d01c619e7c619ac1ac8329fbdd17c74b3eef506690e72c6f71116709de709f` |
| `runs/sealed/baselines_sealed.py` | K0, K1, K1-firstbank, K1-firstbank-none, hassil on test and band F, with the frozen τ/μ/k from `DEV-RESULTS.json` | `3b8e942ca35a8e95eae908fd07a3fe03e127434f68dcafccb6b97e1f57d8bd5d` |
| `runs/sealed/latency_modal.py` | latency (FREEZE §12.2): hard `cpu=(n, n)` for Needle and the baselines, LLM client in Modal region `us-east` | `0bebfd3a14e37e39c8aa145e0a1687a3e3ec43d06435dc7346b727376fd0c302` |
| `runs/sealed/llm_contract.py` | contract-in-prompt diagnostic: the frozen `harness/llm_arm.py`, system paragraph + blank line + CONTRACT text | `e0aabb2dc8c2d1d97866e47ffbeebb12619ff70e9794379895da7b4c29b0543d` |
| `runs/sealed/contract_prompt_home.txt` | CONTRACT.md v1.1 §1 and §2 verbatim (FREEZE §12.3), nothing else | `6590217811c8f1e4ee5f5c207ca32293d95a1741413298252e6921c2035c9a3b` |
| `runs/sealed/contract_prompt_desk.txt` | CONTRACT.md v1.1 §1 and §3 verbatim | `2acfd8f25c9c42aa93dbc31df0716069cb5a11128cea3ae630ccdbefb9412cb7` |
| resulting system text, home, schema contract (llm-a) | `SYSTEM_SCHEMA + "\n\n" + contract_prompt_home.txt` | `2afc516dd2a3495d97e745da02b6ae2679b9dc1b5b22dd2532c72e381f12d151` |
| resulting system text, home, native contract (llm-named) | `SYSTEM_NATIVE + "\n\n" + …home.txt` | `583519c0dae19194fc7219c8c89bb177be1b6378a6abaeeab52f9e895e1404ad` |
| resulting system text, desk, schema | (the fact line and tools follow, placed by `llm_arm.build_body` as in every call) | `b391ba03ba04441ff06eab97c21f89072255fb5ef0850fd2a14b8f73fa69b94c` |
| resulting system text, desk, native | | `e71b022d665fd5f40002231ae73d2531d013742586ce96193537ebbc3e44f237` |
| `runs/sealed/spend.py` | the budget gate: OpenRouter key counter + Modal billing since 2026-09-22; refuses a stage when observed + worst > $4.75 | `6d86fa5f3df782d148ee787a17d14d127ac335eb8a958286908a84cf609b6f40` |
| `runs/sealed/costs.py` | each stage's worst case at FREEZE §10 rates, from input line counts | `02984dd4ef8fc7662f5baf3bac399511cea533de1100e6bfec1cc78fa4aa60bc` |
| `contracts/variants/vendor-smart_home.json` | V-VENDOR tools: the vendor's `smart_home` TOOLS exactly as the preflight known-answer control sent them (`preflight/kac_in_pinned_smart_home.json`), wrapped in the OpenAI form for the LLM arms | `f7ccfcd037f3d19a0e156afe526b915e9c4bc73bfeaec37ecffc7f7cf6cdb5a7` |
| **`results/score_test.py`** | the single scoring (FREEZE §12.4) | **`a61e69a876f541f09be11ca09698c678d087898e46cffc6b8527d3927f219903`** |
| `results/audit_dump.py` | the raw-output reading sample written BEFORE score_test runs; prints no aggregate | `4a1cee363bdab9e71804598e8416d25c4d87384775d61739cda05efd4e3a9ac9` |
| `results/smoke_score_test.py` | the config-side smoke test of score_test (§4) | `431d715dc4c4dceacc436795344becfe4db4073e68a737ec0d8cea9302f57b83` |

Unchanged and re-verified at this commit: `modal/needle_modal.py` `992199b5…`, `harness/llm_arm.py` `a3bfa5ca…`,
`harness/score.py` `0c3a7d6f…`, `harness/execute.py` `67a1fb74…` (FREEZE §2-§4). The Needle scored passes, the
anchors and the repeats all go through `needle_modal.py native` unchanged; `latency_modal.py` imports only its image
and constants.

## 2. Choices FREEZE left open, declared here

1. **Which items each diagnostic runs on.** The request files carry no diagnostic assignment and the keys are not
   read before step 10, so assignment cannot come from them. Every anchor of an app runs under every variant of that
   app. V-REL and V-ROOMREQ run on every home item of test and of the anchors (the custodian's hand-over says the home
   keys carry their gold). The scorer scores a variant on the items whose key carries that variant's gold (V-REL,
   V-ROOMREQ, V-VENDOR, V-TIMER, V-COUNT-6/10/20), and on all anchors with main gold for V-RENAME, V-DISPATCH,
   V-TRIGGERS, V-FORCED and contract-in-prompt (CONTRACT §4). If the anchor keys turn out to carry a per-diagnostic
   assignment, RESULTS reports the assigned subset beside the all-anchor number.
2. **A reference run, S1 on the anchors** (`V-BASE`), for Needle and both LLM arms, fired first among the diagnostics.
   Every diagnostic varies one thing against S1 on the same items, and no S1 output on the anchors existed. It is
   gated like every later stage.
3. **V-VENDOR.** Needle gets the vendor's own system text (`needle.environments.smart_home.SYSTEM`) behind the
   package's date prefix, with our fixed date: `date: 2026-06-10 Wed 14:30; Map each explicit supported home action…`,
   because "vendor home turf" is the maker's best case and that is how the vendor harness calls it. The LLM arms get
   the vendor tools with their own frozen system paragraph, since llm_arm.py cannot take another; the asymmetry is
   reported beside the numbers.
4. **V-TRIGGERS.** Each K0 phrase from `k0/triggers_S1.json` becomes one regex, the phrase as a literal between word
   boundaries (`\b…\b`; regex metacharacters escaped), attached as `triggers` to the S1 tool of that name; the engine
   matches triggers case-insensitively (vendor guide). Run on the anchors and on the whole test (the design asks for
   the trigger arm to be scored on negations, quotations and two-action items, which are test strata).
5. **Contract in the prompt.** Only CONTRACT text: §1 (rules for both apps) and the app's own section, verbatim. §0 is
   left out because it describes gold in canonical action names, which differ from the tool names the arm sees; the
   variant section §4 is left out because it describes schemas the arm is not given. Run on the anchors, S1.
6. **Needle technical failures** also include a non-zero exit and a timeout, whatever stdout holds (FREEZE §2 lists
   them). Needle outputs are accepted only from Intel fam 6 model 85; the scorer stops if any item ran elsewhere.
7. **Unserved LLM items** (FREEZE §3): an item whose records hold no HTTP 200 from the pinned host, and whose every
   attempt was a 429 or was served by another host, is unserved. Any other non-200 end (a 4xx, an exception) is a
   technical failure. Up to three re-passes, each only while unserved items remain.
8. **Repeats.** Needle's two repeats are two separate driver invocations, so they run in fresh containers. The
   identical-output rate compares the main S1 output and both repeats.
9. **Latency.** Warm-up = the first 20 of the app's test items in id order (discarded; they are then timed again
   among the 300). Cold start = 10 fresh single-use containers per app at one core, each timing its first request.
   The LLM client container runs in Modal region `us-east` (the config-side smoke landed on Azure us-east). The
   baselines are timed in the same container as Needle, after it.
10. **Primary comparisons.** Comparison 4 is needle S1 minus needle S0; comparison 5 is (needle S1 − S0) minus
    (llm-a S1 − S0). Holm is applied to the five sign-test p-values (the only p-values computed). Every bootstrap
    uses a fresh `default_rng(20260922)`; paired comparisons keep only items scored for every arm in them (an unserved
    LLM item leaves that comparison). Per-app intervals are also computed for the five comparisons.
11. **Canary on test**: per family, P1 and P2 both scored; the gap acc(P1) − acc(P2) and its difference from K0's
    gap, bootstrapped by family within (app × stratum) cells, same seed.
12. **Key adapter.** The key files' field names were unknown. `score_test.py` reads `id, app, gold, stratum` and
    takes family and phrasing from a declared list of aliases; if a record does not resolve, it stops and names the
    fields. A fix to that alias list after the keys are opened is a field-name fix, committed separately and reported
    in RESULTS; it changes no rule.
13. **Budget.** `run_sealed.sh` gates each stage after tier 1 with `spend.py --gate <worst>`, worst from `costs.py`
    (FREEZE §10 rates; tool-count multipliers 6: 1.2, 10: 1.6, 20: 2.6; contract-in-prompt calls scaled by their
    extra prompt length at 3.5 characters per token). Observed spend = the OpenRouter key's own counter + the Modal
    billing report for app `m37-needle3` since 2026-09-22. Every gate decision lands in `runs/sealed/logs/gates.log`
    and `runs/sealed/spend-ledger.jsonl`.

## 3. Order of the sealed run

`prep` → `tier1` (Needle S0/S1 on test and S1 on band F, both LLM arms likewise, the local arms; always-decline needs
no run) → `latency` (gate) → `repeats` (gate) → `diag`: V-BASE, then FREEZE §8's order: V-REL, V-ROOMREQ,
V-COUNT-6/10/20, V-RENAME, V-DISPATCH, V-TIMER-S/U, V-VENDOR, V-TRIGGERS, contract-in-prompt, V-FORCED, each gated.
Nothing is scored during the run. Step 10 then: open the keys, `audit_dump.py`, read it end to end, `score_test.py`
once.

## 4. Smoke tests run before this commit (config-side data only)

- `results/smoke_score_test.py`: a fake sealed world built from the selection partition, the stored config Needle
  outputs and the two arms' frontier-stage outputs; score_test ran end to end and its Needle S1 accuracy equals an
  independent recount. `audit_dump.py` ran on the same world.
- `latency_modal.py` on 2-3 config items: desk at `cpu=(4, 4)` (landed on model 85 at the second try; `ncpu 4`),
  home at one core with hassil loading from the pinned clone in the image, and the llm-a client (Azure us-east,
  served by Sail Research, 2 floor requests). Spend: a few tenths of a cent, inside the next gate reading.
