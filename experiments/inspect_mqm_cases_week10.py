
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(r"D:\Translation Quality Estimation")
PRED_PATH = (
    ROOT / "results" / "week10" / "error_analysis"
    / "test_predictions_with_mqm.csv"
)
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "results" / "week10" / "error_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

pred = pd.read_csv(PRED_PATH)
mqm = pd.read_csv(MQM_PATH, sep="\t")

KEYS = ["system", "doc", "doc_id", "seg_id"]

# Normalize join keys.
for df in [pred, mqm]:
    for col in ["system", "doc"]:
        df[col] = df[col].astype(str).str.strip()
    for col in ["doc_id", "seg_id"]:
        df[col] = df[col].astype(str).str.strip()

# Reconstruct rankings and top-20% groups.
n_top = max(1, int(np.ceil(0.20 * len(pred))))

for model in ["LogisticRegression", "HeuristicRules"]:
    score_col = f"score_{model}"
    rank_col = f"rank_{model}"
    if rank_col not in pred.columns:
        pred[rank_col] = (
            pred[score_col]
            .rank(method="first", ascending=False)
            .astype(int)
        )

pred["lr_top20"] = pred["rank_LogisticRegression"] <= n_top
pred["heuristic_top20"] = pred["rank_HeuristicRules"] <= n_top
pred["y_primary"] = pred["y_primary"].astype(int)

pred["review_group"] = "Other"

pred.loc[
    (pred["y_primary"] == 1)
    & (~pred["lr_top20"])
    & (~pred["heuristic_top20"]),
    "review_group",
] = "Critical_missed_by_both"

pred.loc[
    (pred["y_primary"] == 1)
    & pred["lr_top20"]
    & (~pred["heuristic_top20"]),
    "review_group",
] = "Critical_only_LogReg"

pred.loc[
    (pred["y_primary"] == 1)
    & (~pred["lr_top20"])
    & pred["heuristic_top20"],
    "review_group",
] = "Critical_only_heuristic"

# Select up to three critical cases from each group.
groups = [
    "Critical_missed_by_both",
    "Critical_only_LogReg",
    "Critical_only_heuristic",
]

chosen = []
for group in groups:
    subset = pred[pred["review_group"] == group].copy()

    if group in ["Critical_missed_by_both", "Critical_only_LogReg"]:
        subset = subset.sort_values(
            "score_LogisticRegression", ascending=False
        )
    else:
        subset = subset.sort_values(
            "score_HeuristicRules", ascending=False
        )

    chosen.append(subset.head(3))

cases = pd.concat(chosen, ignore_index=True)

# Keep the original annotation rows, including each rater's category
# and severity. Exclude human-reference systems.
human_systems = {"Human-A.0", "Human-B.0", "Human-P.0"}
mqm = mqm[~mqm["system"].isin(human_systems)].copy()

details = cases.merge(
    mqm,
    on=KEYS,
    how="left",
    suffixes=("_pred", "_mqm"),
    validate="one_to_many",
)

# Select columns that exist after the merge.
candidate_columns = [
    "review_group", "system", "doc", "doc_id", "seg_id",
    "y_primary", "source_pred", "target_pred",
    "score_LogisticRegression", "rank_LogisticRegression",
    "score_HeuristicRules", "rank_HeuristicRules",
    "rater", "category", "severity", "target_mqm",
]
available_columns = [
    c for c in candidate_columns if c in details.columns
]
details = details[available_columns]

out_path = OUT_DIR / "selected_cases_rater_annotations.csv"
details.to_csv(out_path, index=False)

print("Selected translation cases:", len(cases))
print("Annotation rows:", len(details))
print("\nCases per group:")
print(cases["review_group"].value_counts().to_string())
print("\nSaved to:", out_path)
print("\nPreview:")
print(details.head(15).to_string(index=False))
