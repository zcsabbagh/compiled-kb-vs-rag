"""Condition B: per-paper summaries with no cross-references."""
import json
from pathlib import Path

from common import ROOT, SONNET, chat, print_cost

RAW_TEXT = ROOT / "data" / "raw_text"
META = ROOT / "data" / "papers_meta.jsonl"
OUT = ROOT / "data" / "corpora" / "summaries"
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = """Summarize this paper's key contributions, methods, results, and limitations.
Do NOT reference or mention any other papers. Output as markdown with these sections:

# {title}

## Contributions
## Methods
## Key Results (include specific numbers where present)
## Limitations

Be comprehensive but concise (~800 words). Preserve quantitative claims verbatim.

PAPER TEXT:
{text}
"""


def main():
    meta = [json.loads(l) for l in open(META)]
    for i, p in enumerate(meta):
        dest = OUT / f"{p['id']}.md"
        if dest.exists():
            continue
        text_path = RAW_TEXT / f"{p['id']}.txt"
        if not text_path.exists():
            continue
        txt = text_path.read_text()[:30000]
        prompt = PROMPT.format(title=p["title"], text=txt)
        r = chat(
            SONNET,
            [
                {"role": "system", "content": "You write clear, faithful paper summaries."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
        )
        dest.write_text(r["content"])
        print(f"  [{i+1}/{len(meta)}] {p['id']} ({r['input_tokens']}→{r['output_tokens']} tok)")
    print_cost()


if __name__ == "__main__":
    main()
