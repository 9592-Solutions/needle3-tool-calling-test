#!/bin/bash
# Needle 3 sealed run (DESIGN §10 step 9; FREEZE.md §3, §8, §10, §12). Raw outputs only; nothing is scored here.
# Reads ONLY sealed-v2/{test,diagnostics,bandF}-requests.jsonl (via make_specs.py).
# No key file and no salt is read. Logs carry counts, costs, CPU classes and file names, never request text.
# usage: bash runs/sealed/run_sealed.sh {prep|tier1|latency|repeats|diag|all}
# Tier 1 fires first; every later stage fires only if observed spend + its worst case <= $4.75 (spend.py --gate).
# Every stage is resumable: re-running a stage re-sends only what has no stored output.
cd "$(dirname "$0")/../.."                                    # production/needle3
S=runs/sealed; O=$S/out; L=$S/logs; mkdir -p "$O/needle" "$O/llm" "$O/latency" "$L"
NOPROXY="env -u HTTP_PROXY -u http_proxy -u HTTPS_PROXY -u https_proxy"
: "${OPENROUTER_API_KEY:?export your own OpenRouter key first}"
A_MODEL=deepseek/deepseek-v4-flash-0731; A_HOST="Sail Research"; A_CONTRACT=schema     # llm-a (FREEZE §3)
N_MODEL=deepseek/deepseek-v4-flash;      N_HOST="OpenInference"; N_CONTRACT=native    # llm-named

needle() {  # needle <spec-name> <chunks>: pinned-class driver, resumed until every item has landed
  local k
  for k in $(seq 1 20); do
    (cd modal && $NOPROXY uv run needle_modal.py native --in "../$S/specs/$1.json" --out "../$O/needle/$1.json" --chunks "$2") \
      >> "$L/needle_$1.log" 2>&1 && return 0
    echo "needle $1: pass $k incomplete, resuming" >> "$L/needle_$1.log"; sleep 30
  done
  echo "needle $1: NOT COMPLETE after 20 passes" | tee -a "$L/needle_$1.log"; return 1
}

llm() {  # llm <arm> <schema> <items> <out-name> [runner]: initial pass + up to three re-passes for unserved items
  local arm=$1 schema=$2 items=$3 out=$4 runner=${5:-harness/llm_arm.py} m h c p
  if [ "$arm" = llm-a ]; then m=$A_MODEL; h=$A_HOST; c=$A_CONTRACT; else m=$N_MODEL; h=$N_HOST; c=$N_CONTRACT; fi
  for p in 1 2 3 4; do
    uv run --no-project --with httpx python "$runner" --model "$m" --host "$h" --contract "$c" --schema "$schema" \
      --items "$S/inputs/$items.jsonl" --out "$O/llm/$arm/$out.jsonl" --conc 4 --reasoning off >> "$L/llm_${arm}.log" 2>&1
    left=$(python3 -c "import json,sys; d={json.loads(l)['id'] for l in open(sys.argv[2]) if json.loads(l).get('http')==200}; print(sum(json.loads(l)['id'] not in d for l in open(sys.argv[1])))" "$S/inputs/$items.jsonl" "$O/llm/$arm/$out.jsonl")
    [ "$left" = 0 ] && return 0
    echo "llm $arm $out: $left unserved after pass $p" >> "$L/llm_${arm}.log"; sleep $((30 * p))
  done
}

gate() {  # gate <stage>: exits the stage (returns 1) when it would breach $4.75
  local w; w=$(python3 $S/costs.py "$1")
  if $NOPROXY uv run $S/spend.py --gate "$w" --label "$1" | tee -a "$L/gates.log"; then return 0; fi
  echo "STAGE $1 NOT FIRED (budget)" | tee -a "$L/gates.log"; return 1
}

prep() { python3 $S/make_specs.py | tee "$L/prep.log"; }

tier1() {
  $NOPROXY uv run $S/spend.py --label "tier1 start" >> "$L/gates.log"
  mkdir -p "$O/llm/llm-a" "$O/llm/llm-named"
  for s in needle_S1_home_test needle_S1_desk_test needle_S0_home_test needle_S0_desk_test; do needle $s 20 & done
  for s in needle_S1_home_bandF needle_S1_desk_bandF; do needle $s 4 & done
  for arm in llm-a llm-named; do
    ( for app in home desk; do for ver in S1 S0; do llm $arm $ver-$app test-$app test_${ver}_$app; done
        llm $arm S1-$app bandF-$app bandF_S1_$app; done ) &
  done
  NEEDLE3_INTENTS_DIR=/private/tmp/needle3-intents uv run $S/baselines_sealed.py > "$L/baselines.log" 2>&1
  wait
  $NOPROXY uv run $S/spend.py --label "tier1 end" >> "$L/gates.log"
}

latency() {
  gate latency || return 0
  for app in home desk; do for n in 1 4; do
    $NOPROXY uv run $S/latency_modal.py needle --app $app --n $n --out "$O/latency/needle_${app}_$n.json" > "$L/latency_needle_${app}_$n.log" 2>&1 &
  done; $NOPROXY uv run $S/latency_modal.py cold --app $app --out "$O/latency/cold_$app.json" > "$L/latency_cold_$app.log" 2>&1 & done
  for arm in llm-a llm-named; do        # serial, one arm at a time
    $NOPROXY uv run $S/latency_modal.py llm --arm $arm --out "$O/latency/$arm.json" > "$L/latency_$arm.log" 2>&1
  done
  wait
}

repeats() {
  gate repeats || return 0
  for app in home desk; do for r in 1 2; do needle needle_S1_${app}_repeat_r$r 3 & done; done
  for arm in llm-a llm-named; do for app in home desk; do for r in 1 2; do
    llm $arm S1-$app repeat-$app repeat_r${r}_S1_$app; done; done; done
  wait
}

diag() {  # FREEZE §8 priority order, after the S1 reference on the anchors; each stage gated on its own worst case
  if gate V-BASE; then for app in home desk; do needle needle_S1_${app}_diag 6 & for arm in llm-a llm-named; do llm $arm S1-$app diag-$app diag_S1_$app; done; done; wait; fi
  if gate V-REL; then needle needle_rel_home_relroom 10 & for arm in llm-a llm-named; do llm $arm home-rel relroom-home rel_home; done; wait; fi
  if gate V-ROOMREQ; then needle needle_roomreq_home_relroom 10 & for arm in llm-a llm-named; do llm $arm home-roomreq relroom-home roomreq_home; done; wait; fi
  if gate V-COUNT; then for app in home desk; do for c in 6 10 20; do needle needle_count${c}_${app}_diag 6 & done; done; wait; fi
  if gate V-RENAME; then for app in home desk; do needle needle_renamed_${app}_diag 6 & for arm in llm-a llm-named; do llm $arm $app-renamed diag-$app renamed_$app; done; done; wait; fi
  if gate V-DISPATCH; then for app in home desk; do needle needle_dispatch_${app}_diag 6 & for arm in llm-a llm-named; do llm $arm $app-dispatch diag-$app dispatch_$app; done; done; wait; fi
  if gate V-TIMER; then needle needle_timerS_desk_diag 6 & needle needle_timerU_desk_diag 6 &
    for arm in llm-a llm-named; do llm $arm desk-timer-seconds diag-desk timerS_desk; llm $arm desk-timer-units diag-desk timerU_desk; done; wait; fi
  if gate V-VENDOR; then needle needle_vendor_home_diag 6 & for arm in llm-a llm-named; do llm $arm vendor-smart_home diag-home vendor_home; done; wait; fi
  if gate V-TRIGGERS; then for app in home desk; do needle needle_triggers_${app}_test 10 & needle needle_triggers_${app}_diag 6 & done; wait; fi
  if gate V-CONTRACT; then for arm in llm-a llm-named; do for app in home desk; do llm $arm S1-$app diag-$app contract_S1_$app $S/llm_contract.py; done; done; fi
  if gate V-FORCED; then for app in home desk; do needle needle_forced_${app}_diag 6 & done; wait; fi
}

case "$1" in
  prep) prep ;; tier1) tier1 ;; latency) latency ;; repeats) repeats ;; diag) diag ;;
  all) prep && tier1 && latency && repeats && diag ;;
  *) echo "usage: $0 {prep|tier1|latency|repeats|diag|all}"; exit 2 ;;
esac
$NOPROXY uv run $S/spend.py --label "after $1" >> "$L/gates.log"
