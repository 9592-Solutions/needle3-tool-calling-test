#!/bin/bash
# Needle on every config item, S1 and S0, pinned CPU class; 10 containers per spec.
cd "$(dirname "$0")/../../modal"
for s in S1_home S1_desk S0_home S0_desk; do
  env -u HTTP_PROXY -u http_proxy -u HTTPS_PROXY -u https_proxy uv run needle_modal.py native --in ../runs/needle_config/spec_$s.json --out ../runs/needle_config/out_$s.json --chunks 10 > ../runs/needle_config/log_$s.txt 2>&1 &
done
wait
