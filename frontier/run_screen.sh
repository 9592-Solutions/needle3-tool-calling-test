#!/bin/bash
# The screen (DESIGN §4.2 step 3): every candidate, S1, 100 selection items per app. Resumable (llm_arm skips done ids).
cd "$(dirname "$0")/.."
: "${OPENROUTER_API_KEY:?export your own OpenRouter key first}"
: > frontier/screen/_summary.jsonl
while IFS= read -r cmd; do ( eval "$cmd" 2>/dev/null | tail -1 >> frontier/screen/_summary.jsonl ) & while [ $(jobs -r | wc -l) -ge 6 ]; do sleep 1; done; done < frontier/screen_cmds.sh
wait
