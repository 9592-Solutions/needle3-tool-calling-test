# Data licences and attribution

The MIT licence in `LICENSE` covers the code. The rest of this file covers the data.

## Ours

The requests we wrote (every P2 phrasing marked `written for this test` in `requests/`), the gold labels, the
tool lists, the contract, the raw outputs we recorded, the results and the documents are released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), © 2026 9592 Solutions UG (haftungsbeschränkt). The P2
requests were drafted by language models (the model is named per item) from a scenario we wrote, then screened
and labelled by us.

## Third-party request datasets

Each item in `requests/` names its dataset, its id in that dataset and its licence. Items marked `adapted` were
edited (a join of two requests, a negation, a quotation and so on); the edit type is recorded per item, and the
adaptation is released under the same licence as its source.

| dataset | licence | source | attribution |
|---|---|---|---|
| MASSIVE 1.1, en-US | CC BY 4.0 | https://github.com/alexa/massive | © Amazon.com, Inc. or its affiliates. MASSIVE's English text comes from SLURP (CC BY 4.0, https://github.com/pswietojanski/slurp). FitzGerald et al., "MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages", 2022. |
| HWU64 (NLU-Evaluation-Data) | CC BY 4.0 | https://github.com/xliuhw/NLU-Evaluation-Data | Liu, Eshghi, Swietojanski and Rieser, "Benchmarking Natural Language Understanding Services for building Conversational Agents", 2019. |
| CLINC150 (oos-eval) | CC BY 3.0 | https://github.com/clinc/oos-eval | Larson et al., "An Evaluation Dataset for Intent Classification and Out-of-Scope Prediction", EMNLP 2019. Licence: https://creativecommons.org/licenses/by/3.0/ |

`sources/massive_en-US_train.jsonl`, `sources/massive_en-US_dev.jsonl` and `sources/clinc150_config_splits.json`
are copies of those datasets' non-test splits, used to build the configuration partitions, and are under the same
licences.

Other third-party material that appears inside the run records: Home Assistant intent templates are read from a
clone at run time and not copied here (OHF-Voice/intents, CC BY 4.0); a few test strings and tool definitions from
the Cactus `needle` repository appear in `preflight/` and `contracts/variants/vendor-smart_home.json`
(Apache-2.0, https://github.com/cactus-compute/needle).

## Band F

The 37 band F requests are short quotations from public comments on Hacker News, used to test the model on the
requests people tried when it was announced. Each item links to its comment. They remain the commenters' words and
are not relicensed.

## Needle 3

Needle 3 is © Cactus Compute and licensed under Apache-2.0 (https://huggingface.co/Cactus-Compute/needle3,
https://github.com/cactus-compute/needle). No weights, runner binary or package are included here.
