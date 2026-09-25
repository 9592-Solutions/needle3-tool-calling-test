# Needle 3 build: snapshot manifest (DESIGN §10 step 1)

Taken 2026-09-22 by the configuration lead (session 2537465c). Every artifact the build depends on,
pinned by hash, read from the artifact itself (hashes computed inside the Modal image,
`modal-snapshot.json`, or locally for the dataset files). No test material was read: MASSIVE and
CLINC were split programmatically into their config-side partitions and the test rows were never
written out or printed; HWU64 was hashed only.

## Needle 3 (Hugging Face `Cactus-Compute/needle3`)

- Revision **`b274efcb211a9eef48c9a88da4b43bd569696a39`** (= `main` on 2026-09-22; lastModified 2026-09-19T18:59:36Z; `hf-needle3-api-main.json`). Unchanged since the design pinned it.

| file | bytes | sha256 |
|---|---|---|
| `needle3.cact` | 35,335,380 | `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38` |
| `linux-x86_64/needle` | 1,246,880 | `5eb163c5ed33bd914c103ef8eba2134c7bb2d97bafafdd69f410a4a3100e8c37` |
| `linux-x86_64/needle.h` | 1,187 | `3aa713942528d944598458cecb4a262f2cc49349bec63355f91df0b159964e55` |
| `config.json` | 1,273 | `32f855edcc633c170e260763e00edb50dd9fbba73bcc6d49e7b85861b6eb7d25` |
| `tokenizer/tokenizer.model` | 126,520 | `97dfd5666620b19875deba9e55953d312364e7763bd08bee428b94f1b9491b25` |
| `python/cactus_needle-3.0.1-py3-none-manylinux2014_x86_64.whl` | 536,871 | `05770ef9a85686583968ea15f62f9ad44217e078efdaa99559d3208bb8a369b0` |
| `README.md` | 7,504 | `f63d07574f8ef59f406756aea50f196f839507e5bbdb26d01e5278e42613d4d3` |
| `libneedle3.so` (extracted from the 3.0.1 manylinux wheel; what the Python package loads) | | `978fce130aac08af506b5fe8bb2950da58e9479d0de69d972d9bd69db953568d` |

- `needle3.cact` matches DESIGN §1 (`c9d915ec…`, 35,335,380 bytes). The native runner matches the research pass (1,246,880 bytes).
- **Engine version string: none exists.** Neither the native runner nor `libneedle3.so` contains a version string (`strings` search for `3.x.y` returned nothing), and `--help` prints none. DESIGN §1 asked to pin "the engine version string"; the engine is pinned by the binary hashes above instead, and the Python package's `ENGINE_VERSIONS` says `3.0.1`.
- Runner `--help` (verbatim, rc 0):
```
usage: /opt/needle3/linux-x86_64/needle [--model needle3.cact] [--tools tools.json] [--system system.txt] [--prompt "..."] [--serve] [--port N] [--max N] [--depth N] [--threads N] [--forced] [--fail-input-overflow] [--tool-index path]
  --model needle3.cact     the weights to run (required unless this build embeds them)
  --tools tools.json       the functions the assistant may call, as a JSON array
  --tool-index path        file holding this tool set's embeddings, reused when the schemas match
  --system system.txt      session facts like date, locale, or device
  --prompt "..."           answer one query and exit
  --max N                  response token limit (default 512)
  --depth N                endpoint-preserving ladder depth (2..full; default full)
  --threads N              worker threads (default: the device's fast cores, at most 4)
  --forced                 benchmark mode: always dispatch a call when tools are offered
  --fail-input-overflow    refuse a turn that would not fit the context window instead of trimming it
  --serve [--port N]       run an HTTP server (default port 8080): POST /complete {"input":"..."}, POST /reset
```

## Python package and vendor code

- `cactus-needle` installed from GitHub `cactus-compute/needle` at **`f189b23ebf34b98bcc8f9ee819249425c6623a32`** (= `main` on 2026-09-22, 2026-09-20 17:11 -0700); reports version 3.0.1, `ENGINE_VERSIONS` {'2': '2.0.4', '3': '3.0.1'}. PyPI's latest is **3.0.4** (releases 3.0.1-3.0.4); DESIGN §1 said to record both: the build uses git main, because that is the code the research read and the vendor harness it ships.
- The vendor's six environment suites at that commit (used ONLY as the known-answer control of our harness, DESIGN §10 step 4):

| env | tools | cases | categories | TEST_CASES sha256 | TOOLS sha256 |
|---|---|---|---|---|---|
| smart_home | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `a2b6b57399f9f3d3…` | `4992b54bedf9644b…` |
| media_player | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `0c32b4fb7473304a…` | `e8fc1d02e8ce51ac…` |
| productivity | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `a484ebd29b9e962d…` | `2cd7d36fd7e2e99a…` |
| wearable | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `0c1901acb5d8af20…` | `0801ab84d1955edc…` |
| kitchen_appliance | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `eca244a0605b2f2c…` | `1eef323d65e794a8…` |
| data_capture | 5 | 32 | invalid, irrelevant, missing, negation, parallel, positive | `d17316d35ae2475b…` | `91a6ec153e47659c…` |

## Runtime

- Modal workspace `<workspace>`, app `m37-needle3`, image `debian_slim` Python 3.12, `Linux-4.19.0-gvisor-x86_64-with-glibc2.36`. `/proc/cpuinfo` exposes no model name under gVisor (`unknown`); the CPU identity for latency is recorded per container from other fields at the latency pass.
- Env in every container: `HF_HUB_OFFLINE=1`, `NEEDLE_TELEMETRY=0`, `DO_NOT_TRACK=1`, `NEEDLE3_LIB_PATH` → the extracted pinned `libneedle3.so`. Image definition: `modal/needle_modal.py`.

## Request corpora (config side only)

| source | release | file sha256 | kept here |
|---|---|---|---|
| MASSIVE 1.1 | `amazon-massive-dataset-1.1.tar.gz` (40,251,390 bytes), sha256 `4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577` | train `dab6a7ed…1b02`, dev `b856fc9c…e8b6` | `sources/massive_en-US_{train,dev}.jsonl` (11,514 / 2,033 rows; test's 2,974 rows never written) |
| CLINC150 | GitHub `clinc/oos-eval` @ `828f8093` (2021-06-01), `data/data_full.json` sha256 `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` | config splits `85ffc53e…dfac` | `sources/clinc150_config_splits.json` (train 15,000, val 3,000, oos_train 100, oos_val 100; test and oos_test dropped before writing) |
| HWU64 | GitHub `xliuhw/NLU-Evaluation-Data` @ `f6071b49` (2022-03-09), `NLU-Data-Home-Domain-Annotated-All.csv` sha256 `5f6dbf6d38fc111217924945ac59c554e0b926d5aa836ecdd0d089d2ca48e1d9` (matches the custodian's) | | not kept; config side uses only rows with odd `sha256(str(row_index))[0]` that are not verbatim in MASSIVE (rule agreed with the custodian) |

## OpenRouter (read-only, free endpoints, 2026-09-22)

- `openrouter/models.json` (444 models) sha256 `d8ba143c…733c`; `openrouter/zdr.json` (876 ZDR endpoints) `58412a26…5aad`; `openrouter/endpoints/*.json`: per-host records for the 275 models whose list price was under 2× the ceiling.
- `openrouter/pool_hosts.json` (`d76c3e1e…6ea2`): 575 hosts under the DESIGN §4.2 ceiling ($0.50/M in, $2/M out) taking `tools` or `structured_outputs`, 382 of them ZDR, spanning **129 models**. The design priced ~15. See BUILD-LOG for the pool rule this forces.

## Keys and budget

- OpenRouter key `m37-needle3` (hash prefix redacted), provider-side limit **$4.00**, at `~/keys/OPENROUTER_API_KEY_M37_NEEDLE3.txt` (not committed). Minted 2026-09-22 via the provisioning API.
- Modal: no per-app budget exists (only a workspace-wide one, which would cap Christo's other Modal work); Modal spend is contained by per-function timeouts and a projection before each run, and attributed by app name (`modal billing report --tag-names`).
