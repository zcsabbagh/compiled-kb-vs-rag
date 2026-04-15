"""Generate 3-tier question set with Sonnet.

Tier 1 (factual):      single-paper questions answerable from one paper.
Tier 2 (synthesis):    2-4 papers required to answer.
Tier 3 (contradiction): expose a disagreement across papers.
"""
import json
import random
import re
from pathlib import Path

from common import (
    ROOT,
    SONNET,
    chat,
    N_FACTUAL,
    N_SYNTHESIS,
    N_CONTRADICTION,
    print_cost,
)

random.seed(42)

RAW_TEXT = ROOT / "data" / "raw_text"
META = ROOT / "data" / "papers_meta.jsonl"
OUT = ROOT / "data" / "questions.jsonl"


def load_papers():
    meta = [json.loads(l) for l in open(META)]
    # keep only those with extracted text
    return [p for p in meta if (RAW_TEXT / f"{p['id']}.txt").exists()]


def paper_text(pid: str, max_chars=20000) -> str:
    return (RAW_TEXT / f"{pid}.txt").read_text()[:max_chars]


def parse_jsonl_block(txt: str) -> list[dict]:
    """Extract JSON objects from a model response (tolerates code fences, prose)."""
    # strip fences
    txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.M)
    txt = re.sub(r"\s*```$", "", txt.strip(), flags=re.M)
    out = []
    # try line-delimited first
    for line in txt.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    if out:
        return out
    # fall back: try array
    try:
        arr = json.loads(txt)
        if isinstance(arr, list):
            return arr
        if isinstance(arr, dict):
            return [arr]
    except Exception:
        pass
    # last resort: find {...} spans
    depth = 0
    start = None
    for i, ch in enumerate(txt):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = txt[start : i + 1]
                try:
                    out.append(json.loads(chunk))
                except Exception:
                    pass
                start = None
    return out


FACTUAL_PROMPT = """You are creating an evaluation question for a research-assistant RAG system.

Below is the text of an arXiv paper on RLHF/RLAIF. Produce ONE factual question that:
- has a single, specific, unambiguous correct answer grounded in this paper
- would be hard to answer without reading this specific paper
- is NOT trivially about the paper's title or authors
- focuses on a concrete method detail, quantitative result, or specific claim

Respond with ONE JSON line only, no prose, no fences:
{"question": str, "gold_answer": str}

PAPER (id=PAPER_ID):
PAPER_TEXT
"""


SYNTHESIS_PROMPT = """You are creating an evaluation question for a research-assistant RAG system.

Below are short excerpts from 2-4 arXiv papers on RLHF/RLAIF. Produce ONE synthesis question that:
- requires information from AT LEAST 2 of the provided papers to answer well
- is specific and has a concrete gold answer (not "compare and contrast broadly")
- good examples: "How do papers X and Y differ in how they estimate reward uncertainty?" or "Which of the provided methods achieves the best result on benchmark Z and by how much?"

Respond with ONE JSON line only:
{"question": str, "gold_answer": str, "required_paper_ids": [str, ...]}

PAPERS:
PAPERS_BLOCK
"""


CONTRADICTION_PROMPT = """You are creating hard evaluation questions for a research-assistant RAG system.

Below are abstracts from several arXiv papers on RLHF/RLAIF. Identify CONTRADICTION_N pairs (or small groups) of papers that make genuinely conflicting empirical or theoretical claims. For each contradiction, produce ONE question that asks the system to surface the disagreement.

A good contradiction question:
- asks about a specific claim where the papers genuinely disagree
- has a gold answer that explicitly names both positions and the papers that hold them
- AVOID fake contradictions about different settings / scopes

Respond with EXACTLY CONTRADICTION_N JSON lines, one per line, no prose, no fences:
{"question": str, "gold_answer": str, "required_paper_ids": [str, str]}

ABSTRACTS:
ABSTRACTS_BLOCK
"""


def gen_factual(papers, n):
    chosen = random.sample(papers, min(n, len(papers)))
    out = []
    for i, p in enumerate(chosen):
        prompt = FACTUAL_PROMPT.replace("PAPER_ID", p["id"]).replace(
            "PAPER_TEXT", paper_text(p["id"], max_chars=18000)
        )
        r = chat(
            SONNET,
            [
                {"role": "system", "content": "Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        objs = parse_jsonl_block(r["content"])
        if not objs:
            print(f"  [factual] parse fail for {p['id']}: {r['content'][:120]}")
            continue
        q = objs[0]
        out.append(
            {
                "id": f"f{i:03d}",
                "tier": "factual",
                "question": q.get("question", "").strip(),
                "gold_answer": q.get("gold_answer", "").strip(),
                "source_paper_ids": [p["id"]],
            }
        )
        print(f"  [{i+1}/{len(chosen)}] factual {p['id']}")
    return out


def gen_synthesis(papers, n):
    out = []
    for i in range(n):
        k = random.choice([2, 3])
        grp = random.sample(papers, k)
        block = ""
        for p in grp:
            block += f"\n--- PAPER {p['id']} ---\nTitle: {p['title']}\nAbstract: {p['abstract']}\n\nText excerpt:\n{paper_text(p['id'], max_chars=5000)}\n"
        prompt = SYNTHESIS_PROMPT.replace("PAPERS_BLOCK", block)
        r = chat(
            SONNET,
            [
                {"role": "system", "content": "Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        objs = parse_jsonl_block(r["content"])
        if not objs:
            print(f"  [synthesis] parse fail: {r['content'][:120]}")
            continue
        q = objs[0]
        srcs = q.get("required_paper_ids") or [p["id"] for p in grp]
        out.append(
            {
                "id": f"s{i:03d}",
                "tier": "synthesis",
                "question": q.get("question", "").strip(),
                "gold_answer": q.get("gold_answer", "").strip(),
                "source_paper_ids": srcs,
            }
        )
        print(f"  [{i+1}/{n}] synthesis {srcs}")
    return out


def gen_contradictions(papers, n):
    """One batched call: pass all abstracts, ask for n contradictions."""
    block = "\n\n".join(
        f"--- {p['id']} | {p['title']} ---\n{p['abstract']}" for p in papers
    )
    prompt = CONTRADICTION_PROMPT.replace("CONTRADICTION_N", str(n)).replace(
        "ABSTRACTS_BLOCK", block
    )
    r = chat(
        SONNET,
        [
            {"role": "system", "content": "Output JSON only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2500,
    )
    objs = parse_jsonl_block(r["content"])
    out = []
    for i, q in enumerate(objs[:n]):
        out.append(
            {
                "id": f"c{i:03d}",
                "tier": "contradiction",
                "question": q.get("question", "").strip(),
                "gold_answer": q.get("gold_answer", "").strip(),
                "source_paper_ids": q.get("required_paper_ids", []),
            }
        )
    print(f"  [contradiction] produced {len(out)}")
    return out


def main():
    papers = load_papers()
    print(f"Loaded {len(papers)} papers")

    qs = []
    print("\n== Factual ==")
    qs += gen_factual(papers, N_FACTUAL)
    print("\n== Synthesis ==")
    qs += gen_synthesis(papers, N_SYNTHESIS)
    print("\n== Contradiction ==")
    qs += gen_contradictions(papers, N_CONTRADICTION)

    # filter empty
    qs = [q for q in qs if q["question"] and q["gold_answer"]]
    with open(OUT, "w") as f:
        for q in qs:
            f.write(json.dumps(q) + "\n")
    print(f"\nWrote {len(qs)} questions -> {OUT}")
    print_cost()


if __name__ == "__main__":
    main()
