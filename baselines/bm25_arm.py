# /// script
# requires-python = ">=3.11"
# dependencies = ["bm25s==0.3.9", "PyStemmer==3.1.0", "numpy"]
# ///
"""K0 and K1 keyword baselines (DESIGN §4.3): BM25 over labelled phrases, top-k majority vote, refusal below a
score threshold tau or a vote margin mu, then the K0 author's rule-based argument extractor.

  K0 (schema-only): the documents are the blind author's trigger phrases for the schema (<= 15 per tool).
  K1 (example-fed): the documents are the lexical-bank requests with their agreed gold, labelled by the tool
      of a single-call gold, or "__none__" for a do-nothing gold (an engineer with labelled examples would
      index those too); multi-call and ambiguous items are not indexed.
Tokenisation: lowercase, split on non-alphanumerics, Snowball English stemming, NO stop-word removal
("on", "off", "up", "down" carry the meaning). Two actions: the request is split into clauses by the
author's split(); each clause is routed and extracted on its own; clauses that route to nothing or cannot
be filled yield no call. Only tau, mu and k are tuned (on dev); phrase lists and extractor rules never are.
"""
import json, re, sys
from pathlib import Path
import bm25s, Stemmer

H = Path(__file__).resolve().parent
ROOT = H.parent
sys.path.insert(0, str(H / "k0")); import extractor  # noqa: E402
sys.path.insert(0, str(ROOT / "contracts")); import mapping  # noqa: E402
STEM = Stemmer.Stemmer("english")
NONE = "__none__"
FACT = mapping.FACT_LINE


def tok(texts):
    return bm25s.tokenize([t.lower() for t in texts], stopwords=None, stemmer=STEM, show_progress=False)


def schema_tools(schema_id):
    ver, app = schema_id.split("-", 1)
    return json.loads((ROOT / "contracts" / ver / f"{app}.json").read_text())


class Router:
    def __init__(self, schema_id, docs):
        """docs: [(text, label)]"""
        self.schema_id = schema_id
        self.app = "desk" if "desk" in schema_id else "home"
        self.tools = {t["function"]["name"]: t for t in schema_tools(schema_id)}
        self.labels = [l for _, l in docs]
        self.retriever = bm25s.BM25()
        self.retriever.index(tok([t for t, _ in docs]), show_progress=False)

    def route(self, clause, k, tau, mu):
        k = min(k, len(self.labels))
        res, scores = self.retriever.retrieve(tok([clause]), k=k, show_progress=False)
        idx, sc = res[0], scores[0]
        if len(sc) == 0 or float(sc[0]) <= 0 or float(sc[0]) < tau:
            return None, {"top": float(sc[0]) if len(sc) else 0.0}
        votes, mass = {}, {}
        for i, s in zip(idx, sc):
            if s <= 0:
                continue
            l = self.labels[int(i)]
            votes[l] = votes.get(l, 0) + 1
            mass[l] = mass.get(l, 0.0) + float(s)
        ranked = sorted(votes, key=lambda l: (votes[l], mass[l]), reverse=True)
        top = ranked[0]
        margin = votes[top] - (votes[ranked[1]] if len(ranked) > 1 else 0)
        info = {"top": float(sc[0]), "votes": votes, "margin": margin}
        if top == NONE or margin < mu:
            return None, info
        return top, info

    def predict(self, text, k=5, tau=0.0, mu=0):
        calls, trace = [], []
        for clause in (extractor.split(text) or [text]):
            tool, info = self.route(clause, k, tau, mu)
            args = None
            if tool is not None:
                args = extractor.extract(self.tools[tool], clause, FACT if self.app == "desk" else None)
            trace.append({"clause": clause, "tool": tool, "args": args, **info})
            if tool is not None and args is not None:
                calls.append({"name": tool, "arguments": args})
        return calls, trace


def k0_docs(schema_id):
    ver = schema_id.split("-")[0]
    trig = json.loads((H / "k0" / f"triggers_{ver}.json").read_text())
    names = {t["function"]["name"] for t in schema_tools(schema_id)}
    return [(p, name) for name, ps in trig.items() if name in names for p in ps]


def k1_docs(schema_id, bank, include_none=False):
    """bank: [{"text", "gold"}] agreed gold in canonical form; label = the schema's tool for the one call."""
    table = mapping.TABLES[schema_id]
    inv = {}
    for raw, (action, _) in table.items():
        inv.setdefault(action, raw)
    docs = []
    for b in bank:
        g = b["gold"]
        if g == "ambiguous" or len(g) != 1:
            continue
        ans = g[0]
        if len(ans) == 0:
            if include_none:
                docs.append((b["text"], NONE))
        elif len(ans) == 1 and ans[0]["action"] in inv:
            docs.append((b["text"], inv[ans[0]["action"]]))
    return docs


def k1_bank_docs(schema_id, old_bank):
    """D8 bank: the intent-labelled rows of k1_bank/bank.json (S1 tool names; S0 shares them) plus the first bank's
    gold-labelled single-call act items."""
    app = "desk" if "desk" in schema_id else "home"
    bank = json.loads((H / "k1_bank" / "bank.json").read_text())[app]
    names = {t["function"]["name"] for t in schema_tools(schema_id)}
    docs = [(b["text"], b["tool"]) for b in bank if b["tool"] in names]
    return docs + k1_docs(schema_id, old_bank, include_none=False)
