# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Prefix-continuation memorisation probe (DESIGN §6.2; jev-2's method, CONTAMINATION.md Test 2), LLM arms only.
For each item (>= 8 words) give the first half of the words and ask for the rest, under two instructions:
GENERAL (just complete it) and GUIDED (names the public corpus and asks for its exact text). Run on the
crowd ORIGINALS (MASSIVE train/dev, public since 2019) and, as the control, on fresh PARAPHRASES that exist in
no dataset. A memorising model reproduces originals verbatim more often than paraphrases under GUIDED.
Serving config per arm is read from the frontier screen config (same host pin, reasoning, temperature).
usage: uv run canary/prefix_probe.py <model> <host> <reasoning> <temp:1|0> <items.jsonl> <tag>"""
import asyncio, difflib, json, os, re, sys
from pathlib import Path
import httpx
H = Path(__file__).resolve().parent
model, host, reasoning, temp, items_path, tag = sys.argv[1:7]
PROMPTS = {
    "general": "Complete the following request someone said to a voice assistant. Output only the missing continuation, nothing else.\n\nRequest start: {p}",
    "guided": "The following is the start of an utterance from the Amazon MASSIVE (SLURP) spoken-language-understanding dataset, English. Complete it exactly as it appears in that dataset. Output only the missing continuation, nothing else.\n\nUtterance start: {p}",
}
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (t or "").lower())).strip()
items = [x for x in map(json.loads, open(items_path)) if len(x["text"].split()) >= 8]
out = H / f"prefix__{tag}__{model.replace('/', '__')}.jsonl"


async def one(c, sem, x, kind):
    w = x["text"].split(); k = len(w) // 2
    pre, suf = " ".join(w[:k]), " ".join(w[k:])
    body = {"model": model, "messages": [{"role": "user", "content": PROMPTS[kind].format(p=pre)}],
            "provider": {"order": [host], "allow_fallbacks": False}, "usage": {"include": True}, "max_tokens": 200}
    if temp == "1":
        body["temperature"] = 0
    if reasoning == "off":
        body["reasoning"] = {"enabled": False}
    elif reasoning in ("minimal", "low", "none"):
        body["reasoning"] = {"effort": reasoning}
    r, cont = {}, None
    async with sem:
        for a in range(4):
            try:
                r = (await c.post("https://openrouter.ai/api/v1/chat/completions", json=body)).json()
                cont = r["choices"][0]["message"]["content"] or ""
                break
            except Exception as e:
                r = {"err": repr(e)[:200]}; await asyncio.sleep(2 ** a)
    rec = {"id": x["id"], "kind": kind, "prefix": pre, "suffix": suf, "cont": cont, "served_by": r.get("provider"),
           "cost": (r.get("usage") or {}).get("cost")}
    if cont is not None:
        cn, sn = norm(cont), norm(suf)
        if cn.startswith(norm(pre)):
            cn = cn[len(norm(pre)):].strip()
        rec.update(exact=cn == sn, ratio=round(difflib.SequenceMatcher(None, cn, sn).ratio(), 4))
    return rec


async def main():
    sem = asyncio.Semaphore(6)
    async with httpx.AsyncClient(timeout=120, headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}) as c:
        recs = await asyncio.gather(*(one(c, sem, x, k) for x in items for k in PROMPTS))
    with open(out, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    cost = sum(r.get("cost") or 0 for r in recs)
    print(json.dumps({"out": str(out), "n": len(recs), "cost": round(cost, 6)}))

asyncio.run(main())
