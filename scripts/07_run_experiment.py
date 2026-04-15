"""Run the retrieval+generation experiment across (condition x model x question).

For each triple:
  - embed question
  - retrieve top-k (k=5) chunks from condition's Chroma collection
  - generate answer with generator model using ONLY provided context
  - log usage + retrieved chunks + answer

Raw results go to results/raw_results.jsonl.
"""
import json
import os
from pathlib import Path

import chromadb

from common import ROOT, SONNET, LLAMA8B, chat, embed, print_cost

K = int(os.environ.get("K", 5))
CHROMA_DIR = ROOT / "chroma"
CONDITIONS = ["A_raw", "B_summaries", "C_wiki"]
MODELS = [LLAMA8B, SONNET]

QUESTIONS = ROOT / "data" / "questions.jsonl"
OUT = ROOT / "results" / "raw_results.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

SYSTEM = (
    "You are a research assistant. Answer the question using ONLY the provided context. "
    "If the context is insufficient, say so. Cite specific papers or wiki pages when possible. "
    "Be concise."
)


def fmt_context(hits) -> str:
    parts = []
    for i, (doc, meta) in enumerate(hits):
        src = meta.get("source_id", "?")
        parts.append(f"[chunk {i+1} | source={src}]\n{doc}")
    return "\n\n".join(parts)


def load_completed() -> set[str]:
    done = set()
    if OUT.exists():
        for line in open(OUT):
            try:
                r = json.loads(line)
                done.add((r["question_id"], r["condition"], r["model"]))
            except Exception:
                pass
    return done


def main():
    questions = [json.loads(l) for l in open(QUESTIONS)]
    print(f"Loaded {len(questions)} questions")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collections = {c: client.get_collection(c) for c in CONDITIONS}

    # pre-embed all question texts (cached)
    q_texts = [q["question"] for q in questions]
    q_embs = embed(q_texts)
    q_emb_map = {q["id"]: q_embs[i] for i, q in enumerate(questions)}

    done = load_completed()
    print(f"Already have {len(done)} completed (condition,model,q) triples")

    out_f = open(OUT, "a")
    total = len(questions) * len(CONDITIONS) * len(MODELS)
    n = 0
    for q in questions:
        for cond in CONDITIONS:
            # retrieve once per (q, cond); share across models
            res = collections[cond].query(
                query_embeddings=[q_emb_map[q["id"]]],
                n_results=K,
                include=["documents", "metadatas"],
            )
            docs = res["documents"][0]
            metas = res["metadatas"][0]
            hits = list(zip(docs, metas))
            context = fmt_context(hits)
            retrieved_sources = [m.get("source_id", "?") for m in metas]

            for model in MODELS:
                n += 1
                key = (q["id"], cond, model)
                if key in done:
                    continue
                user_prompt = (
                    f"CONTEXT:\n{context}\n\nQUESTION: {q['question']}\n\n"
                    "Answer based only on the context above."
                )
                try:
                    r = chat(
                        model,
                        [
                            {"role": "system", "content": SYSTEM},
                            {"role": "user", "content": user_prompt},
                        ],
                        max_tokens=500,
                    )
                except Exception as e:
                    print(f"  [{n}/{total}] {q['id']}/{cond}/{model.split('/')[-1]} FAIL: {e}")
                    continue
                rec = {
                    "question_id": q["id"],
                    "tier": q["tier"],
                    "condition": cond,
                    "model": model,
                    "k": K,
                    "question": q["question"],
                    "gold_answer": q["gold_answer"],
                    "source_paper_ids": q["source_paper_ids"],
                    "retrieved_sources": retrieved_sources,
                    "context": context,
                    "answer": r["content"],
                    "input_tokens": r["input_tokens"],
                    "output_tokens": r["output_tokens"],
                }
                out_f.write(json.dumps(rec) + "\n")
                out_f.flush()
                short = model.split("/")[-1][:18]
                print(
                    f"  [{n}/{total}] {q['id']}/{cond}/{short}  tok {r['input_tokens']}→{r['output_tokens']}"
                )
    out_f.close()
    print_cost()


if __name__ == "__main__":
    main()
