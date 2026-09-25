# hassil arm: pins

- **hassil 3.12.1** (PyPI, uploaded 2026-09-14). Pinned in the PEP 723 headers of `hassil_arm.py` and
  `test_hassil_arm.py` together with `PyYAML==6.0.3`. These are the same versions the intents repo's own
  `requirements.txt` pins at the commit below.
- **OHF-Voice/intents @ `f8cdbb0b6601cde140b9a40c297363c6137d219d`** (HEAD of the default branch on
  2026-09-22; commit dated 2026-09-19, "[PL] Add missing Combos and smaller improvements (#4217)").

## How they were fetched

```sh
cd /private/tmp && git clone https://github.com/OHF-Voice/intents.git needle3-intents
git -C /private/tmp/needle3-intents rev-parse HEAD   # f8cdbb0b6601cde140b9a40c297363c6137d219d
```
To reproduce at the pin: clone as above, then `git -C needle3-intents checkout f8cdbb0b6601cde140b9a40c297363c6137d219d`.

hassil comes from `uv run` resolving the header pins. No template is copied into this repo. The arm reads
the clone from `NEEDLE3_INTENTS_DIR` (or the `intents_dir` argument). At load it refuses to run if the
clone's HEAD differs from the pinned SHA, or if `git status` shows changes under `sentences/`, `lists/`,
`rules/`, `intents.yaml` or `script/`.

## Loader

The grammar is assembled by the repository's own `script/intentfest/util.py::load_intents_dict("en")`,
imported unmodified from the clone. Upstream's `merged_output` command uses the same function to build the
package Home Assistant ships. The result is then filtered to `supported` intents and to data blocks that
have sentences, the same filter `merged_output` applies. **Loader check:** every upstream English test
sentence for HassTurnOn, HassTurnOff, HassLightSet, HassVacuumStart, HassVacuumCleanArea and
HassVacuumReturnToBase whose expected slots fit our device list (area in our six rooms, no floor, no
name) was run through the arm's recognizer, and 114 of 114 returned the expected intent and area. That
check used upstream test files only, no Needle 3 data.
