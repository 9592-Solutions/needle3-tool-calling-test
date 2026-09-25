"""Needle 3 step 10, BEFORE any aggregate: the raw-output reading sample (DESIGN §10 step 10). For every
(arm x schema x outcome) cell on test, the first three items in FREEZE §11 display order (both apps, labelled), plus
EVERY technical failure in any run (test, band F, anchors), plus every band F item: request text, gold, what the arm
returned (raw), and the outcome the scorer assigns. Prints no rate, no count of correct items, no aggregate; it writes
results/AUDIT-SAMPLE.md for a human (or agent) to read end to end and confirm each item is classified as what it is.
usage: uv run --no-project --with numpy --with jsonschema==4.26.0 python results/audit_dump.py
"""
import hashlib, json
from pathlib import Path

import score_test as T
from score_test import score

TXT = {}
for p in T.INP.glob("*.jsonl"):
    for l in open(p):
        r = json.loads(l); TXT[r["id"]] = r["text"]


def order(ids):
    return sorted(ids, key=lambda i: hashlib.sha256(("needle3-display-2026-09-22:" + i).encode()).hexdigest())


def raw_excerpt(p):
    if p is None:
        return "(no output)"
    if p.get("unserved"):
        return f"UNSERVED: {json.dumps(p.get('raw'))[:300]}"
    raw = p.get("raw")
    if isinstance(raw, dict) and "function_calls" in raw:     # Needle envelope
        keep = {k: raw.get(k) for k in ("success", "error", "error_code", "reason", "function_calls", "suppressed_calls",
                                        "confidence", "validation", "reasoning")}
        return json.dumps(keep, ensure_ascii=False)[:900]
    if isinstance(raw, dict) and "choices" in raw:
        m = raw["choices"][0].get("message", {})
        return json.dumps({"content": m.get("content"), "tool_calls": m.get("tool_calls")}, ensure_ascii=False)[:900]
    return json.dumps(raw, ensure_ascii=False)[:900]


def block(lines, label, k, p, outcome):
    lines += [f"- **{label}** `{k['id']}` ({k['app']}/{k.get('stratum')}) outcome **{outcome}**",
              f"  - text: {TXT.get(k['id'], '?')!r}",
              f"  - gold: `{json.dumps(k['gold'], ensure_ascii=False)[:400]}`",
              f"  - returned (what the app receives): `{json.dumps(None if p is None or p.get('unserved') else p.get('pred'), ensure_ascii=False)[:400]}`"
              + (f" tf={p.get('tf')}" if p and p.get("tf") else ""),
              f"  - raw: `{raw_excerpt(p)}`"]


def main():
    test = T.load_keys("test", True); band = T.load_keys("bandF", False); diag = T.load_keys("diagnostics", False)
    lines = ["# Needle 3 step 10: raw-output reading sample (no aggregates)", "",
             "Written by results/audit_dump.py before results/score_test.py is run. Three items per (arm x schema x outcome) "
             "cell in FREEZE §11 display order, every technical failure, every band F item.", ""]
    runs = {}
    for ver in ("S1", "S0"):
        runs[("needle", ver)] = {**(T.needle_file(f"needle_{ver}_home_test") or {}), **(T.needle_file(f"needle_{ver}_desk_test") or {})}
        for arm in ("llm-a", "llm-named"):
            runs[(arm, ver)] = {**(T.llm_file(arm, f"test_{ver}_home") or {}), **(T.llm_file(arm, f"test_{ver}_desk") or {})}
        for arm in ("K0", "K1", "K1-firstbank", "K1-firstbank-none"):
            runs[(arm, ver)] = {**(T.base_file(f"{arm}_{ver}_home_test") or {}), **(T.base_file(f"{arm}_{ver}_desk_test") or {})}
    runs[("hassil", "S1")] = T.base_file("hassil_S1_home_test") or {}
    for (arm, ver), preds in runs.items():
        preds.pop("__missing__", None)
        lines += [f"## {arm} / {ver} (test)", ""]
        cells = {}
        for i, k in test.items():
            if arm == "hassil" and k["app"] != "home":
                continue
            p = preds.get(i)
            if p is None:
                oc = "missing"
            elif p.get("unserved"):
                oc = "unserved"
            else:
                oc = score.score_item(k["gold"], p["pred"], f"{ver}-{k['app']}")["outcome"]
            cells.setdefault(oc, []).append(i)
        for oc in sorted(cells):
            lines += [f"### {arm} / {ver} / {oc}", ""]
            show = order(cells[oc])[:3] if oc != "technical_failure" else order(cells[oc])
            for i in show:
                block(lines, f"{arm} {ver}", test[i], preds.get(i), oc)
            lines.append("")
    lines += ["## Technical failures outside test (band F, anchors, variants)", ""]
    for f in sorted((T.O / "needle").glob("*.json")):
        name = f.stem
        if name.endswith("_test"):
            continue
        preds = T.needle_file(name); preds.pop("__missing__", None)
        for i, p in preds.items():
            if p["pred"] is None:
                k = band.get(i) or diag.get(i) or test.get(i)
                block(lines, name, k, p, "technical_failure")
    for arm in ("llm-a", "llm-named"):
        for f in sorted((T.O / "llm" / arm).glob("*.jsonl")):
            if f.stem.startswith("test_"):
                continue
            preds = T.llm_file(arm, f.stem)
            for i, p in preds.items():
                if p.get("unserved") or p["pred"] is None:
                    k = band.get(i) or diag.get(i) or test.get(i)
                    block(lines, f"{arm} {f.stem}", k, p, "unserved" if p.get("unserved") else "technical_failure")
    lines += ["", "## Band F, every request, every arm (S1)", ""]
    bruns = {"needle": {**(T.needle_file("needle_S1_home_bandF") or {}), **(T.needle_file("needle_S1_desk_bandF") or {})}}
    for arm in ("llm-a", "llm-named"):
        bruns[arm] = {**(T.llm_file(arm, "bandF_S1_home") or {}), **(T.llm_file(arm, "bandF_S1_desk") or {})}
    for arm in ("K0", "K1"):
        bruns[arm] = {**(T.base_file(f"{arm}_S1_home_bandF") or {}), **(T.base_file(f"{arm}_S1_desk_bandF") or {})}
    bruns["hassil"] = T.base_file("hassil_S1_home_bandF") or {}
    for i in order(band):
        k = band[i]
        for arm, preds in bruns.items():
            p = preds.get(i)
            if arm == "hassil" and k["app"] != "home":
                continue
            oc = "missing" if p is None else "unserved" if p.get("unserved") else score.score_item(k["gold"], p["pred"], f"S1-{k['app']}")["outcome"]
            block(lines, f"{arm} bandF", k, p, oc)
        lines.append("")
    out = T.R / "AUDIT-SAMPLE.md"
    out.write_text("\n".join(lines))
    print("wrote", out, "lines", len(lines))


if __name__ == "__main__":
    main()
