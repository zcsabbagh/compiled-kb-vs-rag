"""LLM-judge evaluation.

For each (condition, model, question) answer, we ask Sonnet to score:
  - correctness (1-5)
  - faithfulness (bool + list of unsupported claims)

Plus two tier-specific metrics computed directly:
  - coverage (tier 2 synthesis): fraction of gold source papers surfaced in answer
  - contradiction_detected (tier 3): did the answer explicitly name a disagreement?
"""
import json
import re
from pathlib import Path

from common import ROOT, SONNET, chat, print_cost

RAW = ROOT / "results" / "raw_results.jsonl"
OUT = ROOT / "results" / "judged_results.jsonl"


CORRECTNESS_PROMPT = """You are evaluating an answer against a gold answer.

QUESTION: {question}

GOLD ANSWER: {gold}

GENERATED ANSWER: {answer}

Rate correctness on 1-5:
  1 = completely wrong or irrelevant
  2 = mostly wrong, one correct fragment
  3 = partially correct; misses major details or includes errors
  4 = largely correct with minor omissions or imprecision
  5 = fully correct; captures the essence and key specifics of the gold

Respond with JSON only:
{{"score": int, "reasoning": "short"}}
"""

FAITHFUL_PROMPT = """Does the generated answer contain claims NOT supported by the retrieved context?

CONTEXT:
{context}

ANSWER: {answer}

Respond with JSON only:
{{"faithful": true|false, "unsupported_claims": ["..."]}}
A claim counts as supported if the context plausibly backs it, even if paraphrased.
"""


def parse_json(txt: str) -> dict:
    txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.M)
    txt = re.sub(r"\s*```$", "", txt.strip(), flags=re.M)
    try:
        return json.loads(txt)
    except Exception:
        pass
    # try to find a {...} block
    m = re.search(r"\{.*\}", txt, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


def coverage(record: dict) -> float:
    """Fraction of gold source papers referenced in the answer."""
    srcs = record.get("source_paper_ids") or []
    if not srcs:
        return 0.0
    ans = record["answer"]
    hit = 0
    for sid in srcs:
        # arxiv ids like "2604.03391"; also try dash-form
        if sid in ans or sid.replace(".", "-") in ans or sid.replace(".", "") in ans:
            hit += 1
    return hit / len(srcs)


def contradiction_detected(record: dict) -> bool:
    """Heuristic: answer mentions two differing positions."""
    a = record["answer"].lower()
    markers = [
        "disagree",
        "contradict",
        "conflict",
        "opposite",
        "however",
        "whereas",
        "in contrast",
        "on the other hand",
        "differ",
    ]
    has_marker = any(m in a for m in markers)
    # also require >=2 paper ids to be cited
    srcs = record.get("source_paper_ids") or []
    hits = sum(1 for sid in srcs if sid in record["answer"])
    return has_marker and hits >= 2


def load_done() -> set[tuple]:
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
    results = [json.loads(l) for l in open(RAW)]
    print(f"Loaded {len(results)} raw results")
    done = load_done()
    print(f"Already judged: {len(done)}")

    out_f = open(OUT, "a")
    for i, rec in enumerate(results):
        key = (rec["question_id"], rec["condition"], rec["model"])
        if key in done:
            continue

        # correctness
        cr = chat(
            SONNET,
            [
                {"role": "system", "content": "Output JSON only."},
                {
                    "role": "user",
                    "content": CORRECTNESS_PROMPT.format(
                        question=rec["question"],
                        gold=rec["gold_answer"],
                        answer=rec["answer"],
                    ),
                },
            ],
            max_tokens=300,
        )
        c_obj = parse_json(cr["content"])
        score = c_obj.get("score")
        if not isinstance(score, int) or not (1 <= score <= 5):
            score = None

        # faithfulness
        fr = chat(
            SONNET,
            [
                {"role": "system", "content": "Output JSON only."},
                {
                    "role": "user",
                    "content": FAITHFUL_PROMPT.format(
                        context=rec["context"][:8000], answer=rec["answer"]
                    ),
                },
            ],
            max_tokens=400,
        )
        f_obj = parse_json(fr["content"])
        faithful = f_obj.get("faithful")
        unsupported = f_obj.get("unsupported_claims") or []

        cov = coverage(rec) if rec["tier"] == "synthesis" else None
        contra = contradiction_detected(rec) if rec["tier"] == "contradiction" else None

        judged = {
            "question_id": rec["question_id"],
            "tier": rec["tier"],
            "condition": rec["condition"],
            "model": rec["model"],
            "correctness_score": score,
            "correctness_reasoning": c_obj.get("reasoning", ""),
            "faithful": faithful,
            "unsupported_claims": unsupported,
            "coverage": cov,
            "contradiction_detected": contra,
            "input_tokens": rec["input_tokens"],
            "output_tokens": rec["output_tokens"],
        }
        out_f.write(json.dumps(judged) + "\n")
        out_f.flush()
        short = rec["model"].split("/")[-1][:18]
        print(
            f"  [{i+1}/{len(results)}] {rec['question_id']}/{rec['condition']}/{short}  "
            f"score={score} faith={faithful}"
        )
    out_f.close()
    print_cost()


if __name__ == "__main__":
    main()
