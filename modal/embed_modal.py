# /// script
# requires-python = ">=3.11"
# dependencies = ["modal==1.5.5", "numpy"]
# ///
"""Sentence embeddings on Modal CPU for the nearest-neighbour diagnostic (DESIGN §4.3). Model:
BAAI/bge-small-en-v1.5 at a pinned revision, normalised vectors. No inference on the Mac.
usage: uv run modal/embed_modal.py <in.jsonl with id,text> <out.npz>"""
import json, sys
from pathlib import Path
import modal

MODEL = "BAAI/bge-small-en-v1.5"
REV = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
image = (modal.Image.debian_slim(python_version="3.12")
         .pip_install("sentence-transformers==3.3.1", "torch==2.5.1", "numpy<2.1")
         .run_commands(f"python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('{MODEL}', revision='{REV}')\""))
app = modal.App("m37-needle3-embed", image=image, tags={"project": "m37", "episode": "needle3"})


@app.function(cpu=2.0, memory=2048, timeout=1200)
def embed(texts):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(MODEL, revision=REV)
    return m.encode(texts, normalize_embeddings=True, batch_size=64).tolist()


if __name__ == "__main__":
    import numpy as np
    rows = [json.loads(l) for l in open(sys.argv[1])]
    with modal.enable_output(), app.run():
        v = embed.remote([r["text"] for r in rows])
    np.savez(sys.argv[2], ids=np.array([r["id"] for r in rows]), vecs=np.array(v, dtype=np.float32))
    print("wrote", sys.argv[2], len(rows))
