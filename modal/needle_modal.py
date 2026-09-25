# /// script
# requires-python = ">=3.11"
# dependencies = ["modal==1.5.5"]
# ///
"""Needle 3 on rented CPU (Modal, workspace <workspace>). No inference ever runs on Christo's Mac.

The image pins everything DESIGN §1 names: HF Cactus-Compute/needle3 at revision b274efcb (weights, native
runner, tokenizer, config, the 3.0.1 wheel whose libneedle3.so the Python package loads), the Python package
from GitHub cactus-compute/needle at f189b23 (the commit the research read; it pins engine 3.0.1), telemetry
off, HF offline after the pinned download.

Entry points (called from the local driver, never with test material in this session):
  snapshot()                      hashes, --help, version strings, cpuinfo, vendor env suite fingerprints
  run_native(items, cfg)          one fresh `needle` PROCESS per item (DESIGN §1), raw stdout kept
  vendor_harness(env, min_conf)   the vendor's own _harness logic via the Python package, per case raw
Cost containment: every function has a hard timeout; the driver prints a projection before each call.
"""
import hashlib, json, os, subprocess, time
from pathlib import Path

import modal

HF_REPO = "Cactus-Compute/needle3"
HF_REV = "b274efcb211a9eef48c9a88da4b43bd569696a39"
GH_COMMIT = "f189b23ebf34b98bcc8f9ee819249425c6623a32"
ENGINE = "3.0.1"
ROOT = "/opt/needle3"
CACHE = f"/root/.cache/cactus-needle/v3/{ENGINE}"
FILES = ["needle3.cact", "linux-x86_64/needle", "linux-x86_64/needle.h", "config.json", "tokenizer/tokenizer.model",
         f"python/cactus_needle-{ENGINE}-py3-none-manylinux2014_x86_64.whl", "README.md"]
APP_NAME = "m37-needle3"

def _download_pinned():
    import shutil, zipfile
    from huggingface_hub import hf_hub_download
    os.makedirs(ROOT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
    for f in FILES:
        p = hf_hub_download(HF_REPO, f, revision=HF_REV)
        d = os.path.join(ROOT, f); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copyfile(p, d)
    os.chmod(f"{ROOT}/linux-x86_64/needle", 0o755)
    shutil.copyfile(f"{ROOT}/needle3.cact", f"{CACHE}/needle3.cact")
    z = zipfile.ZipFile(f"{ROOT}/python/cactus_needle-{ENGINE}-py3-none-manylinux2014_x86_64.whl")
    names = z.namelist()
    lib = next(n for n in names if n.startswith("needle/libneedle") and n.endswith(".so"))
    open(f"{CACHE}/libneedle.so", "wb").write(z.read(lib))
    open(f"{ROOT}/wheel-members.txt", "w").write("\n".join(names))


image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "binutils")
    .pip_install("huggingface_hub==0.35.3")
    .pip_install(f"cactus-needle @ git+https://github.com/cactus-compute/needle@{GH_COMMIT}")
    .run_function(_download_pinned)
    .env({"HF_HUB_OFFLINE": "1", "NEEDLE_TELEMETRY": "0", "DO_NOT_TRACK": "1",
          "NEEDLE3_LIB_PATH": f"{CACHE}/libneedle.so", "TOKENIZERS_PARALLELISM": "false"})
)
app = modal.App(APP_NAME, image=image, tags={"project": "m37", "episode": "needle3"})
BIN = f"{ROOT}/linux-x86_64/needle"
CACT = f"{ROOT}/needle3.cact"


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _cpu():
    """CPU identity. Under gVisor /proc/cpuinfo carries no model name, so record vendor, family, model,
    stepping and a hash of the flag set (which decides the SIMD kernels an engine picks)."""
    try:
        txt = open("/proc/cpuinfo").read().split("\n\n")[0]
        f = dict(l.split(":", 1) for l in txt.splitlines() if ":" in l)
        f = {k.strip(): v.strip() for k, v in f.items()}
        flags = f.get("flags", "").split()
        simd = [x for x in ("avx2", "avx512f", "avx512_vnni", "avx512bw", "avx_vnni", "amx_int8", "fma") if x in flags]
        return (f"{f.get('model name') or '?'} | {f.get('vendor_id')} fam {f.get('cpu family')} model {f.get('model')} "
                f"step {f.get('stepping')} | simd {','.join(simd)} | flags#{hashlib.sha256(' '.join(sorted(flags)).encode()).hexdigest()[:10]} "
                f"| ncpu {os.cpu_count()} | task {os.environ.get('MODAL_TASK_ID', '?')}")
    except Exception as e:
        return f"unknown ({e})"


@app.function(cpu=1.0, memory=1024, timeout=600)
def snapshot():
    import importlib, platform, re, sys
    out = {"hf_repo": HF_REPO, "hf_revision": HF_REV, "gh_commit": GH_COMMIT, "cpu_model": _cpu(),
           "platform": platform.platform(), "python": sys.version}
    out["files"] = {f: {"sha256": _sha(f"{ROOT}/{f}"), "bytes": os.path.getsize(f"{ROOT}/{f}")} for f in FILES}
    out["libneedle_so_sha256"] = _sha(f"{CACHE}/libneedle.so")
    h = subprocess.run([BIN, "--help"], capture_output=True, text=True, timeout=60)
    out["runner_help"] = {"rc": h.returncode, "stdout": h.stdout, "stderr": h.stderr}
    for label, path in (("runner", BIN), ("libneedle_so", f"{CACHE}/libneedle.so")):
        s = subprocess.run(["strings", path], capture_output=True, text=True).stdout
        out[f"{label}_version_strings"] = sorted({m for m in re.findall(r"\b3\.\d+\.\d+\b", s)})
        out[f"{label}_needle_strings"] = sorted({l for l in s.splitlines() if re.search(r"(?i)needle[ -]?v?3\.\d", l)})[:20]
    import needle
    from needle.agent import fetch
    out["python_pkg"] = {"file": needle.__file__, "engine_versions": fetch.ENGINE_VERSIONS,
                         "pip_version": subprocess.run([sys.executable, "-m", "pip", "show", "cactus-needle"],
                                                       capture_output=True, text=True).stdout}
    envs = {}
    for name in ("smart_home", "media_player", "productivity", "wearable", "kitchen_appliance", "data_capture"):
        m = importlib.import_module(f"needle.environments.{name}")
        envs[name] = {"n_tools": len(m.TOOLS), "n_cases": len(m.TEST_CASES),
                      "cases_sha256": hashlib.sha256(json.dumps(m.TEST_CASES, sort_keys=True, default=str).encode()).hexdigest(),
                      "tools_sha256": hashlib.sha256(json.dumps(m.TOOLS, sort_keys=True, default=str).encode()).hexdigest(),
                      "categories": sorted({c.get("category") for c in m.TEST_CASES})}
    out["vendor_envs"] = envs
    return out


@app.function(cpu=1.0, memory=1024, timeout=3600, max_inputs=1)
def run_native(items, cfg):
    """items: [{"id", "prompt"}]; cfg: {"tools": [...], "system": str|None, "depth": int|None, "threads": int,
    "forced": bool, "overflow_flag": bool, "extra": [str]}. One fresh process per item. Nothing is dropped:
    rc, stdout, stderr and wall time are kept raw, parsed JSON added when stdout parses."""
    import tempfile
    need = cfg.get("require_cpu")        # DESIGN change 2026-09-22: outputs differ across CPU classes
    if need and need not in _cpu():
        return {"cpu_model": _cpu(), "argv_base": None, "results": [], "wrong_cpu": True, "items": items}
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "tools.json"); Path(tp).write_text(json.dumps(cfg["tools"]))
    base = [BIN, "--model", CACT, "--tools", tp, "--threads", str(cfg.get("threads", 1))]
    if cfg.get("system"):
        sp = os.path.join(d, "system.txt"); Path(sp).write_text(cfg["system"]); base += ["--system", sp]
    if cfg.get("depth"):
        base += ["--depth", str(cfg["depth"])]
    if cfg.get("forced"):
        base += ["--forced"]
    if cfg.get("overflow_flag", True):
        base += ["--fail-input-overflow"]
    base += cfg.get("extra", [])
    res = []
    reps = int(cfg.get("repeats", 1))
    items = [dict(it, rep=k) for it in items for k in range(reps)]
    for it in items:
        t0 = time.perf_counter()
        try:
            p = subprocess.run(base + ["--prompt", it["prompt"]], capture_output=True, text=True, timeout=120)
            rc, so, se = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            rc, so, se = "timeout", (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout 120s"
        wall = time.perf_counter() - t0
        parsed = None
        try:
            parsed = json.loads(so.strip().splitlines()[-1]) if so.strip() else None
        except Exception:
            try:
                parsed = json.loads(so)
            except Exception:
                parsed = None
        res.append({"id": it["id"], "rep": it.get("rep", 0), "cpu": _cpu(), "prompt": it["prompt"], "rc": rc, "stdout": so, "stderr": se[-4000:],
                    "wall_s": wall, "parsed": parsed})
    return {"cpu_model": _cpu(), "argv_base": base, "results": res}


@app.function(cpu=1.0, memory=1024, timeout=1800, max_inputs=1)
def vendor_harness(env_name, min_conf=0.0, require_cpu=None):
    """The vendor's run_tests loop, unchanged in logic, but returning every case's raw response instead of
    printing. Also returns the exact system text the package sent (its auto-date prefix included), so the
    native runner can be given byte-identical input."""
    import importlib
    if require_cpu and require_cpu not in _cpu():
        return json.dumps({"wrong_cpu": True, "env": env_name, "cpu_model": _cpu()})
    import needle
    from needle.environments import _harness
    m = importlib.import_module(f"needle.environments.{env_name}")
    agent = _harness.agent_for(m)
    cases = []
    for case in m.TEST_CASES:
        agent.reset()
        r = agent.complete(case["query"])
        got = r.get("function_calls") or []
        v = r.get("validation") or {}
        if got and (v.get("ungrounded") or v.get("negation")):
            got = []
        if got and (r.get("confidence") or 0.0) < min_conf:
            got = []
        ok = sorted(_harness._key(c) for c in got) == sorted(_harness._key(c) for c in case["calls"])
        cases.append({"query": case["query"], "category": case.get("category"), "want": case["calls"],
                      "critical": case.get("critical", False), "response": r, "harness_got": got, "harness_ok": ok})
    tools_rendered = [t if isinstance(t, dict) else getattr(t, "schema", None) or repr(t) for t in m.TOOLS]
    agent_schemas = getattr(agent, "_tool_schemas", None)
    return json.dumps({"env": env_name, "system_text": agent._system_text, "tools": tools_rendered,
            "agent_tool_schemas": agent_schemas, "system_module": m.SYSTEM,
            "passed": sum(c["harness_ok"] for c in cases), "n": len(cases), "cases": cases, "cpu_model": _cpu()},
            default=repr)


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "native", "vendor"])
    ap.add_argument("--in", dest="inp", help="native: JSON file {items, cfg}")
    ap.add_argument("--env", help="vendor: environment name, or 'all'")
    ap.add_argument("--min-conf", type=float, default=0.0)
    ap.add_argument("--require-cpu", default=None, help="vendor: CPU class substring every container must match")
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunks", type=int, default=1, help="native: split items over N containers (accuracy runs only)")
    a = ap.parse_args()
    with modal.enable_output(), app.run():
        if a.cmd == "snapshot":
            res = snapshot.remote()
        elif a.cmd == "vendor":
            names = ["smart_home", "media_player", "productivity", "wearable", "kitchen_appliance", "data_capture"] if a.env == "all" else [a.env]
            res, pending = [], names
            for _ in range(25):
                got = [json.loads(x) for x in vendor_harness.starmap([(n, a.min_conf, a.require_cpu) for n in pending])]
                res += [g for g in got if not g.get("wrong_cpu")]
                pending = [g["env"] for g in got if g.get("wrong_cpu")]
                if not pending:
                    break
                print("retrying", pending)
            if pending:
                raise SystemExit(f"could not land {pending} on {a.require_cpu}")
        else:
            spec = json.loads(Path(a.inp).read_text())
            items, cfg = spec["items"], spec["cfg"]
            prev = json.loads(Path(a.out).read_text()) if Path(a.out).exists() else {"results": [], "containers": []}
            done = {r["id"] for r in prev["results"]}
            todo = [it for it in items if it["id"] not in done]
            k = max(1, a.chunks); pending = [p for p in (todo[i::k] for i in range(k)) if p]
            outs, tries = [], 0
            def save():
                order = {it["id"]: i for i, it in enumerate(items)}
                res = {"cfg": cfg, "chunk_attempts": tries,
                       "containers": prev["containers"] + [{"cpu_model": o["cpu_model"], "argv_base": o["argv_base"]} for o in outs],
                       "results": sorted(prev["results"] + [r for o in outs for r in o["results"]], key=lambda r: (order[r["id"]], r.get("rep", 0))),
                       "missing": [it["id"] for p in pending for it in p]}
                Path(a.out).parent.mkdir(parents=True, exist_ok=True)
                Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
                return res
            import time as _t
            while pending and tries < 60:
                tries += 1
                got = list(run_native.starmap([(p, cfg) for p in pending]))
                outs += [o for o in got if not o.get("wrong_cpu")]
                pending = [o["items"] for o in got if o.get("wrong_cpu")]
                save()
                if pending:
                    print(f"try {tries}: {len(pending)} chunk(s) landed elsewhere: {[o['cpu_model'][:48] for o in got if o.get('wrong_cpu')]}")
                    _t.sleep(min(60, 5 * tries))
            res = save()
            if pending:
                raise SystemExit(f"{len(res['missing'])} item(s) not landed on {cfg.get('require_cpu')!r}; partial results saved, rerun to resume")
            print("wrote", a.out); raise SystemExit(0)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("wrote", a.out)
