# /// script
# requires-python = ">=3.11"
# dependencies = ["modal==1.5.5", "httpx"]
# ///
"""Needle 3 latency (DESIGN §8; FREEZE §8, §12 item 2). Separate from the scored passes; nothing here is scored.

needle + K0 + K1 + hassil: one container per (app x core count) with a HARD cpu limit cpu=(n, n) and
  `--threads n`, n in {1, 4}, asserted on Intel fam 6 model 85 (else the container returns wrong_cpu and the
  driver re-lands it). 20 warm-up requests (the first 20 of the app's S1 test items) are discarded, then the
  app's 300 S1 test items serially, each timed in-process from request to parsed, schema-validated decision
  (for Needle: fresh process, stdout JSON, score.needle_calls, execute.valid_bundle). Needle's own prefill_tps,
  decode_tps and peak_ram_mb are kept. Cold start: 10 fresh containers per app at 1 core (max_inputs=1), each
  timing its first request from process start to decision.
llm-a, llm-named: a client in ONE Modal container in one fixed region (REGION), serial, one arm at a time, on the
  200 items of runs/sealed/inputs/latency-{home,desk}.jsonl; total time to a parsed decision and time to first
  token (streamed); network floor = 50 minimal requests (max_tokens 1) to the same pinned host before and after.
Image: modal/needle_modal.py's image (imported, file unchanged) plus the baselines' pinned packages, the pinned
OHF-Voice/intents clone and the repo's harness/contracts/baselines/partitions code.

usage (driver, from production/needle3):
  uv run runs/sealed/latency_modal.py needle --app home --n 1 --out runs/sealed/out/latency/needle_home_1.json
  uv run runs/sealed/latency_modal.py cold --app home --out runs/sealed/out/latency/cold_home.json
  uv run runs/sealed/latency_modal.py llm --arm llm-a --out runs/sealed/out/latency/llm-a.json
The OpenRouter key (OPENROUTER_API_KEY) is passed as an ephemeral Modal secret, never written to disk.
"""
import json, os, subprocess, sys, time
from pathlib import Path

import modal

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT / "modal"))
import needle_modal as NM  # noqa: E402   (frozen file, sha256 992199b5…; only its image and constants are used)

REGION = "us-east"
CPU = "GenuineIntel fam 6 model 85"
INTENTS_SHA = "f8cdbb0b6601cde140b9a40c297363c6137d219d"
ARMS = {"llm-a": {"model": "deepseek/deepseek-v4-flash-0731", "host": "Sail Research", "contract": "schema"},
        "llm-named": {"model": "deepseek/deepseek-v4-flash", "host": "OpenInference", "contract": "native"}}

image = (NM.image
         .pip_install("bm25s==0.3.9", "PyStemmer==3.1.0", "numpy", "hassil==3.12.1", "PyYAML==6.0.3",
                      "jsonschema==4.26.0", "httpx")
         .run_commands(f"git clone https://github.com/OHF-Voice/intents.git /opt/intents && git -C /opt/intents checkout {INTENTS_SHA}")
         .env({"NEEDLE3_INTENTS_DIR": "/opt/intents"})
         .add_local_dir(str(ROOT / "harness"), "/repo/harness", ignore=["__pycache__"])
         .add_local_dir(str(ROOT / "contracts"), "/repo/contracts", ignore=["__pycache__"])
         .add_local_dir(str(ROOT / "baselines"), "/repo/baselines", ignore=["__pycache__", "nn"])
         .add_local_file(str(ROOT / "partitions" / "gold.jsonl"), "/repo/partitions/gold.jsonl")
         .add_local_python_source("needle_modal"))
app = modal.App(NM.APP_NAME, image=image, tags={"project": "m37", "episode": "needle3"})


def _decide_needle(base, text, validators):
    import score, execute
    t0 = time.perf_counter()
    p = subprocess.run(base + ["--prompt", text], capture_output=True, text=True, timeout=120)
    so = p.stdout.strip()
    try:
        parsed = json.loads(so.splitlines()[-1]) if so else None
    except Exception:
        parsed = None
    calls = score.needle_calls(parsed)
    ok = calls is not None and (not calls or execute.valid_bundle(calls, validators))
    dt = time.perf_counter() - t0
    g = (lambda k: parsed.get(k) if isinstance(parsed, dict) else None)
    return {"t_s": dt, "rc": p.returncode, "returned": bool(calls), "tech_fail": calls is None, "valid": ok,
            "prefill_tps": g("prefill_tps"), "decode_tps": g("decode_tps"), "peak_ram_mb": g("peak_ram_mb"),
            "confidence": g("confidence")}


def _setup(appname, n, tools, system):
    import tempfile
    sys.path[:0] = ["/repo/harness", "/repo/contracts", "/repo/baselines", "/repo/baselines/hassil"]
    import execute
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "tools.json"); Path(tp).write_text(json.dumps(tools))
    base = [NM.BIN, "--model", NM.CACT, "--tools", tp, "--threads", str(n)]
    if system:
        sp = os.path.join(d, "system.txt"); Path(sp).write_text(system); base += ["--system", sp]
    base += ["--fail-input-overflow"]
    validators = execute.tools_for(tp)
    return base, validators


def _latency(appname, n, items, tools, system, warmup):
    t_entry = time.perf_counter()
    cpu = NM._cpu()
    if CPU not in cpu:
        return {"wrong_cpu": True, "cpu_model": cpu}
    base, validators = _setup(appname, n, tools, system)
    import bm25_arm as B, execute
    out = {"app": appname, "n": n, "cpu_model": cpu, "argv_base": base, "needle": [], "baselines": {}}
    for it in warmup:
        _decide_needle(base, it["text"], validators)
    for it in items:
        out["needle"].append({"id": it["id"], **_decide_needle(base, it["text"], validators)})
    dev = json.loads(Path("/repo/baselines/DEV-RESULTS.json").read_text())["arms"]
    bank = [g for g in map(json.loads, open("/repo/partitions/gold.jsonl")) if g["partition"] == "lexical" and g["app"] == appname]
    sid = f"S1-{appname}"
    arms = {"K0": B.Router(sid, B.k0_docs(sid)), "K1": B.Router(sid, B.k1_bank_docs(sid, bank))}
    for name, r in arms.items():
        t = dev[f"{name}-S1"]["tuned"]
        for it in warmup:
            r.predict(it["text"], t["k"], t["tau"][appname], t["mu"])
        rows = []
        for it in items:
            t0 = time.perf_counter()
            calls, _ = r.predict(it["text"], t["k"], t["tau"][appname], t["mu"])
            ok = not calls or execute.valid_bundle(calls, validators)
            rows.append({"id": it["id"], "t_s": time.perf_counter() - t0, "returned": bool(calls), "valid": ok})
        out["baselines"][name] = rows
    if appname == "home":
        import hassil_arm
        inv = {}
        import mapping
        for raw, (action, amap) in mapping.TABLES["S1-home"].items():
            inv[action] = (raw, {c: r for r, c in amap.items()})
        t0 = time.perf_counter(); arm = hassil_arm.HassilArm(); out["hassil_load_s"] = time.perf_counter() - t0
        for it in warmup:
            arm.predict(it["text"])
        rows = []
        for it in items:
            t0 = time.perf_counter()
            pc = arm.predict(it["text"])
            raw = [{"name": inv[c["action"]][0], "arguments": {inv[c["action"]][1].get(k, k): v for k, v in c["args"].items()}} for c in pc]
            ok = not raw or execute.valid_bundle(raw, validators)
            rows.append({"id": it["id"], "t_s": time.perf_counter() - t0, "returned": bool(raw), "valid": ok})
        out["baselines"]["hassil"] = rows
    out["container_s"] = time.perf_counter() - t_entry
    out["cpu_model_end"] = NM._cpu()
    return out


@app.function(cpu=(1, 1), memory=1024, timeout=7200, max_inputs=1)
def latency_1(appname, items, tools, system, warmup):
    return _latency(appname, 1, items, tools, system, warmup)


@app.function(cpu=(4, 4), memory=2048, timeout=7200, max_inputs=1)
def latency_4(appname, items, tools, system, warmup):
    return _latency(appname, 4, items, tools, system, warmup)


@app.function(cpu=(1, 1), memory=1024, timeout=600, max_inputs=1)
def cold(appname, item, tools, system, k):
    t_proc = time.perf_counter()
    cpu = NM._cpu()
    if CPU not in cpu:
        return {"wrong_cpu": True, "cpu_model": cpu, "k": k}
    base, validators = _setup(appname, 1, tools, system)
    r = _decide_needle(base, item["text"], validators)
    return {"k": k, "cpu_model": cpu, "id": item["id"], "first_request": r, "entry_to_decision_s": time.perf_counter() - t_proc}


def _stream_call(client, body, key):
    """One streamed chat completion. Returns (ttft_s, total_s, message, meta)."""
    t0 = time.perf_counter(); ttft = None
    msg = {"content": "", "tool_calls": []}; meta = {}
    with client.stream("POST", "https://openrouter.ai/api/v1/chat/completions", json=body, timeout=120,
                       headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://m37.local", "X-Title": "m37-needle3"}) as r:
        meta["http"] = r.status_code
        if r.status_code != 200:
            meta["body"] = r.read().decode()[:500]
            return None, time.perf_counter() - t0, None, meta
        for line in r.iter_lines():
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data.strip() == "[DONE]":
                break
            try:
                d = json.loads(data)
            except Exception:
                continue
            if d.get("provider"):
                meta["served_by"] = d["provider"]
            if d.get("usage"):
                meta["usage"] = d["usage"]
            if d.get("error"):
                meta["error"] = d["error"]
            for ch in d.get("choices") or []:
                delta = ch.get("delta") or {}
                if (delta.get("content") or delta.get("tool_calls")) and ttft is None:
                    ttft = time.perf_counter() - t0
                if delta.get("content"):
                    msg["content"] += delta["content"]
                for tc in delta.get("tool_calls") or []:
                    i = tc.get("index", 0)
                    while len(msg["tool_calls"]) <= i:
                        msg["tool_calls"].append({"function": {"name": "", "arguments": ""}})
                    f = tc.get("function") or {}
                    if f.get("name"):
                        msg["tool_calls"][i]["function"]["name"] += f["name"]
                    if f.get("arguments"):
                        msg["tool_calls"][i]["function"]["arguments"] += f["arguments"]
    if not msg["tool_calls"]:
        msg["tool_calls"] = None
    return ttft, time.perf_counter() - t0, msg, meta


@app.function(cpu=1.0, memory=1024, timeout=7200, region=REGION, max_inputs=1,
              secrets=[modal.Secret.from_local_environ(["OPENROUTER_API_KEY"])])
def llm_latency(arm, items_by_app, tools_by_app, n_floor=50):
    import httpx
    sys.path[:0] = ["/repo/harness"]
    import llm_arm
    key = os.environ["OPENROUTER_API_KEY"]
    a = ARMS[arm]
    out = {"arm": arm, **a, "region": REGION, "modal_region": os.environ.get("MODAL_REGION"),
           "cloud": os.environ.get("MODAL_CLOUD_PROVIDER"), "floor_before": [], "floor_after": [], "rows": []}

    def floor(dst):
        body = {"model": a["model"], "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1, "stream": True,
                "provider": {"order": [a["host"]], "allow_fallbacks": False}, "reasoning": {"enabled": False}}
        for _ in range(n_floor):
            ttft, tot, _m, meta = _stream_call(client, body, key)
            dst.append({"ttft_s": ttft, "total_s": tot, "http": meta.get("http"), "served_by": meta.get("served_by"),
                        "cost": (meta.get("usage") or {}).get("cost")})

    with httpx.Client() as client:
        floor(out["floor_before"])
        for appname in ("home", "desk"):
            tools = tools_by_app[appname]
            cfg = {"model": a["model"], "host": a["host"], "contract": a["contract"], "schema": f"S1-{appname}", "app": appname,
                   "reasoning": "off", "temperature": True, "lite": False, "require": True, "max_tokens": 600}
            for it in items_by_app[appname]:
                body = llm_arm.build_body(cfg, tools, it["text"]); body["stream"] = True
                row = {"id": it["id"], "app": appname}
                for attempt in range(1, 5):
                    ttft, tot, msg, meta = _stream_call(client, body, key)
                    row.update(attempt=attempt, ttft_s=ttft, total_s=tot, http=meta.get("http"), served_by=meta.get("served_by"),
                               cost=(meta.get("usage") or {}).get("cost"), err=meta.get("body") or meta.get("error"))
                    if meta.get("http") == 200 and msg is not None:
                        t0 = time.perf_counter()
                        pred, status = llm_arm.parse(cfg, {"choices": [{"message": msg}]})
                        row.update(parse=status, returned=bool(pred), tech_fail=pred is None,
                                   total_to_decision_s=tot + (time.perf_counter() - t0))
                        break
                    if meta.get("http") in (408, 429, 500, 502, 503, 504):
                        time.sleep(3 * attempt); continue
                    break
                out["rows"].append(row)
        floor(out["floor_after"])
    return out


def _land(fn, args, tries=60):
    for t in range(1, tries + 1):
        r = fn.remote(*args)
        if not r.get("wrong_cpu"):
            r["land_tries"] = t
            return r
        print(f"try {t}: landed on {r['cpu_model'][:48]}, re-landing", flush=True)
        time.sleep(min(60, 5 * t))
    raise SystemExit("could not land on the pinned CPU class")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["needle", "cold", "llm"])
    ap.add_argument("--app"); ap.add_argument("--n", type=int, default=1); ap.add_argument("--arm")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="smoke test only: first N items, N warm-ups, N floor requests")
    a = ap.parse_args()
    INP = Path(os.environ.get("NEEDLE3_INPUTS", H / "inputs"))   # override for the config-side smoke test only
    FACT = "date: 2026-06-10 Wed 14:30; locale: en-US"
    rows = lambda app_: [json.loads(l) for l in open(INP / f"test-{app_}.jsonl")]
    tools = lambda app_: json.loads((ROOT / "contracts" / "S1" / f"{app_}.json").read_text())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with modal.enable_output(), app.run():
        if a.cmd == "needle":
            items = sorted(rows(a.app), key=lambda r: r["id"])
            fn = latency_1 if a.n == 1 else latency_4
            w = items[:a.limit] if a.limit else items[:20]
            items = items[:a.limit] if a.limit else items
            res = _land(fn, (a.app, items, tools(a.app), FACT if a.app == "desk" else None, w))
        elif a.cmd == "cold":
            items = sorted(rows(a.app), key=lambda r: r["id"])
            res, pending = [], list(range(10))
            for t in range(60):
                got = list(cold.starmap([(a.app, items[k], tools(a.app), FACT if a.app == "desk" else None, k) for k in pending]))
                res += [g for g in got if not g.get("wrong_cpu")]
                pending = [g["k"] for g in got if g.get("wrong_cpu")]
                if not pending:
                    break
                print(f"try {t + 1}: {len(pending)} cold container(s) off-class, re-landing", flush=True); time.sleep(min(60, 5 * (t + 1)))
            res = {"app": a.app, "containers": res, "unlanded": pending}
        else:
            it = {ap_: [json.loads(l) for l in open(INP / f"latency-{ap_}.jsonl")][: a.limit or None] for ap_ in ("home", "desk")}
            res = llm_latency.remote(a.arm, it, {ap_: tools(ap_) for ap_ in ("home", "desk")}, a.limit or 50)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("wrote", a.out)
