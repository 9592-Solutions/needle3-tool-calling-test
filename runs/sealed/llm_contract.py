# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Needle 3 diagnostic "LLM with the contract in its prompt" (DESIGN §4.2, §5.3; FREEZE §8). Runs the frozen
harness/llm_arm.py unchanged, with its fixed system paragraph (SYSTEM_SCHEMA or SYSTEM_NATIVE) followed by a blank
line and the app's CONTRACT text (runs/sealed/contract_prompt_{home,desk}.txt: CONTRACT.md v1.1 §1 and the app's
section, verbatim, nothing else). The desk fact line and the tools are placed by llm_arm.build_body as in every
other call. Same arguments as llm_arm.py; the app is read from --schema.
"""
import asyncio, sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent.parent / "harness"))
import llm_arm  # noqa: E402


def patch(schema_id):
    app = llm_arm.app_of(schema_id)
    text = (H / f"contract_prompt_{app}.txt").read_text()
    llm_arm.SYSTEM_SCHEMA = llm_arm.SYSTEM_SCHEMA + "\n\n" + text
    llm_arm.SYSTEM_NATIVE = llm_arm.SYSTEM_NATIVE + "\n\n" + text


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--host", required=True)
    ap.add_argument("--contract", choices=["schema", "native"], required=True)
    ap.add_argument("--schema", required=True); ap.add_argument("--items", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--conc", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reasoning", default="off", choices=["off", "minimal", "none", "low", "omit"])
    ap.add_argument("--no-temp", action="store_true"); ap.add_argument("--lite", action="store_true")
    ap.add_argument("--no-require", action="store_true"); ap.add_argument("--max-tokens", type=int, default=600)
    a = ap.parse_args()
    patch(a.schema)
    asyncio.run(llm_arm.main(a))
