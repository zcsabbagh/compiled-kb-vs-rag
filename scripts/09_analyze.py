"""Analysis: tables, paired tests, cost-accuracy plots."""
import json
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from common import ROOT, cost_of

RAW = ROOT / "results" / "raw_results.jsonl"
JUDGED = ROOT / "results" / "judged_results.jsonl"
ANALYSIS = ROOT / "analysis"
ANALYSIS.mkdir(parents=True, exist_ok=True)

CONDITIONS = ["A_raw", "B_summaries", "C_wiki"]
MODELS = ["meta-llama/llama-3.1-8b-instruct", "anthropic/claude-sonnet-4"]
MODEL_SHORT = {MODELS[0]: "llama-8b", MODELS[1]: "sonnet-4"}


def load_df() -> pd.DataFrame:
    raw = [json.loads(l) for l in open(RAW)]
    judged = [json.loads(l) for l in open(JUDGED)]
    r_df = pd.DataFrame(raw)[
        ["question_id", "tier", "condition", "model", "input_tokens", "output_tokens"]
    ]
    j_df = pd.DataFrame(judged)
    # merge on (q,c,m); keep judge fields
    df = r_df.merge(
        j_df[
            [
                "question_id",
                "condition",
                "model",
                "correctness_score",
                "faithful",
                "coverage",
                "contradiction_detected",
            ]
        ],
        on=["question_id", "condition", "model"],
        how="left",
    )
    df["cost_usd"] = df.apply(
        lambda r: cost_of(r["model"], r["input_tokens"], r["output_tokens"]), axis=1
    )
    df["model_short"] = df["model"].map(MODEL_SHORT)
    return df


def main_table(df):
    """Mean correctness +/- SE per (condition x model) and per tier."""
    rows = []
    for tier in ["all", "factual", "synthesis", "contradiction"]:
        sub = df if tier == "all" else df[df["tier"] == tier]
        for cond in CONDITIONS:
            for m in MODELS:
                s = sub[(sub["condition"] == cond) & (sub["model"] == m)][
                    "correctness_score"
                ].dropna()
                if len(s) == 0:
                    mean, se, n = float("nan"), float("nan"), 0
                else:
                    mean = s.mean()
                    se = s.std(ddof=1) / np.sqrt(len(s)) if len(s) > 1 else 0.0
                    n = len(s)
                rows.append(
                    {
                        "tier": tier,
                        "condition": cond,
                        "model": MODEL_SHORT[m],
                        "n": n,
                        "mean_correctness": round(mean, 3),
                        "se": round(se, 3),
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(ANALYSIS / "main_table.csv", index=False)
    print("\n=== Main table (correctness) ===")
    print(out.to_string(index=False))
    return out


def paired_tests(df):
    """For each (model, pair of conditions), paired Wilcoxon on correctness."""
    pairs = [("A_raw", "B_summaries"), ("B_summaries", "C_wiki"), ("A_raw", "C_wiki")]
    rows = []
    for m in MODELS:
        sub = df[df["model"] == m]
        wide = sub.pivot_table(
            index="question_id", columns="condition", values="correctness_score"
        )
        for a, b in pairs:
            if a not in wide.columns or b not in wide.columns:
                continue
            paired = wide[[a, b]].dropna()
            if len(paired) < 5:
                continue
            try:
                stat, p = stats.wilcoxon(paired[a], paired[b], zero_method="wilcox")
            except Exception:
                stat, p = float("nan"), float("nan")
            # Cohen's d on differences
            diff = paired[b] - paired[a]
            d = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0.0
            rows.append(
                {
                    "model": MODEL_SHORT[m],
                    "comparison": f"{a} vs {b}",
                    "n_paired": len(paired),
                    "mean_a": round(paired[a].mean(), 3),
                    "mean_b": round(paired[b].mean(), 3),
                    "delta": round(paired[b].mean() - paired[a].mean(), 3),
                    "wilcoxon_stat": round(stat, 3),
                    "p_value": round(p, 4),
                    "cohens_d": round(d, 3),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(ANALYSIS / "paired_tests.csv", index=False)
    print("\n=== Paired tests ===")
    print(out.to_string(index=False))
    return out


def model_interaction(df):
    """Is A->C improvement larger for 8B than Sonnet? Effect sizes."""
    rows = []
    for m in MODELS:
        sub = df[df["model"] == m]
        wide = sub.pivot_table(
            index="question_id", columns="condition", values="correctness_score"
        )
        if "A_raw" not in wide.columns or "C_wiki" not in wide.columns:
            continue
        paired = wide[["A_raw", "C_wiki"]].dropna()
        diff = paired["C_wiki"] - paired["A_raw"]
        d = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) > 0 else 0.0
        rows.append(
            {
                "model": MODEL_SHORT[m],
                "n": len(paired),
                "mean_A": round(paired["A_raw"].mean(), 3),
                "mean_C": round(paired["C_wiki"].mean(), 3),
                "delta_C-A": round(diff.mean(), 3),
                "cohens_d": round(d, 3),
            }
        )
    out = pd.DataFrame(rows)
    out.to_csv(ANALYSIS / "model_interaction.csv", index=False)
    print("\n=== Model interaction (A vs C) ===")
    print(out.to_string(index=False))
    return out


def faithfulness_table(df):
    rows = []
    for cond in CONDITIONS:
        for m in MODELS:
            s = df[(df["condition"] == cond) & (df["model"] == m)]["faithful"]
            s = s.dropna()
            if len(s) == 0:
                continue
            rows.append(
                {
                    "condition": cond,
                    "model": MODEL_SHORT[m],
                    "n": len(s),
                    "pct_faithful": round(s.mean() * 100, 1),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(ANALYSIS / "faithfulness.csv", index=False)
    print("\n=== Faithfulness ===")
    print(out.to_string(index=False))
    return out


def tier_specific_table(df):
    rows = []
    # coverage on synthesis
    syn = df[df["tier"] == "synthesis"]
    for cond in CONDITIONS:
        for m in MODELS:
            s = syn[(syn["condition"] == cond) & (syn["model"] == m)]["coverage"].dropna()
            if len(s) == 0:
                continue
            rows.append(
                {
                    "metric": "coverage(synthesis)",
                    "condition": cond,
                    "model": MODEL_SHORT[m],
                    "n": len(s),
                    "value": round(s.mean(), 3),
                }
            )
    # contradiction_detected on contradiction tier
    con = df[df["tier"] == "contradiction"]
    for cond in CONDITIONS:
        for m in MODELS:
            s = con[(con["condition"] == cond) & (con["model"] == m)][
                "contradiction_detected"
            ].dropna()
            if len(s) == 0:
                continue
            rows.append(
                {
                    "metric": "contradiction_rate",
                    "condition": cond,
                    "model": MODEL_SHORT[m],
                    "n": len(s),
                    "value": round(s.mean(), 3),
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(ANALYSIS / "tier_specific.csv", index=False)
    print("\n=== Tier-specific metrics ===")
    print(out.to_string(index=False))
    return out


def cost_accuracy_plot(df):
    agg = (
        df.groupby(["condition", "model_short"])
        .agg(mean_correct=("correctness_score", "mean"), mean_cost=("cost_usd", "mean"))
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"A_raw": "o", "B_summaries": "s", "C_wiki": "^"}
    for _, row in agg.iterrows():
        ax.scatter(
            row["mean_cost"] * 1000,  # dollars -> millidollars for readable scale
            row["mean_correct"],
            s=180,
            marker=markers[row["condition"]],
            label=f"{row['condition']}/{row['model_short']}",
        )
    ax.set_xlabel("Mean cost per query (millidollars, $/1000)")
    ax.set_ylabel("Mean correctness score (1-5)")
    ax.set_title("Cost vs accuracy by condition × model")
    ax.legend(fontsize=8, loc="best")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(ANALYSIS / "cost_accuracy.png", dpi=120)
    plt.close()
    agg.to_csv(ANALYSIS / "cost_accuracy.csv", index=False)
    print("\n=== Cost-accuracy (mean per query) ===")
    print(agg.to_string(index=False))


def bar_plot(df):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, m in zip(axes, MODELS):
        sub = df[df["model"] == m]
        tier_order = ["factual", "synthesis", "contradiction"]
        ag = (
            sub.groupby(["tier", "condition"])["correctness_score"]
            .agg(["mean", "sem"])
            .reset_index()
        )
        pivot_m = ag.pivot(index="tier", columns="condition", values="mean").reindex(tier_order)
        pivot_e = ag.pivot(index="tier", columns="condition", values="sem").reindex(tier_order)
        pivot_m = pivot_m[CONDITIONS]
        pivot_e = pivot_e[CONDITIONS]
        pivot_m.plot(kind="bar", yerr=pivot_e, ax=ax, capsize=3, rot=0, width=0.8)
        ax.set_title(MODEL_SHORT[m])
        ax.set_ylabel("Mean correctness (1-5)")
        ax.set_ylim(1, 5)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(title="condition", fontsize=8)
    plt.suptitle("Correctness by tier × condition × model")
    plt.tight_layout()
    plt.savefig(ANALYSIS / "correctness_by_tier.png", dpi=120)
    plt.close()


def main():
    df = load_df()
    print(f"Loaded {len(df)} joined records")
    main_table(df)
    paired_tests(df)
    model_interaction(df)
    faithfulness_table(df)
    tier_specific_table(df)
    cost_accuracy_plot(df)
    bar_plot(df)
    print(f"\nArtifacts written to {ANALYSIS}/")


if __name__ == "__main__":
    main()
