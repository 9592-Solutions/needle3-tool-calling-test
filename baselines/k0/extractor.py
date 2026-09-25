"""K0 rule-based argument extractor (standard library only).

extract(schema_tool, text, fact_line) -> dict | None   (None = refuse)
split(text) -> list[str]

Every value comes from one of: the schema's enum values and the synonyms its own descriptions
declare, a fixed polar-verb lexicon, digits / English number words, or a time/date grammar.
See AUTHOR-NOTES.md for the choices.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- triggers

def _load_triggers() -> dict[str, list[str]]:
    out: dict[str, set[str]] = {}
    for fn in ("triggers_S0.json", "triggers_S1.json"):
        p = os.path.join(HERE, fn)
        if os.path.exists(p):
            with open(p) as f:
                for k, v in json.load(f).items():
                    out.setdefault(k, set()).update(x.lower() for x in v)
    return {k: sorted(v, key=len, reverse=True) for k, v in out.items()}


TRIGGERS = _load_triggers()

B_L = r"(?<![\w'-])"
B_R = r"(?![\w'-])"


def _finditer(phrase: str, low: str):
    for m in re.finditer(B_L + re.escape(phrase) + B_R, low):
        yield m.start(), m.end()


def _overlaps(s, e, spans):
    return any(s < e2 and s2 < e for s2, e2 in spans)


def _trigger(name: str, low: str):
    """Earliest (then longest) trigger phrase match for this tool, as (start, end), or None."""
    phrases = TRIGGERS.get(name) or [w for w in name.split("_") if len(w) > 2]
    best = None
    for ph in phrases:
        for s, e in _finditer(ph, low):
            if best is None or s < best[0] or (s == best[0] and e > best[1]):
                best = (s, e)
            break
    return best


def _dist(span, anchor):
    if anchor is None:
        return span[0]
    s, e = span
    a, b = anchor
    if s < b and a < e:
        return 0
    return a - e if e <= a else s - b


# --------------------------------------------------------------------------- numbers

UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
_UNIT_ALT = "|".join(sorted(UNITS, key=len, reverse=True))
_TENS_ALT = "|".join(TENS)
NUMWORD = (rf"(?:(?:a|one)\s+hundred|(?:{_TENS_ALT})(?:[\s-](?:{_UNIT_ALT}))?|{_UNIT_ALT})")


def _word_value(w: str) -> int:
    w = w.strip()
    if "hundred" in w:
        return 100
    parts = re.split(r"[\s-]+", w)
    if parts[0] in TENS:
        return TENS[parts[0]] + (UNITS.index(parts[1]) if len(parts) > 1 else 0)
    return UNITS.index(parts[0])


def _numbers(low: str):
    """Yield (value, start, end) for digit numbers and English number words."""
    for m in re.finditer(r"(?<![\w.:/-])(\d+(?:\.\d+)?)(?![\w:/-]|\.\d)", low):
        v = m.group(1)
        yield (float(v) if "." in v else int(v)), m.start(), m.end()
    for m in re.finditer(B_L + NUMWORD + B_R, low):
        yield _word_value(m.group(0)), m.start(), m.end()


def _declared_number_words(desc: str) -> dict[str, int]:
    """Words the schema itself equates with a number, e.g. 'full or max is 100, half is 50'."""
    out = {}
    for m in re.finditer(r"((?:[a-z]+)(?:\s+or\s+[a-z]+)*)\s+is\s+(\d+)", desc.lower()):
        for w in re.split(r"\s+or\s+", m.group(1)):
            out[w] = int(m.group(2))
    return out


# --------------------------------------------------------------------------- enums

POLAR = {  # value -> (priority, cue phrases). Higher priority wins over lower; ties -> nearest.
    "on": (1, ["turn on", "switch on", "power on", "put on", "on", "enable", "activate"]),
    "off": (1, ["turn off", "switch off", "power off", "shut off", "turn out", "off", "out",
                "disable", "deactivate", "kill", "unplug"]),
    "dock": (3, ["dock", "base", "home", "charger", "recharge"]),
    "stop": (2, ["stop", "pause", "halt"]),
    "start": (1, ["start", "begin", "run", "resume", "clean", "vacuum", "hoover"]),
}


def _forms(v: str) -> set[str]:
    f = {v.lower(), v.lower().replace("_", " "), v.lower().replace("-", " ")}
    return {x for x in f if x}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _enum_synonyms(values, pdesc: str, tdesc: str) -> dict[str, set[str]]:
    syn = {v: _forms(v) for v in values}
    d = pdesc.lower()
    for v in values:
        for f in _forms(v):
            # 'value (syn, syn or syn)'
            for m in re.finditer(B_L + re.escape(f) + r"\s*\(([^)]*)\)", d):
                for s in re.split(r",|\bor\b", m.group(1)):
                    s = s.strip(" .'")
                    if s:
                        syn[v].add(s)
            # "'value' means X"
            for m in re.finditer(r"'" + re.escape(f) + r"'\s+means\s+([^;.]+)", d):
                syn[v].add(m.group(1).strip())
    # spellings in any description that normalise to the enum value ('to-do' -> 'todo')
    words = re.findall(r"[a-z0-9'-]+", (pdesc + " " + tdesc).lower())
    for n in (1, 2, 3):
        for i in range(len(words) - n + 1):
            g = " ".join(words[i:i + n])
            for v in values:
                if _norm(g) == _norm(v):
                    syn[v].add(g)
    return syn


def _enum_matches(values, syn, low, used):
    hits = []
    for v in values:
        for s in syn[v]:
            for a, b in _finditer(s, low):
                if not _overlaps(a, b, used):
                    hits.append((a, b, v))
    # drop matches contained in a longer match
    return [h for h in hits
            if not any(o is not h and o[0] <= h[0] and h[1] <= o[1] and (o[1] - o[0]) > (h[1] - h[0])
                       for o in hits)]


def _extend_noun(low, a, b, pname):
    """Swallow a following parameter noun ('shopping list') and a leading determiner/preposition."""
    m = re.match(r"\s+" + re.escape(pname) + B_R, low[b:])
    bonus = bool(m)
    if m:
        b += m.end()
    m = re.search(r"(?:\b(?:to|onto|from|into|for)\s+)?(?:\b(?:the|my|our)\s+)?$", low[:a])
    if m and m.group(0).strip():
        a = m.start()
    return a, b, bonus


# --------------------------------------------------------------------------- time / date

INVALID = object()
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]
_MON_ALT = "|".join(sorted(MONTHS + [m[:3] for m in MONTHS] + ["sept"], key=len, reverse=True))
AMPM = r"(a\.?\s?m\.?|p\.?\s?m\.?)"
_HOURWORD = "|".join(sorted(UNITS[1:13], key=len, reverse=True))


def _parse_fact(fact_line):
    if not fact_line:
        return None, None, "en-US"
    m = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})(?:\s+\w+)?(?:\s+(\d{1,2}):(\d{2}))?", fact_line)
    today = dt.date.fromisoformat(m.group(1)) if m else None
    now = dt.time(int(m.group(2)), int(m.group(3))) if (m and m.group(2)) else None
    loc = re.search(r"locale:\s*([\w-]+)", fact_line)
    return today, now, (loc.group(1) if loc else "en-US")


def _meridiem(h, tag, ctx):
    if tag:
        if not 1 <= h <= 12:
            return None
        pm = tag.replace(" ", "").startswith("p")
        return h % 12 + (12 if pm else 0)
    if ctx == "pm" and 1 <= h < 12:
        return h + 12
    if ctx == "am" and h == 12:
        return 0
    return h


def _num(tok: str) -> int:
    tok = tok.strip()
    return int(tok) if tok.isdigit() else _word_value(tok)


def _times(low, now):
    """Return list of (hh, mm | INVALID, start, end)."""
    ctx = None
    ctx_span = None
    m = re.search(r"\b(tonight|this evening|in the evening|at night|this afternoon|in the afternoon)\b", low)
    if m:
        ctx, ctx_span = "pm", (m.start(), m.end())
    m2 = re.search(r"\b(this morning|in the morning)\b", low)
    if m2 and not ctx:
        ctx, ctx_span = "am", (m2.start(), m2.end())
    out = []

    def add(h, mi, s, e, tag=None):
        h2 = _meridiem(h, tag, ctx)
        if h2 is None or not (0 <= h2 <= 23) or not (0 <= mi <= 59):
            out.append((INVALID, None, s, e))
        else:
            out.append((h2, mi, s, e))

    W = rf"(?:\d{{1,2}}|{_HOURWORD})"
    MINW = rf"(?:\d{{2}}|{NUMWORD}|oh[\s-](?:{_UNIT_ALT}))"
    # relative: in 20 minutes / in two hours / in an hour / in half an hour
    for m in re.finditer(rf"\bin\s+(an|a|half an|{NUMWORD}|\d+)\s+(minutes?|mins?|hours?|hrs?)\b", low):
        if now is None:
            continue
        q = m.group(1)
        n = 0.5 if q == "half an" else 1 if q in ("a", "an") else _num(q)
        mins = n * 60 if m.group(2).startswith("h") else n
        t = (dt.datetime.combine(dt.date(2000, 1, 1), now) + dt.timedelta(minutes=mins)).time()
        out.append((t.hour, t.minute, m.start(), m.end()))
    for m in re.finditer(rf"\b(\d{{1,2}}):(\d{{2}})(?:\s*{AMPM})?", low):
        add(int(m.group(1)), int(m.group(2)), m.start(), m.end(), m.group(3))
    for m in re.finditer(rf"\b(half past|quarter past|quarter to)\s+({W})(?:\s*{AMPM})?", low):
        h = _num(m.group(2))
        mi = {"half past": 30, "quarter past": 15, "quarter to": 45}[m.group(1)]
        if m.group(1) == "quarter to":
            h = h - 1 if h > 1 else 12
        add(h, mi, m.start(), m.end(), m.group(3))
    for m in re.finditer(rf"(?<![\w:])({W})(?:[\s-]({MINW}))?\s*(?:{AMPM}|(o'clock))(?![\w])", low):
        h = _num(m.group(1))
        mi_tok = m.group(2)
        mi = 0
        if mi_tok:
            mi_tok = re.sub(r"^oh[\s-]", "", mi_tok)
            mi = _num(mi_tok)
        add(h, mi, m.start(), m.end(), m.group(3))
    for m in re.finditer(r"\b(noon|midday|midnight)\b", low):
        out.append((12 if m.group(1) != "midnight" else 0, 0, m.start(), m.end()))
    # bare 'at 7' / 'at seven thirty' / 'at 0730'
    for m in re.finditer(rf"\bat\s+({W})(?:[\s-]({MINW}))?(?![\w:%])(?!\s*(?:%|percent|per cent|a\.?\s?m\b|p\.?\s?m\b|o'clock|:))", low):
        tok = m.group(1)
        if tok.isdigit() and len(tok) > 2:
            continue
        mi_tok = m.group(2)
        mi = _num(re.sub(r"^oh[\s-]", "", mi_tok)) if mi_tok else 0
        add(_num(tok), mi, m.start(), m.end())
    for m in re.finditer(r"\bat\s+(\d{2})(\d{2})\b", low):
        add(int(m.group(1)), int(m.group(2)), m.start(), m.end())
    # keep only maximal spans
    out = [o for o in out if not any(p is not o and p[2] <= o[2] and o[3] <= p[3]
                                     and (p[3] - p[2]) > (o[3] - o[2]) for p in out)]
    out.sort(key=lambda o: o[2])
    return out, (ctx_span if out else None)


def _dates(low, today, locale):
    """Return list of (date | INVALID, start, end)."""
    out = []
    if today is None:
        return out

    def mk(y, mo, d, s, e, roll=None):
        try:
            x = dt.date(y, mo, d)
        except ValueError:
            out.append((INVALID, s, e))
            return
        if roll == "year" and x < today:
            try:
                x = dt.date(y + 1, mo, d)
            except ValueError:
                out.append((INVALID, s, e))
                return
        out.append((x, s, e))

    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", low):
        mk(int(m.group(1)), int(m.group(2)), int(m.group(3)), m.start(), m.end())
    for m in re.finditer(r"\b(?:the\s+)?day after tomorrow\b", low):
        out.append((today + dt.timedelta(days=2), m.start(), m.end()))
    for m in re.finditer(r"\btomorrow\b", low):
        out.append((today + dt.timedelta(days=1), m.start(), m.end()))
    for m in re.finditer(r"\b(today|tonight)\b", low):
        out.append((today, m.start(), m.end()))
    for m in re.finditer(r"\b(?:(?:next|this|on)\s+)?(" + "|".join(WEEKDAYS) + r")\b", low):
        delta = (WEEKDAYS.index(m.group(1)) - today.weekday()) % 7 or 7
        out.append((today + dt.timedelta(days=delta), m.start(), m.end()))
    for m in re.finditer(rf"\bin\s+({NUMWORD}|\d+|a)\s+(days?|weeks?)\b", low):
        n = 1 if m.group(1) == "a" else _num(m.group(1))
        out.append((today + dt.timedelta(days=n * (7 if m.group(2).startswith("w") else 1)),
                    m.start(), m.end()))
    for m in re.finditer(rf"\b({_MON_ALT})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b", low):
        mo = _month(m.group(1))
        y = int(m.group(3)) if m.group(3) else today.year
        mk(y, mo, int(m.group(2)), m.start(), m.end(), None if m.group(3) else "year")
    for m in re.finditer(rf"\b(?:the\s+)?(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MON_ALT})\b(?:,?\s+(\d{{4}}))?", low):
        mo = _month(m.group(2))
        y = int(m.group(3)) if m.group(3) else today.year
        mk(y, mo, int(m.group(1)), m.start(), m.end(), None if m.group(3) else "year")
    for m in re.finditer(r"\b(?:on\s+)?the\s+(\d{1,2})(?:st|nd|rd|th)\b(?!\s+(?:of\s+)?[a-z]{3})", low):
        d = int(m.group(1))
        y, mo = today.year, today.month
        if d < today.day:
            mo += 1
            if mo == 13:
                y, mo = y + 1, 1
        mk(y, mo, d, m.start(), m.end())
    for m in re.finditer(r"(?<![\d/])(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?![\d/])", low):
        a, b = int(m.group(1)), int(m.group(2))
        mo, d = (b, a) if not locale.lower().endswith("us") else (a, b)
        y = m.group(3)
        if y:
            y = int(y) + (2000 if len(y) == 2 else 0)
            mk(y, mo, d, m.start(), m.end())
        else:
            mk(today.year, mo, d, m.start(), m.end(), "year")
    out = [o for o in out if not any(p is not o and p[1] <= o[1] and o[2] <= p[2]
                                     and (p[2] - p[1]) > (o[2] - o[1]) for p in out)]
    out.sort(key=lambda o: o[1])
    return out


def _month(tok):
    tok = tok.rstrip(".")
    for i, m in enumerate(MONTHS):
        if tok == m or tok == m[:3] or (tok == "sept" and i == 8):
            return i + 1
    raise ValueError(tok)


# --------------------------------------------------------------------------- free text

_LEAD = {"to", "about", "that", "of", "me", "please", "for"}
_TRAIL = {"to", "on", "onto", "from", "off", "for", "at", "in", "into", "by", "the", "my", "our",
          "please", "and", "then"}
_POLITE = re.compile(r"^\s*(?:please|hey|ok|okay|can you|could you|would you|will you)[\s,]+")


def _free_text(name, text, low, used):
    tr = _trigger(name, low)
    start = tr[1] if tr else 0
    # characters inside used spans become separators
    chars = list(text)
    for s, e in used:
        for i in range(max(s, 0), min(e, len(chars))):
            chars[i] = "\x00"
    if tr and tr[0] > 0:
        # a trigger that is not at the start (e.g. 'shopping list') is itself used
        pre = "".join(chars[:tr[0]])
        m = _POLITE.match(pre.lower())
        pre = pre[m.end():] if m else pre
        post = "".join(chars[tr[1]:])
        segs = pre.split("\x00") + post.split("\x00")
        # text before a non-initial trigger is a candidate first (e.g. 'milk' in 'milk on my list')
        # but a leading verb is stripped
        segs[0] = re.sub(r"^\s*(add|put|stick|remove|delete|take|cross|scratch|strike|drop|pack)\b", "", segs[0], flags=re.I)
    else:
        segs = "".join(chars[start:]).split("\x00")
    for seg in segs:
        toks = re.findall(r"[^\s]+", seg.replace(":", " ").strip())
        toks = [t.strip(",.!?") for t in toks]
        toks = [t for t in toks if t]
        while toks and toks[0].lower() in _LEAD:
            toks.pop(0)
        while toks and toks[-1].lower() in _TRAIL:
            toks.pop()
        if toks:
            return " ".join(toks)
    return None


# --------------------------------------------------------------------------- main

def extract(schema_tool: dict, text: str, fact_line: str | None) -> dict | None:
    fn = schema_tool.get("function", schema_tool)
    name = fn["name"]
    tdesc = fn.get("description", "")
    params = fn.get("parameters", {})
    props = params.get("properties", {})
    required = params.get("required", [])
    low = text.lower()
    anchor = _trigger(name, low)
    today, now, locale = _parse_fact(fact_line)
    used: list[tuple[int, int]] = []
    out: dict = {}

    kinds = {}
    for pname, p in props.items():
        if "enum" in p:
            kinds[pname] = "enum"
        elif p.get("type") in ("integer", "number"):
            kinds[pname] = "number"
        elif "HH:MM" in p.get("description", "") or (p.get("pattern", "").find(":[0-5]") >= 0):
            kinds[pname] = "time"
        elif p.get("format") == "date":
            kinds[pname] = "date"
        else:
            kinds[pname] = "text"

    # times and dates first, so their tokens are not reused
    for pname, k in kinds.items():
        if k == "time":
            ts, ctx_span = _times(low, now)
            if ts:
                h, mi, s, e = min(ts, key=lambda o: _dist((o[2], o[3]), anchor))
                if h is INVALID:
                    return None
                out[pname] = f"{h:02d}:{mi:02d}"
                used.append(_with_prep(low, s, e))
                if ctx_span:
                    used.append(ctx_span)
        elif k == "date":
            ds = _dates(low, today, locale)
            if ds:
                d, s, e = min(ds, key=lambda o: _dist((o[1], o[2]), anchor))
                if d is INVALID:
                    return None
                out[pname] = d.isoformat()
                used.append(_with_prep(low, s, e))
    # a date span like 'tonight' also lies inside time context; dedupe is harmless

    # polar enums (on/off, start/stop/dock) first: their cue words are the most specific evidence
    order = sorted(kinds, key=lambda n: not (kinds[n] == "enum" and set(props[n]["enum"]) & set(POLAR)))
    for pname in order:
        k = kinds[pname]
        p = props[pname]
        if k == "enum":
            values = p["enum"]
            syn = _enum_synonyms(values, p.get("description", ""), tdesc)
            hits = [(a, b, v, 0) for a, b, v in _enum_matches(values, syn, low, used)]
            # polar lexicon, mapped onto the schema's own values
            if set(values) & set(POLAR):
                for v in values:
                    if v in POLAR:
                        pr, cues = POLAR[v]
                        for c in cues:
                            for a, b in _finditer(c, low):
                                if not _overlaps(a, b, used):
                                    hits.append((a, b, v, pr))
                hits = [h for h in hits if not any(o is not h and o[0] <= h[0] and h[1] <= o[1]
                                                   and (o[1] - o[0]) > (h[1] - h[0]) for o in hits)]
            if not hits:
                continue
            scored = []
            for a, b, v, pr in hits:
                a2, b2, bonus = _extend_noun(low, a, b, pname)
                scored.append((-pr, -int(bonus), _dist((a, b), anchor), a2, b2, v))
            scored.sort()
            _, _, _, a2, b2, v = scored[0]
            out[pname] = v
            used.append((a2, b2))
        elif k == "number":
            desc = (p.get("description", "") + " " + tdesc)
            words = _declared_number_words(desc)
            percent = "percent" in desc.lower() or "%" in desc
            cands = []
            for v, a, b in _numbers(low):
                if _overlaps(a, b, used):
                    continue
                rest = low[b:]
                unit = bool(re.match(r"\s*(%|percent|per cent)", rest)) if percent else False
                if unit:
                    b += re.match(r"\s*(%|percent|per cent)", rest).end()
                pre_to = bool(re.search(r"\b(to|at)\s*$", low[:a]))
                cands.append((-int(unit), -int(pre_to), _dist((a, b), anchor), v, a, b))
            for w, v in words.items():
                for a, b in _finditer(w, low):
                    if not _overlaps(a, b, used):
                        cands.append((0, 0, _dist((a, b), anchor), v, a, b))
            if not cands:
                continue
            cands.sort(key=lambda c: c[:3])
            *_, v, a, b = cands[0]
            if p.get("type") == "integer" and (isinstance(v, float) and not float(v).is_integer()):
                return None
            v = int(v) if p.get("type") == "integer" else v
            if ("minimum" in p and v < p["minimum"]) or ("maximum" in p and v > p["maximum"]):
                return None
            out[pname] = v
            used.append((a, b))

    # conditional parameters: "Only used with action 'start'"
    for pname, p in props.items():
        m = re.search(r"only used with (\w+) '([^']+)'", p.get("description", "").lower())
        if m and pname in out and out.get(m.group(1)) != m.group(2):
            del out[pname]

    for pname, k in kinds.items():
        if k == "text":
            val = _free_text(name, text, low, used)
            if val:
                out[pname] = val

    for r in required:
        if r not in out:
            return None
    return out


def _with_prep(low, s, e):
    m = re.search(r"(?:\b(?:at|on|for|by|this|next|in)\s+)$", low[:s])
    return (m.start() if m else s), e


_SPLIT = [", then", ";", " and ", " then "]


def split(text: str) -> list[str]:
    parts = [text]
    for sep in _SPLIT:
        nxt = []
        for p in parts:
            nxt.extend(re.split(re.escape(sep), p, flags=re.I))
        parts = nxt
    out = []
    for p in parts:
        p = re.sub(r"^\s*then\s+", "", p.strip(), flags=re.I).strip(" ,")
        if p:
            out.append(p)
    return out
