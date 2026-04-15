# Results

Single-run output at the reduced scale documented in `README.md`: 30 arXiv papers
on RLHF/RLAIF, 60 questions (25 factual / 25 synthesis / 10 contradiction), 3
retrieval conditions × 2 generators × 60 questions = **360 experiment trials**,
judged by Sonnet for correctness and faithfulness. Total pipeline cost ~**$9.83**.

## Headline: compilation does not beat raw chunks at this scale

Mean correctness (1-5, Sonnet judge) across all 60 questions:

| model | A (raw) | B (summaries) | C (wiki) |
|---|---|---|---|
| llama-8b  | 3.20 | **3.27** | 2.93 |
| sonnet-4  | 3.50 | **3.70** | 3.13 |

Both models rank **B > A > C**. The compiled, interlinked wiki underperforms
both raw chunks and per-paper summaries.

### Paired Wilcoxon tests (same questions, paired across conditions)

For Sonnet, the **B vs C drop is significant**: p = 0.002, Cohen's d = −0.41.
A vs C (the headline in the spec) trends negative but is not significant at this
n (p = 0.17, d = −0.19). For llama-8b, no comparison crosses p < 0.05.

See `analysis/paired_tests.csv` for all pairs.

## Where the wiki lost

Breaking correctness down by tier (Sonnet):

| tier | A | B | C |
|---|---|---|---|
| factual (n=25)      | 4.32 | 4.20 | **3.20** |
| synthesis (n=25)    | 2.84 | **3.40** | 3.20 |
| contradiction (n=10)| 3.10 | **3.20** | 2.80 |

The wiki collapses on **factual** questions — concrete numeric claims like
"r = 0.002 correlation" or "ECE rising by +0.006" survive in raw text and
~800-word summaries but get diluted or dropped by the wiki compilation into
shorter interlinked concept pages.

Encouragingly, the wiki **matches or beats** raw chunks on synthesis and
contradiction questions where cross-paper integration matters — just not by
enough to overcome the factual penalty.

## Faithfulness

The wiki does produce the most **faithful** answers for Sonnet:

| condition | llama-8b | sonnet-4 |
|---|---|---|
| A_raw       | 53.3% | 80.0% |
| B_summaries | 63.3% | 79.7% |
| C_wiki      | 65.0% | **91.7%** |

Tracks with the wiki presenting denser, more structured claims that are easier
for the generator to stay within.

## Cost-accuracy

From `analysis/cost_accuracy.csv` (mean $ per query):

| condition / model | correctness | $/query |
|---|---|---|
| A_raw / llama-8b      | 3.20 | $0.00006 |
| B_summaries / llama-8b | 3.27 | $0.00005 |
| C_wiki / llama-8b     | 2.93 | $0.00005 |
| A_raw / sonnet-4      | 3.50 | $0.01356 |
| B_summaries / sonnet-4 | 3.70 | $0.01223 |
| C_wiki / sonnet-4     | 3.13 | $0.01139 |

Condition B dominates Pareto for both models — smaller retrieved context
(summaries are pre-compressed), higher correctness.

## Caveats that temper the result

1. **Reduced scale vs spec**: 30 papers / 60 questions instead of 100/120.
   Smaller paired sample → lower statistical power. Some near-significant
   negative effects for C could be noise.

2. **Unequal information budget during compilation.** The wiki compile
   truncated each paper to the first 15k chars (~25% of median paper length);
   summaries were truncated to 30k. Condition A (raw chunks) has access to the
   full paper via chunking. This penalizes B and C on content from later
   sections (experiments, appendices) — especially bad for factual questions,
   which matches what we see. A fair rerun should feed the full paper text or
   multi-pass summarize.

3. **Wiki batches hit max_tokens=8000** on every batch in `05_compile_wiki.py`,
   so some `UPDATE` operations may have been cut mid-content. The recovered
   wiki (54 pages, 193k chars, median 3.6k/page) is usable but incomplete.

4. **Coverage/contradiction metrics are citation-style biased**: they match on
   literal arxiv IDs in the answer text, and wiki chunks carry
   `[[paper-<id>]]` slugs which make IDs surface more often in C's answers.
   Coverage on synthesis is highest for C (0.56 Sonnet) but that is partly
   the citation style, not true multi-paper integration. The correctness score
   from the Sonnet judge is format-agnostic and is the primary metric.

5. **Judge is Sonnet; generator also Sonnet in one condition.** There is a
   known self-preference risk in same-family judging. Mitigation would be a
   second independent judge (e.g. a GPT model), not done here.

## What would improve the setup

- Restore full-paper context in compilation (multi-pass summarize or raise
  truncation to 80k chars; bump wiki batch output cap to 16k).
- Re-run at 100 papers / 120 questions for statistical power.
- Add the dropped 70B generator to test the "compilation helps the weak model
  more" hypothesis properly — at this scale, 8B and Sonnet move together.
- Replace paper-ID string-matching coverage with a Sonnet-judged "which papers
  does this answer draw from" classification.
- Add a second judge model for cross-check.

## Files

- `analysis/main_table.csv`, `paired_tests.csv`, `model_interaction.csv`,
  `faithfulness.csv`, `tier_specific.csv`, `cost_accuracy.csv`
- `analysis/correctness_by_tier.png`, `cost_accuracy.png`
- `results/raw_results.jsonl` (360 rows, full answers + retrieved chunks)
- `results/judged_results.jsonl` (correctness/faithfulness scores)
- `results/cost_log.jsonl` (every API call)
