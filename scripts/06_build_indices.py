"""Chunk each corpus and build a Chroma vector index per condition.

Conditions:
  A — raw (source: data/raw_text/*.txt)
  B — summaries (source: data/corpora/summaries/*.md)
  C — wiki (source: data/corpora/wiki/*.md)
"""
import json
from pathlib import Path

import chromadb
import tiktoken

from common import ROOT, EMBED_MODEL, embed, print_cost

CHROMA_DIR = ROOT / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_TOKENS = 512
OVERLAP = 64

ENC = tiktoken.get_encoding("cl100k_base")

SOURCES = {
    "A_raw": ROOT / "data" / "raw_text",
    "B_summaries": ROOT / "data" / "corpora" / "summaries",
    "C_wiki": ROOT / "data" / "corpora" / "wiki",
}


def chunk(text: str, max_tok=CHUNK_TOKENS, overlap=OVERLAP) -> list[str]:
    tokens = ENC.encode(text)
    chunks = []
    step = max_tok - overlap
    i = 0
    while i < len(tokens):
        piece = tokens[i : i + max_tok]
        chunks.append(ENC.decode(piece))
        i += step
        if i + overlap >= len(tokens):
            break
    if not chunks:
        chunks = [text]
    return chunks


def iter_source(d: Path, condition: str):
    """Yield (doc_id, source_path, source_id, text) per chunk."""
    paths = sorted(list(d.glob("*.txt")) + list(d.glob("*.md")))
    for p in paths:
        text = p.read_text()
        if not text.strip():
            continue
        chunks = chunk(text)
        for idx, c in enumerate(chunks):
            # For raw/summaries, source_id = arxiv id (filename stem)
            # For wiki, source_id = page slug (may not map 1:1 to paper)
            yield (
                f"{condition}::{p.stem}::{idx}",
                str(p),
                p.stem,
                c,
            )


def build_index(condition: str, src_dir: Path):
    print(f"\n== {condition}: indexing {src_dir} ==")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # reset collection to ensure clean build
    try:
        client.delete_collection(condition)
    except Exception:
        pass
    coll = client.create_collection(condition, metadata={"hnsw:space": "cosine"})

    ids, docs, metas = [], [], []
    for cid, path, src_id, text in iter_source(src_dir, condition):
        ids.append(cid)
        docs.append(text)
        metas.append({"path": path, "source_id": src_id})
    print(f"  {len(docs)} chunks")

    embs = embed(docs)
    # bulk insert in batches
    BATCH = 256
    for i in range(0, len(ids), BATCH):
        coll.add(
            ids=ids[i : i + BATCH],
            documents=docs[i : i + BATCH],
            metadatas=metas[i : i + BATCH],
            embeddings=embs[i : i + BATCH],
        )
    print(f"  indexed {coll.count()} chunks")


def main():
    for cond, src in SOURCES.items():
        build_index(cond, src)
    print_cost()


if __name__ == "__main__":
    main()
