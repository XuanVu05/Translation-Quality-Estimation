
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\Translation Quality Estimation")
INPUT = (
    ROOT / "results" / "week10" / "test_evaluation"
    / "test_predictions.csv"
)
OUT_DIR = ROOT / "results" / "week10" / "error_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# Verify required columns before processing.
required = [
    "system", "doc", "doc_id", "seg_id",
    "source", "target", "y_primary",
    "score_HeuristicRules", "score_LogisticRegression",
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["y_primary"] = df["y_primary"].astype(int)

# Rank within the whole test set, separately for each method.
# Rank 1 means highest priority.
for model in ["HeuristicRules", "LogisticRegression"]:
    score_col = f"score_{model}"
    df[f"rank_{model}"] = (
        df[score_col].rank(method="first", ascending=False).astype(int)
    )

n_top = max(1, int(np.ceil(0.20 * len(df))))
df["top20_HeuristicRules"] = df["rank_HeuristicRules"] <= n_top
df["top20_LogisticRegression"] = (
    df["rank_LogisticRegression"] <= n_top
)

def classify(row):
    critical = row["y_primary"] == 1
    lr_top = row["top20_LogisticRegression"]
    h_top = row["top20_HeuristicRules"]

    if critical and not lr_top:
        if not h_top:
            return "FN_both_miss"
        return "FN_LogReg_heuristic_finds"
    if critical and lr_top and not h_top:
        return "Critical_found_only_by_LogReg"
    if not critical and lr_top:
        return "FP_LogReg_top20"
    if not critical and h_top:
        return "FP_Heuristic_top20"
    return "Other"

df["analysis_group"] = df.apply(classify, axis=1)

# Export a full review table, including all samples.
columns = [
    "analysis_group", "system", "doc", "doc_id", "seg_id",
    "y_primary", "source", "target",
    "score_LogisticRegression", "rank_LogisticRegression",
    "score_HeuristicRules", "rank_HeuristicRules",
    "top20_LogisticRegression", "top20_HeuristicRules",
]
review = df[columns].sort_values(
    ["analysis_group", "rank_LogisticRegression"]
)
review.to_csv(OUT_DIR / "all_test_error_analysis_candidates.csv", index=False)

# Summarize the groups to help select cases.
summary = (
    df.groupby("analysis_group", dropna=False)
    .agg(
        n=("y_primary", "size"),
        critical_count=("y_primary", "sum"),
    )
    .reset_index()
)
summary.to_csv(OUT_DIR / "error_analysis_group_summary.csv", index=False)

# Create a compact sample of up to 15 cases for manual review.
# Prioritize missed critical cases, then critical cases found by only one method.
priority_groups = [
    "FN_both_miss",
    "FN_LogReg_heuristic_finds",
    "Critical_found_only_by_LogReg",
    "FP_LogReg_top20",
    "FP_Heuristic_top20",
]
parts = []
for group in priority_groups:
    subset = review[review["analysis_group"] == group].head(3)
    if not subset.empty:
        parts.append(subset)

sample = pd.concat(parts, ignore_index=True) if parts else review.head(0)
sample.to_csv(OUT_DIR / "manual_review_sample.csv", index=False)

print("\n=== GROUP SUMMARY ===")
print(summary.to_string(index=False))
print(f"\nTest rows: {len(df)}")
print(f"Top-20% budget: {n_top}")
print(f"Manual review sample: {len(sample)} rows")
print(f"\nSaved files to: {OUT_DIR}")
print("- error_analysis_group_summary.csv")
print("- manual_review_sample.csv")
print("- all_test_error_analysis_candidates.csv")
