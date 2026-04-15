# Compiled Knowledge Bases vs. RAG

Controlled experiment comparing retrieval from LLM-compiled wiki pages vs. raw document chunks for QA. See `PROMPT.md` at repo root for full spec.

| | Retrieval | Corpus |
|---|---|---|
| A | RAG (k=5) | Raw document chunks |
| B | RAG (k=5) | LLM summaries |
| C | RAG (k=5) | LLM wiki (interlinked) |

A vs B isolates compression. B vs C isolates cross-referencing. A vs C is the headline.

## Setup
```bash
cp .env.example .env  # add OPENROUTER_API_KEY
uv sync
```

## Run
```bash
uv run scripts/01_download_papers.py
uv run scripts/02_extract_text.py
uv run scripts/03_generate_questions.py
uv run scripts/04_compile_summaries.py
uv run scripts/05_compile_wiki.py
uv run scripts/06_build_indices.py
uv run scripts/07_run_experiment.py
uv run scripts/08_evaluate.py
uv run scripts/09_analyze.py
```

Scale via env: `N_PAPERS=100 N_FACTUAL=50 N_SYNTHESIS=50 N_CONTRADICTION=20` for full spec. Defaults to 30/25/25/10 for a tractable end-to-end run.

Hard cost stop at $45; responses cached in `cache/`.
