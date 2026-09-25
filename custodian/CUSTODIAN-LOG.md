# Needle 3 test custodian log

Custodian session `2ceae776-ba05-4ac9-914f-8226bfec6a3e` (Opus 5, effort high), dispatched by
m37-lead 2026-09-22 to run DESIGN.md §10 step 3 (§3 in full, §6.1). The configuration lead is
`m37-n3-config`. Firewall: nothing here describes the sealed test beyond what DESIGN.md already
says. The sealed material lives OUTSIDE git under `~/temp/m37-needle3-sealed/` (mode 700); only
its salted commitment is committed here.

## Sources (pinned 2026-09-22, raw copies in `~/temp/m37-needle3-src/`, public)
| source | url | sha256 |
|---|---|---|
| MASSIVE 1.1 tarball | https://amazon-massive-nlu-dataset.s3.amazonaws.com/amazon-massive-dataset-1.1.tar.gz | 4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577 |
| MASSIVE en-US.jsonl (inside it) | | c70f75c6a543a26e249ec383df67733ad9b1066f6c0406c2e04a3f03356e407e |
| HWU64 NLU-Data-Home-Domain-Annotated-All.csv | raw.githubusercontent.com/xliuhw/NLU-Evaluation-Data/master/AnnotatedData/ | 5f6dbf6d38fc111217924945ac59c554e0b926d5aa836ecdd0d089d2ca48e1d9 |
| CLINC150 data_full.json | raw.githubusercontent.com/clinc/oos-eval/master/data/ | 36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0 |
| Cactus `needle` repo (overlap scans only) | github.com/cactus-compute/needle | HEAD f189b23ebf34b98bcc8f9ee819249425c6623a32 |

## Partition boundary agreed with the config lead (2026-09-22, by message)
- Config lead builds dev / selection / calibration / lexical bank itself, ONLY from MASSIVE en-US
  train+dev and CLINC150 train+val (+ oos_train/oos_val), and never opens MASSIVE test, CLINC test,
  band F or the sealed paths. **Change from the custodian brief**, which listed dev and selection
  as custodian deliverables: the config lead proposed it and it keeps the one-way firewall clean
  (the custodian reads its partitions for cross-partition near-dup removal; it reads nothing of ours).
- HWU64 rows NOT verbatim in MASSIVE en-US: row id = 0-based data-row index in the pinned CSV
  (`answerid` is not unique: 21,339 distinct over 25,716 rows). `sha256(str(i))` first hex digit
  even → custodian (test-eligible), odd → config.
- `test-pool-blocklist.sha256`: sha256 of the normalised text of EVERY utterance in the whole
  test-eligible pools (all MASSIVE en-US test, CLINC test + oos_test, HWU even-parity not-in-MASSIVE
  rows): 14,457 utterances, 14,369 distinct hashes. It reveals no selection. Normalisation:
  `re.sub(r"\s+"," ",re.sub(r"[^\w\s']"," ",t.lower())).strip()`. The config lead drops exact
  matches from its partitions.

## Overlap scans (DESIGN §6.1)
- **Vendor material** (2026-09-22): every test-eligible utterance (14,457) against 925 distinct
  strings extracted from Cactus's six environment `TEST_CASES` suites (repo f189b23e), the
  playground presets (`needle/playground/app.js`), both Wayback snapshots of the demo sandbox
  (2026-09-18 00:13, 2026-09-19 03:07) and the fine-tuning guide page. Run on the Mac mini
  (bge-small-en-v1.5 via fastembed, CPU, $0). Drop rule: normalised exact match, OR char-4gram
  Jaccard ≥ 0.65, OR cosine ≥ 0.95. Thresholds set by reading the top of the distribution: at 0.95
  the pairs are paraphrases of one command ("olly turn the lights off in the bedroom" / "switch off
  the lights in the bedroom"); between 0.90 and 0.93 they are the same intent in different words
  ("send an e-mail" / "Send an email."), kept. 31 utterances dropped from the pools before any
  family was chosen; the drop list is sealed and published with the results.
- **Cross-partition** (DESIGN §3.4): MASSIVE train/dev repeat MASSIVE test's templates, so the
  first scan of the sealed set against the config partitions flagged many items. Removing them on
  the test side would have stripped most real crowd phrasing from the home test, so instead the
  config lead replaced every partition item (and screened its whole 12,353-row supply) that
  near-duplicates ANYTHING in the whole public test-eligible pool: pool-level lists, committed as
  `config-neardup-vs-test-pools.txt` (f67ac86a) and `config-supply-neardup-vs-test-pools.txt`
  (509e7de3), which carry no selection information. Residual collisions with fresh P2s and edits
  were resolved on the custodian side. Final scan vs items.jsonl at 0dc5e711 (1,277 items): no
  test or diagnostic collisions. The HN band keeps its few collisions by design: those requests are
  quoted verbatim and reported alone.
- **Within the sealed set**: same rule; same-outcome near-paraphrases between an anchor and a test
  family dropped the anchor. Different-outcome contrasts were kept.

## Log
- 11:28 sources pinned; test-eligible pools built (script and pools under the sealed dir).
- 11:50 contracts landed (dc7ba325, 6f10185f, 55319b21). Vendor overlap scan done.
- 12:00 two family-builder subagents (Opus; home, desk) dispatched on the sealed pools; P2 writers
  will be one Claude family (Opus) and one non-Anthropic family, **Muse Spark 1.3 via the CLX
  bridge on the OpenCode Go allowance** (labour, not in the $5; probed on three dummy scenarios,
  served model recorded as `muse`). Chosen over DeepSeek/Qwen/MiniMax because no Muse model is in the cheap-LLM comparator pool
  (`research/arms-and-cost.md` §1.2), so no comparator shares a writer.
- 12:15 families built: per app 150 test families (25 × six strata) and 72 anchor families, from
  the sealed pools, with builders' notes kept sealed. P1 self-scan (Mac mini, same rule): 5 anchors
  were same-outcome near-paraphrases of test families and were dropped (anchors now 139); remaining
  flagged pairs have different gold (deliberate contrasts) and were kept.
- 12:25 P2 writing: 300 scenarios, alternated by family within each (app, stratum) between the two
  writer families, shuffled and numbered so no writer sees a family id, stratum, P1 or schema.
- 12:25-14:50 P2 writing, annotation, adjudication, repairs (detail sealed in SEALED-RECORD.md):
  - P2s: every writer wrote THREE blind candidates per scenario, and a fixed surface rule kept the
    one least similar to the family's own P1, after dropping candidates that matched or near-duplicated
    any P1, band-F, vendor or config text. A first single-candidate round produced copies of the crowd
    phrasing, which would have voided the P1-vs-P2 canary; it is kept in the record and not used.
  - Gold: two blind annotators on every item (Opus 5 and Fable 5.1; Sonnet 5 stood in for Fable on the
    last nine repair items after the account hit its Fable limit), one fresh Opus adjudicator for every
    disagreement and every agreed-but-unsure case, and a decorrelation check by a third, non-Anthropic
    annotator (Muse) on a random 100 (98 matched final gold). Main-label agreement before
    adjudication: 783/787. None ruled ambiguous. Transcript audit: every annotator on its stated model,
    no reads of the other annotator's output.
  - Family checks: every family's two phrasings share gold except verbatim free text (list item,
    reminder text), and every item's act/no-act matches its stratum. Families that failed were
    replaced whole by promoted anchors, never edited to fit.
  - Process slip, recorded: one `git pull --rebase --autostash` on the shared tree (the house rules
    forbid autostash). Checked immediately: no stash left behind, and peers' uncommitted files identical
    to the session start.
- 14:53 **SEALED.** Commitment `96d2bc70bbf917bbfdf1d2da8d1044a278fd4b8caf3f7c1596a96c3a2cb26367`
  (COMMITMENT.md, git 4956b529). 150 files under `~/temp/m37-needle3-sealed/sealed/` (mode 700,
  outside git): test, diagnostics and band F request files (id/app/text, shuffled: the runner
  input at step 9, handed over only after FREEZE), their key files with gold and provenance, and
  the full working record. **The salt is at `~/temp/m37-needle3-salt/salt.hex` (mode 600, outside git)**
  and stays private until publication.
- 15:00 CONTRACT v1.1 (54f5a4ff) arrived after the seal. The config lead flagged it. An impact assessment
  (which sealed items it would change, with options) went to m37-lead. It is kept outside git because it
  names test items: `~/temp/m37-needle3-sealed/POST-SEAL-contract-v1.1-impact.md`. Not applied; the
  call is m37-lead's.
- Dollars: $0.00 (Mac mini CPU scans; subscription and OpenCode Go labour).

- 15:00-15:23 **v2 re-seal** on m37-lead's ruling (relabel under CONTRACT v1.1, re-seal before
  FREEZE, keep the v1.0 strata as the reporting frame, keep v1 on record). One inclusive screen of all
  sealed items against v1.1 flagged 37 items. They were relabelled by a blind pair (Opus 5 and Sonnet 5;
  Fable was still limited), and a fresh Opus adjudicator decided every one of the 73 labels.
  **10 gold labels on 4 items moved.** Three test families no longer fitted their stratum and were
  replaced whole by promoted anchors, whose new P2s were written blind, pre-screened for overlap,
  labelled by the pair and adjudicated. One diagnostic anchor became ambiguous and stays out of that
  diagnostic's headline. v2 sealed 15:23: commitment
  `f73c32e4807e793ab0be3bd1a943a01f4f9239a79fae1094ac9dda0e7ced55fe`, files in
  `~/temp/m37-needle3-sealed/sealed-v2/`, salt `~/temp/m37-needle3-salt/salt-v2.hex`. v1 is untouched
  in `sealed/` and still verifies against its manifest. COMMITMENT.md carries both.

## Hand-over for step 9 and after
- **Use v2** (`sealed-v2/`). Runner input: `sealed-v2/test-requests.jsonl` and `sealed-v2/diagnostics-requests.jsonl` and
  `sealed-v2/bandF-requests.jsonl` (id, app, text). Hand them to the runner only after FREEZE.md is committed.
- Gold for scoring (step 10): `sealed-v2/*-key.jsonl` (CONTRACT v1.1), canonical form, normalised by
  `contracts/mapping.py`. Home keys carry V-ROOMREQ and V-REL; anchors carry V-VENDOR (home), V-TIMER
  (desk) and V-COUNT-6/10/20. V-DISPATCH, V-RENAME, V-TRIGGERS, V-FORCED, V-CONTRACT-IN-PROMPT and the
  depth curve reuse main gold.
- Publication: reveal both salts, `MANIFEST.sealed.txt` and `MANIFEST.sealed-v2.txt` (beside the sealed dirs), and both sets of sealed files.
  Check: `sha256(salt_hex + "\n" + MANIFEST)` equals the committed value.
