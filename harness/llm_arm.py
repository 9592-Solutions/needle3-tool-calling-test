# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""The cheap-LLM arm (DESIGN §4.2). One configuration per (model, host, contract); every call written raw.

Contracts:
  schema : the tool list is rendered in the system turn; the reply is constrained by a strict JSON schema
           {"calls": [oneOf(one object per tool)]}, where the EMPTY list is the refusal (Needle's own output space).
  native : the tool list goes in `tools`, tool_choice "auto"; no tool_calls in the reply = nothing.
Information parity (DESIGN §4.2): the system turn carries one fixed, task-neutral paragraph, the app's fact line
(the same one Needle receives) and, for the schema contract, the tools; no contract knowledge beyond the tool
descriptions both arms see byte-identically.

Per call: sha256 of the canonical request body, the host that served it, the full response body, usage (incl.
billed cost), wall latency, attempts, UTC timestamp. A call that fails after retries, or whose output does not
parse, is recorded with pred=None (a technical failure), never dropped.

usage: uv run harness/llm_arm.py --model M --host H --contract schema|native --schema S1-home \
          --items F.jsonl --out O.jsonl [--conc 8] [--limit N] [--reasoning off|minimal|none|omit] [--no-temp]
Key: OPENROUTER_API_KEY from the environment (the per-episode key; exported per run, never written to disk here).
"""
import argparse, asyncio, copy, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent.parent
FACT = "date: 2026-06-10 Wed 14:30; locale: en-US"
SYSTEM_SCHEMA = ("Call the tools below for the user's request. Reply with the calls as JSON; "
                 "return an empty list of calls if none applies.")
SYSTEM_NATIVE = "Call the tools for the user's request. If none applies, call no tool."


def schema_file(schema_id):
    ver, app = schema_id.split("-", 1)
    if ver in ("S0", "S1"):
        return ROOT / "contracts" / ver / f"{app}.json"
    return ROOT / "contracts" / "variants" / f"{schema_id}.json"


def app_of(schema_id):
    return "desk" if "desk" in schema_id else "home"


STRIP_LITE = ("pattern", "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "default")


def _strict_params(params, lite):
    """A tool's parameters as a strict-mode object: every property required, optional ones nullable."""
    p = copy.deepcopy(params)
    props = p.get("properties", {})
    req = set(p.get("required", []))
    for k, v in props.items():
        v.pop("default", None)
        if lite:
            for kw in STRIP_LITE:
                v.pop(kw, None)
        if k not in req:
            t = v.get("type")
            v["type"] = [t, "null"] if isinstance(t, str) else t
            if "enum" in v:
                v["enum"] = list(v["enum"]) + [None]
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def response_schema(tools, lite=False):
    variants = []
    for t in tools:
        f = t["function"]
        variants.append({"type": "object", "properties": {
            "name": {"type": "string", "enum": [f["name"]]},
            "arguments": _strict_params(f["parameters"], lite)},
            "required": ["name", "arguments"], "additionalProperties": False})
    return {"type": "json_schema", "json_schema": {"name": "calls", "strict": True, "schema": {
        "type": "object", "properties": {"calls": {"type": "array", "items": {"anyOf": variants}}},
        "required": ["calls"], "additionalProperties": False}}}


def build_body(cfg, tools, text):
    app = cfg["app"]
    fact = FACT if app == "desk" else None
    if cfg["contract"] == "schema":
        sys_txt = SYSTEM_SCHEMA + ("\n\n" + fact if fact else "") + "\n\nTools:\n" + json.dumps(tools, ensure_ascii=False)
        body = {"messages": [{"role": "system", "content": sys_txt}, {"role": "user", "content": text}],
                "response_format": response_schema(tools, cfg.get("lite", False))}
    else:
        sys_txt = SYSTEM_NATIVE + ("\n\n" + fact if fact else "")
        body = {"messages": [{"role": "system", "content": sys_txt}, {"role": "user", "content": text}],
                "tools": tools, "tool_choice": "auto"}
    body["model"] = cfg["model"]
    body["provider"] = {"order": [cfg["host"]], "allow_fallbacks": False, "require_parameters": cfg.get("require", True)}
    body["usage"] = {"include": True}
    body["max_tokens"] = cfg.get("max_tokens", 600)
    if cfg.get("temperature", True):
        body["temperature"] = 0
    r = cfg.get("reasoning", "off")
    if r == "off":
        body["reasoning"] = {"enabled": False}
    elif r in ("minimal", "none", "low"):
        body["reasoning"] = {"effort": r}
    return body


def parse(cfg, d):
    """-> (pred_calls or None, parse_status)"""
    try:
        msg = d["choices"][0]["message"]
    except Exception:
        return None, "no_choices"
    if cfg["contract"] == "native":
        tcs = msg.get("tool_calls") or []
        out = []
        for tc in tcs:
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except Exception:
                    return None, "tool_args_not_json"
            out.append({"name": fn.get("name"), "arguments": args or {}})
        return out, "ok"
    content = msg.get("content") or ""
    if not content.strip() and msg.get("tool_calls"):
        # Some hosts ignore response_format and return the model's calls as native tool calls (seen: gpt-oss-20b on
        # AkashML, 2026-09-22). They are unambiguous calls, so they are read as the answer (declared in FRONTIER.md).
        out = []
        for tc in msg["tool_calls"]:
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args) if args.strip() else {}
                except Exception:
                    return None, "tool_args_not_json"
            if fn.get("name") == "calls" and isinstance(args, dict) and isinstance(args.get("calls"), list):
                return [{"name": c.get("name"), "arguments": c.get("arguments") or {}} for c in args["calls"]], "ok_forced_wrapper"
            out.append({"name": fn.get("name"), "arguments": args or {}})
        return out, "ok_native_under_schema"
    try:
        j = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        calls = j["calls"]
        if not isinstance(calls, list):
            return None, "calls_not_list"
        return [{"name": c.get("name"), "arguments": c.get("arguments") or {}} for c in calls], "ok"
    except Exception as e:
        return None, f"invalid_json:{type(e).__name__}"


async def one(client, cfg, tools, item, sem, key):
    body = build_body(cfg, tools, item["text"])
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False)
    rec = {"id": item["id"], "model": cfg["model"], "host": cfg["host"], "contract": cfg["contract"],
           "schema": cfg["schema"], "request_sha256": hashlib.sha256(raw.encode()).hexdigest()}
    async with sem:
        for attempt in range(1, 5):
            t0 = time.perf_counter()
            try:
                r = await client.post("https://openrouter.ai/api/v1/chat/completions", json=body,
                                      headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://m37.local",
                                               "X-Title": "m37-needle3"}, timeout=90)
                wall = time.perf_counter() - t0
                d = r.json()
            except Exception as e:
                rec.update(error=f"{type(e).__name__}: {e}"[:300], attempts=attempt)
                await asyncio.sleep(2 * attempt)
                continue
            if r.status_code != 200 or "choices" not in d:
                rec.update(http=r.status_code, body=d, attempts=attempt)
                if r.status_code in (429, 500, 502, 503, 504, 408):
                    await asyncio.sleep(3 * attempt); continue
                break
            pred, status = parse(cfg, d)
            rec.update(http=200, attempts=attempt, wall_s=wall, served_by=d.get("provider"), usage=d.get("usage"),
                       response=d, pred=pred, parse=status)
            break
    rec.setdefault("pred", None)
    rec["ts"] = datetime.now(timezone.utc).isoformat()
    return rec


async def main(a):
    key = os.environ["OPENROUTER_API_KEY"]
    tools = json.loads(schema_file(a.schema).read_text())
    items = [json.loads(l) for l in open(a.items)]
    if a.limit:
        items = items[: a.limit]
    cfg = {"model": a.model, "host": a.host, "contract": a.contract, "schema": a.schema, "app": app_of(a.schema),
           "reasoning": a.reasoning, "temperature": not a.no_temp, "lite": a.lite, "require": not a.no_require,
           "max_tokens": a.max_tokens}
    done = set()
    if Path(a.out).exists():
        done = {json.loads(l)["id"] for l in open(a.out) if json.loads(l).get("http") == 200}
    todo = [i for i in items if i["id"] not in done]
    sem = asyncio.Semaphore(a.conc)
    async with httpx.AsyncClient() as client:
        recs = await asyncio.gather(*[one(client, cfg, tools, i, sem, key) for i in todo])
    with open(a.out, "a") as f:
        for r in recs:
            f.write(json.dumps({"cfg": cfg, **r}, ensure_ascii=False) + "\n")
    ok = sum(r.get("http") == 200 for r in recs)
    cost = sum(((r.get("usage") or {}).get("cost") or 0) for r in recs)
    hosts = {r.get("served_by") for r in recs if r.get("http") == 200}
    errs = [r.get("body") or r.get("error") for r in recs if r.get("http") != 200][:2]
    print(json.dumps({"model": a.model, "host": a.host, "contract": a.contract, "schema": a.schema, "n": len(recs),
                      "ok": ok, "cost": round(cost, 6), "served_by": sorted(h for h in hosts if h), "errors": errs})[:1500])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--host", required=True)
    ap.add_argument("--contract", choices=["schema", "native"], required=True)
    ap.add_argument("--schema", required=True); ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--conc", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reasoning", default="off", choices=["off", "minimal", "none", "low", "omit"])
    ap.add_argument("--no-temp", action="store_true"); ap.add_argument("--lite", action="store_true")
    ap.add_argument("--no-require", action="store_true"); ap.add_argument("--max-tokens", type=int, default=600)
    asyncio.run(main(ap.parse_args()))
