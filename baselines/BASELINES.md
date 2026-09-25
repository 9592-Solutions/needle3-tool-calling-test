# Needle 3: the non-generative baselines (DESIGN §4.3, §10 step 5)

Built and tuned 2026-09-22 by the configuration lead (session 2537465c) on the DEV partition only (home 158,
desk 167 labelled items after ambiguous ones are excluded). No test item was read. Accuracy axis: DESIGN §13 D6
(per app, half act accuracy and half the mean over N1/N2/N3; then the mean over apps). Raw results:
`baselines/DEV-RESULTS.json`, `baselines/DEV-OUTCOMES.json`, `baselines/hassil/DEV-dev.json`, `baselines/nn/`.

## Result on dev

| arm | data budget | D6 accuracy | micro | tuned (only these) |
|---|---|---|---|---|
| **K0-S1** | the frozen S1 schema only (blind author) | 0.619 | 0.625 | k=1, μ=1, τ at the 0.3 quantile of dev top-1 scores (home 1.46, desk 1.72) |
| K0-S0 | the frozen S0 schema only | 0.604 | 0.674 | k=1, μ=1, τ at the 0.5 quantile of dev top-1 scores (home 1.89, desk 2.10) |
| **K1-S1** | labelled act examples: home 173, desk 237 (D8) | 0.529 | 0.532 | k=1, μ=1, τ at the 0.2 quantile of dev top-1 scores (home 1.93, desk 2.85) |
| K1-S0 | same | 0.531 | 0.588 | k=3, μ=1, τ at the 0.4 quantile of dev top-1 scores (home 2.43, desk 3.38) |
| hassil (home only) | Home Assistant's own English templates, unmodified | 0.588 (home) | | nothing to tune |
| always-decline | none | 0.500 | 0.708 | nothing to tune |
| embedding NN (diagnostic) | K1's bank, bge-small-en-v1.5 on Modal | 0.579 | | cosine ≥ 0.85 |

Reported beside K1, never as the arm (D8): the first lexical bank indexed on its ~40 act items per app
(0.530) and with a "none" class (0.550).

**The embedding router does not become an arm.** It beats K1 by +0.051 on dev with a paired,
stratified bootstrap interval of [-0.009, +0.108], which includes zero; §4.3 promotes it only
past the noise.

## What the arms are

- **K0** (schema-only): a blind author agent wrote ≤ 15 trigger phrases per tool and a rule-based argument
  extractor from the four schema files alone, in one pass from a published prompt (`baselines/k0/AUTHOR-PROMPT.md`,
  notes in `AUTHOR-NOTES.md`). BM25 (`bm25s` 0.3.9, PyStemmer 3.1.0 Snowball, no stop-word removal), top-k
  majority vote, refusal below τ (per app) or a vote margin μ; conjunction split for two actions. The author's
  choices are measured, never corrected (e.g. a bare "at 7" is read as 07:00 where the contract says ambiguous).
- **K1** (example-fed): the same machinery indexed on labelled act examples: MASSIVE en-US train/dev rows of the
  apps' action intents that the custodian's scan marked clean and no other partition uses, labelled by a declared
  intent-to-tool table (`baselines/k1_bank/`; home 130 rows, which is all the clean unused home text there is, and
  desk 200), plus the first bank's gold-labelled single-call act items. The label only routes; arguments come from the
  K0 extractor and refusal from τ/μ.
- **hassil**: OHF-Voice/intents at `f8cdbb0b` loaded by the repository's own loader, hassil 3.12.1, a declared
  intent-to-tool table written before any data (`baselines/hassil/MAPPING.md`, `NOTES.md`). It can never produce
  vacuum stop, relative levels, shade colours, indirect wording or two actions (upstream coverage); on dev it
  served 10 act items correctly, refused 47 and did nothing on every no-act item.
- **always-decline**: returns nothing; scores 0.500 on the D6 axis by construction, the check that a refusal-heavy
  result is not read as competence.

## Findings worth carrying

- **More labelled examples did not help BM25 here.** K1 stays below the schema-only K0 at every τ, μ and k in the
  grid (τ up to the 0.9 quantile, k up to 11). The outcomes say why: the crowd's own intent labels include requests
  the contract does not serve (MASSIVE `calendar_set` holds calendar events, not reminders), and near-miss requests
  share vocabulary with served ones, so K1 makes more wrong calls on do-nothing items (desk: 71 against K0's 49).
  Narrow trigger phrases separate them better than real examples do.
- **The D6 axis was corrected once before any LLM number was read** (DESIGN §13 D6): the first version made
  always-decline optimal and the tuning chose settings that refuse everything, which is how it was caught.
- **Two K1 banks were rejected as straw men** (DESIGN §13 D8), both after their dev numbers were seen; recorded as
  such.

For reference only (not a baseline; the subject), Needle on the same dev items: S1 home 0.502, S1 desk 0.489, S0 home 0.522, S0 desk
0.439 (`runs/needle_config/`).
