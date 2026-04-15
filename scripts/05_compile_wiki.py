"""Condition C: compile the corpus into an interlinked wiki.

Architecture (Karpathy-style):
- Pages live in data/corpora/wiki/<slug>.md
- Content uses [[wikilinks]] to refer to other pages by slug
- Papers are processed in batches; each batch the model can CREATE or UPDATE pages
- Final lint pass catches unlinked references and creates an index page
"""
import json
import re
from pathlib import Path

from common import (
    ROOT,
    SONNET,
    chat,
    BATCH_SIZE_WIKI,
    print_cost,
)

RAW_TEXT = ROOT / "data" / "raw_text"
META = ROOT / "data" / "papers_meta.jsonl"
OUT = ROOT / "data" / "corpora" / "wiki"
OUT.mkdir(parents=True, exist_ok=True)

BATCH_PROMPT = """You are compiling a research wiki on RLHF/RLAIF from a set of arXiv papers. The wiki
has interlinked pages for concepts, methods, benchmarks, and papers. Pages use Markdown with
[[page-slug]] wikilinks to reference other pages. Page slugs are lowercase-hyphenated.

EXISTING WIKI STATE (may be empty if this is the first batch):
WIKI_STATE

NEW PAPERS IN THIS BATCH:
BATCH_PAPERS

Your job: emit a series of operations to update the wiki so it absorbs the new papers'
content and weaves it into the existing knowledge graph. Guidelines:
- For each new paper, CREATE a page at slug `paper-<arxiv_id>` summarising its contributions,
  methods, and key quantitative results. Use [[wikilinks]] to concepts it uses.
- UPDATE existing concept/method pages to incorporate findings from new papers.
- CREATE new pages for novel concepts/methods/benchmarks introduced by the new papers.
- Concept/method page slugs are lowercase-hyphenated names, e.g. `reward-hacking`, `dpo`.
- Every page MUST contain wikilinks to related pages. Cite papers as [[paper-<id>]].
- Keep pages focused; ~150-400 words each.

Output FORMAT: one JSON object per line, no fences, no prose. Each object is one operation:
{"op": "create"|"update", "slug": "<page-slug>", "content": "<full markdown content>"}

For UPDATE, return the FULL new content of the page (not a diff).
Emit only operations needed for this batch. Aim for 5-15 operations per batch.
"""

LINT_PROMPT = """You are finalizing a research wiki.

Here are all pages. Perform a final lint pass:
1. Identify any [[wikilinks]] that reference slugs not present -> either create those pages or fix links
2. Identify contradictions between pages -> note them in the relevant pages
3. CREATE an `index` page listing major concepts, methods, benchmarks with [[wikilinks]]

Existing pages:
WIKI_STATE

Output one JSON op per line (create/update), same format as before.
Limit to at most 15 ops. The 'index' page is required.
"""


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80]


def load_wiki_state() -> dict[str, str]:
    state = {}
    for p in sorted(OUT.glob("*.md")):
        state[p.stem] = p.read_text()
    return state


def save_page(slug: str, content: str):
    (OUT / f"{slug}.md").write_text(content)


def render_state(state: dict[str, str], max_chars=None) -> str:
    """Render current wiki as a text block."""
    if not state:
        return "(empty — this is the first batch)"
    parts = []
    for slug, content in sorted(state.items()):
        parts.append(f"--- [[{slug}]] ---\n{content.strip()}")
    out = "\n\n".join(parts)
    if max_chars and len(out) > max_chars:
        out = out[:max_chars] + "\n\n...(truncated)..."
    return out


def parse_ops(txt: str) -> list[dict]:
    txt = re.sub(r"^```(?:json)?\s*", "", txt.strip(), flags=re.M)
    txt = re.sub(r"\s*```$", "", txt.strip(), flags=re.M)
    ops = []
    # JSONL
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ops.append(json.loads(line))
            continue
        except Exception:
            pass
    if ops:
        return ops
    # Fallback: brace matching, may span lines
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(txt):
        if esc:
            esc = False
            continue
        if ch == "\\" and in_str:
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = txt[start : i + 1]
                try:
                    ops.append(json.loads(chunk))
                except Exception:
                    pass
                start = None
    return ops


def apply_ops(ops: list[dict], state: dict[str, str]):
    applied = 0
    for op in ops:
        slug = slugify(op.get("slug", ""))
        content = op.get("content", "")
        if not slug or not content:
            continue
        state[slug] = content
        save_page(slug, content)
        applied += 1
    return applied


def batch_papers(meta: list[dict], size: int):
    for i in range(0, len(meta), size):
        yield meta[i : i + size]


def main():
    meta = [json.loads(l) for l in open(META)]
    state = load_wiki_state()
    print(f"Starting wiki compile: {len(meta)} papers, batch={BATCH_SIZE_WIKI}")
    print(f"Existing pages on disk: {len(state)}")

    batches = list(batch_papers(meta, BATCH_SIZE_WIKI))

    for bi, batch in enumerate(batches):
        print(f"\n== Batch {bi+1}/{len(batches)} ({len(batch)} papers) ==")
        # Build batch papers block
        block = ""
        for p in batch:
            txt = (RAW_TEXT / f"{p['id']}.txt").read_text()[:15000]
            block += f"\n--- arxiv:{p['id']} | {p['title']} ---\n{txt}\n"
        state_str = render_state(state, max_chars=60000)
        prompt = BATCH_PROMPT.replace("WIKI_STATE", state_str).replace("BATCH_PAPERS", block)
        r = chat(
            SONNET,
            [
                {
                    "role": "system",
                    "content": "You compile research wikis. Output JSONL operations only.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=8000,
        )
        ops = parse_ops(r["content"])
        applied = apply_ops(ops, state)
        print(
            f"  ops parsed={len(ops)} applied={applied} | tokens {r['input_tokens']}→{r['output_tokens']}"
        )

    # Lint pass
    print(f"\n== Lint pass ==")
    state_str = render_state(state, max_chars=100000)
    r = chat(
        SONNET,
        [
            {
                "role": "system",
                "content": "You finalize research wikis. Output JSONL operations only.",
            },
            {"role": "user", "content": LINT_PROMPT.replace("WIKI_STATE", state_str)},
        ],
        max_tokens=6000,
    )
    ops = parse_ops(r["content"])
    applied = apply_ops(ops, state)
    print(
        f"  lint ops={len(ops)} applied={applied} | tokens {r['input_tokens']}→{r['output_tokens']}"
    )

    # final stats
    final = sorted(OUT.glob("*.md"))
    total_chars = sum(p.stat().st_size for p in final)
    print(f"\nFinal wiki: {len(final)} pages, {total_chars:,} chars")
    print_cost()


if __name__ == "__main__":
    main()
