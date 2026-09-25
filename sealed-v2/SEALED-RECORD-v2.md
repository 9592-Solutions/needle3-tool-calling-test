# Needle 3 sealed test v2: what changed from v1, and why (SEALED; published with the results)

Custodian session 2ceae776, 2026-09-22. v1 (commitment 96d2bc70..., git 4956b529) was labelled under
CONTRACT.md v1.0 (55319b21). CONTRACT v1.1 (54f5a4ff), written by the configuration lead from its own
dev-side adjudication, arrived after the v1 seal. m37-lead ruled: relabel under v1.1 and re-seal as v2
before FREEZE, because the arms run against v1.1 and gold following a contract the arms never saw
would score the contract change, not the models; keep the v1.0 strata as the reporting frame.
v1's files are unchanged in `../sealed/` and its commitment still verifies.

## Procedure
1. Screen: one Opus pass read all 768 sealed items with their v1.0 gold against CONTRACT v1.1 and
   flagged every item whose gold under any labelled variant could plausibly change (inclusive):
   37 items, 73 labels (`record/v2/screen-flags.jsonl`).
2. Relabel: the same blind pair discipline on those 37 items under v1.1: A = Opus 5, B = Sonnet 5
   (the account's Fable limit was still in force; the Fable attempt failed before writing).
   62 of 73 labels agreed.
3. Adjudicate: a fresh Opus adjudicator decided EVERY one of the 73 labels (not only disagreements):
   62 confirmed, 6 took draft 1, 4 took draft 2, 1 ambiguous.
4. Result: **10 gold labels on 4 items moved** (v1.0 -> v1.1), all traceable to the v1.1 changelog:
   - home-A2-21 P1 "make it dark in here": light_power(here, off) -> [] under main, V-ROOMREQ, V-REL (§6 case 3).
   - home-N2-21 P1 "change the lights in the living room to green and red": [] -> two set_light_color
     calls under main, V-ROOMREQ, V-REL (§6 case 1).
   - desk-A2-03 P2 "An alert at five in the afternoon would help me.": set_alarm -> "ambiguous".
   - desk-A2-X07 (anchor) "can you set a reminder alarm for me to workout": create_reminder ->
     "ambiguous" under main, V-TIMER, V-COUNT-20 (§6 case 10); it stays a diagnostic anchor and leaves
     that diagnostic's headline.
5. Family repairs: the three TEST families above no longer fit their stratum (or lost a scorable pair),
   so each was replaced whole by a promoted anchor (home-A2-a04, desk-A2-X01, home-N2-a06), whose P2s
   were written blind by the same writer family (three candidates, pre-screened against vendor,
   config partitions at 0dc5e711 and every other sealed text, selected by the fixed rule), labelled by
   the blind pair (7/7 labels agreed) and adjudicated (7/7 confirmed).
6. Checks at seal: 600 test items (25 per app x stratum x phrasing), 128 anchors, 37 band F; every
   family's P1 and P2 agree except verbatim free text; every item's act/no-act matches its stratum
   (v1.0 strata kept as the reporting frame; v1.1's strata precedence is a config-side convention and
   is NOT applied here).
