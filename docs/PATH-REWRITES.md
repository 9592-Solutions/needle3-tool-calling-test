# Local paths changed for publication

The test ran from a private working tree. Six files in that tree held paths to local folders, key files or a
Modal workspace name. In this repository those lines are changed so the scripts run from the repository root and
read the OpenRouter key from your environment. Nothing else in those files changed.

The freeze documents record sha256 hashes of the files as they ran. To check a hash, apply the diff below in
reverse (`git apply -R`) and hash the result: the first column is what you should get. One exception:
`modal/needle_modal.py` named our Modal workspace in its docstring, and that name is withheld here as well, so its
reversed file differs from the one that ran by that single word and its hash cannot be checked from this
repository alone. Nothing the file does depends on the name.

| file | sha256 as run | sha256 here | hash recorded in |
|---|---|---|---|
| `frontier/run_screen.sh` | `69589db53d30a5533aa63d3389be0892ad3b45dc5d2a7b1290b7ed17aa374d9e` | `206042d76c5ee4061adbd9173c19899b19c700aa04dc4442661b5f90b661c5a3` | not hashed in the freeze |
| `modal/needle_modal.py` | `992199b5fa2585787b7944b766505bec0f0740d37453920103612f35239a21d1` | `95f030afc17c85dd6413c28149b0cea383960fa7df373f8a0f72068c895e8247` | FREEZE.md §2 |
| `results/score_test.py` | `6caed0dc406e8971d693e700f71d200c50bf629664a33999d956ffabad41c010` | `b23d7de93c1f269d34ed757b032593e787807c9cc396369880bcd8c6e1b47414` | FREEZE-ADDENDUM.md §1 (a61e69a8…; see below) |
| `runs/sealed/make_specs.py` | `15d01c619e7c619ac1ac8329fbdd17c74b3eef506690e72c6f71116709de709f` | `f13ddc6abce9f02132020ee1460748a50dcfcd8f5688837201d54ec264747da4` | FREEZE-ADDENDUM.md §1 |
| `runs/sealed/run_sealed.sh` | `231c24326fbe91bfbdc1be161c677598bf01fc566f004178f69ddef6f3da4848` | `70bb230d38c0c9aa6854e202e778fd02fa72ff375b3eb00ac778666040f71de0` | FREEZE-ADDENDUM.md §1 |
| `runs/sealed/spend.py` | `6d86fa5f3df782d148ee787a17d14d127ac335eb8a958286908a84cf609b6f40` | `24c311fdbc41f8d78362a69975ed58912b82d6e4f90e830c87520e8de0d4a8d2` | FREEZE-ADDENDUM.md §1 |

`results/score_test.py` was hashed in FREEZE-ADDENDUM.md as `a61e69a8…` and then received one field-name fix
after the key files were opened (the sealed keys keep main gold under `gold["main"]`). The fix changed no rule and
is reported in RESULTS.md §11.1; the "as run" hash above is the file after that fix, which is the version that
produced `results/SCORES.json`.

Run logs under `runs/sealed/logs/` also had local paths replaced (`<repo>`, `<python>`, `~`) and Modal run links
shortened to `https://modal.com/apps/<workspace>/main/<app-run>`. `snapshot/MANIFEST.md` had the Modal workspace
name and the OpenRouter key's hash prefix removed, and `snapshot/hf-needle3-api-main.json` lists the two Hugging Face Spaces that used the model on
the day as `<hf-user>/<space>`, since those are other people's accounts. In the raw
LLM outputs, OpenRouter's `user_id` field (our account's id) reads `user_<redacted>`, and one rate-limit message
has an opaque id replaced with `<redacted-id>`; neither is read by any script. The freeze documents themselves are unchanged, so they still
name the folders the sealed files lived in during the run (`~/temp/m37-needle3-sealed/sealed-v2/`); in this
repository those files are in `sealed-v2/`.

```diff
--- a/frontier/run_screen.sh
+++ b/frontier/run_screen.sh
@@ -1,7 +1,7 @@
 #!/bin/bash
 # The screen (DESIGN §4.2 step 3): every candidate, S1, 100 selection items per app. Resumable (llm_arm skips done ids).
 cd "$(dirname "$0")/.."
-export OPENROUTER_API_KEY=$(cat ~/keys/OPENROUTER_API_KEY_M37_NEEDLE3.txt)
+: "${OPENROUTER_API_KEY:?export your own OpenRouter key first}"
 : > frontier/screen/_summary.jsonl
 while IFS= read -r cmd; do ( eval "$cmd" 2>/dev/null | tail -1 >> frontier/screen/_summary.jsonl ) & while [ $(jobs -r | wc -l) -ge 6 ]; do sleep 1; done; done < frontier/screen_cmds.sh
 wait

--- a/modal/needle_modal.py
+++ b/modal/needle_modal.py
@@ -2,7 +2,7 @@
 # requires-python = ">=3.11"
 # dependencies = ["modal==1.5.5"]
 # ///
-"""Needle 3 on rented CPU (Modal, workspace <workspace>). No inference ever runs on Christo's Mac.
+"""Needle 3 on rented CPU (Modal, workspace <workspace>). No inference ever runs on Christo's Mac.
 
 The image pins everything DESIGN §1 names: HF Cactus-Compute/needle3 at revision b274efcb (weights, native
 runner, tokenizer, config, the 3.0.1 wheel whose libneedle3.so the Python package loads), the Python package

--- a/results/score_test.py
+++ b/results/score_test.py
@@ -5,7 +5,7 @@
   uv run --no-project --with numpy --with jsonschema==4.26.0 python results/score_test.py
 Writes results/SCORES.json (every number) and results/EXAMPLES.json (FREEZE §11 draws). Prints a digest.
 
-Inputs: runs/sealed/out/** (raw outputs), ~/temp/m37-needle3-sealed/sealed-v2/{test,diagnostics,bandF}-key.jsonl.
+Inputs: runs/sealed/out/** (raw outputs), sealed-v2/{test,diagnostics,bandF}-key.jsonl.
 The salt is never read.
 
 Key adapter (the key files' field names were not known when this was written, because no key file is opened before
@@ -37,7 +37,7 @@
 S = ROOT / "runs" / "sealed"
 # The three overrides exist only for results/smoke_score_test.py (config-side data); the real run uses the defaults.
 O = Path(os.environ.get("NEEDLE3_SEALED_OUT", S / "out"))
-KEYS = Path(os.environ.get("NEEDLE3_KEYS", os.path.expanduser("~/temp/m37-needle3-sealed/sealed-v2")))
+KEYS = Path(os.environ.get("NEEDLE3_KEYS", ROOT / "sealed-v2"))
 INP = Path(os.environ.get("NEEDLE3_INPUTS", S / "inputs"))
 R = Path(os.environ.get("NEEDLE3_RESULTS_DIR", R))
 sys.path.insert(0, str(ROOT / "harness"))

--- a/runs/sealed/make_specs.py
+++ b/runs/sealed/make_specs.py
@@ -16,7 +16,7 @@
 
 H = Path(__file__).resolve().parent
 ROOT = H.parent.parent
-REQ = Path(os.path.expanduser("~/temp/m37-needle3-sealed/sealed-v2"))
+REQ = ROOT / "sealed-v2"
 FACT = "date: 2026-06-10 Wed 14:30; locale: en-US"
 CPU = "GenuineIntel fam 6 model 85"
 # V-VENDOR: the vendor harness's own system text (needle.environments.smart_home.SYSTEM, as captured in

--- a/runs/sealed/run_sealed.sh
+++ b/runs/sealed/run_sealed.sh
@@ -1,6 +1,6 @@
 #!/bin/bash
 # Needle 3 sealed run (DESIGN §10 step 9; FREEZE.md §3, §8, §10, §12). Raw outputs only; nothing is scored here.
-# Reads ONLY ~/temp/m37-needle3-sealed/sealed-v2/{test,diagnostics,bandF}-requests.jsonl (via make_specs.py).
+# Reads ONLY sealed-v2/{test,diagnostics,bandF}-requests.jsonl (via make_specs.py).
 # No key file and no salt is read. Logs carry counts, costs, CPU classes and file names, never request text.
 # usage: bash runs/sealed/run_sealed.sh {prep|tier1|latency|repeats|diag|all}
 # Tier 1 fires first; every later stage fires only if observed spend + its worst case <= $4.75 (spend.py --gate).
@@ -8,7 +8,7 @@
 cd "$(dirname "$0")/../.."                                    # production/needle3
 S=runs/sealed; O=$S/out; L=$S/logs; mkdir -p "$O/needle" "$O/llm" "$O/latency" "$L"
 NOPROXY="env -u HTTP_PROXY -u http_proxy -u HTTPS_PROXY -u https_proxy"
-export OPENROUTER_API_KEY="$(cat ~/keys/OPENROUTER_API_KEY_M37_NEEDLE3.txt)"
+: "${OPENROUTER_API_KEY:?export your own OpenRouter key first}"
 A_MODEL=deepseek/deepseek-v4-flash-0731; A_HOST="Sail Research"; A_CONTRACT=schema     # llm-a (FREEZE §3)
 N_MODEL=deepseek/deepseek-v4-flash;      N_HOST="OpenInference"; N_CONTRACT=native    # llm-named
 

--- a/runs/sealed/spend.py
+++ b/runs/sealed/spend.py
@@ -10,7 +10,7 @@
 import httpx, modal
 ap = argparse.ArgumentParser(); ap.add_argument("--gate", type=float); ap.add_argument("--label", default="")
 a = ap.parse_args()
-key = open(os.path.expanduser("~/keys/OPENROUTER_API_KEY_M37_NEEDLE3.txt")).read().strip()
+key = os.environ["OPENROUTER_API_KEY"]
 k = httpx.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {key}"}, timeout=30).json()["data"]
 start = dt.datetime(2026, 9, 22, tzinfo=dt.timezone.utc)
 end = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
```
