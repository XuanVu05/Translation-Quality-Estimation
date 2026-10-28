
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PRED_PATH = (
    ROOT / "results" / "week10" / "test_evaluation"
    / "test_predictions.csv"
)
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "results" / "week10" / "error_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEYS = ["system", "doc", "doc_id", "seg_id"]

pred = pd.read_csv(PRED_PATH)
mqm = pd.read_csv(MQM_PATH, sep="\t")

# Remove human-reference systems; keep the seven MT systems.
human_systems = {"Human-A.0", "Human-B.0", "Human-P.0"}
mqm = mqm[~mqm["system"].isin(human_systems)].copy()

# Normalize columns used in the join.
for col in ["system", "doc"]:
    pred[col] = pred[col].astype(str).str.strip()
    mqm[col] = mqm[col].astype(str).str.strip()

for col in ["doc_id", "seg_id"]:
    pred[col] = pred[col].astype(str).str.strip()
    mqm[col] = mqm[col].astype(str).str.strip()

# Identify serious annotation rows using the project's fixed rule.
category = mqm["category"].fillna("").astype(str)
severity = mqm["severity"].fillna("").astype(str).str.strip()

mqm["is_serious_row"] = (
    severity.eq("Major")
    & (
        category.str.startswith("Accuracy/")
        | category.eq("Non-translation!")
    )
)

# Count unique raters who marked at least one serious error
# for each translation segment.
serious_by_rater = (
    mqm[mqm["is_serious_row"]]
    .groupby(KEYS)["rater"]
    .nunique()
    .rename("serious_votes_recomputed")
    .reset_index()
)

# Aggregate annotation details for manual review.
def unique_join(series):
    values = sorted({
        str(x).strip()
        for x in series.dropna()
        if str(x).strip()
    })
    return " | ".join(values)

annotation_summary = (
    mqm.groupby(KEYS, dropna=False)
    .agg(
        mqm_categories=("category", unique_join),
        mqm_severities=("severity", unique_join),
        n_annotation_rows=("rater", "size"),
        n_distinct_raters=("rater", "nunique"),
    )
    .reset_index()
)

annotation_summary = annotation_summary.merge(
    serious_by_rater,
    on=KEYS,
    how="left",
)
annotation_summary["serious_votes_recomputed"] = (
    annotation_summary["serious_votes_recomputed"]
    .fillna(0)
    .astype(int)
)

# Left join preserves all test prediction rows.
merged = pred.merge(
    annotation_summary,
    on=KEYS,
    how="left",
    validate="one_to_one",
    indicator=True,
)

merged["mqm_match"] = merged["_merge"].eq("both")
merged.drop(columns=["_merge"], inplace=True)

# Reconstruct the primary label from the original annotations.
merged["y_recomputed"] = (
    merged["serious_votes_recomputed"] >= 2
).astype(int)

merged["label_match"] = (
    merged["y_primary"].astype(int) == merged["y_recomputed"]
)

# Save the full joined table.
full_path = OUT_DIR / "test_predictions_with_mqm.csv"
merged.to_csv(full_path, index=False)

# Select useful cases for manual review.
n_top = max(1, int((0.20 * len(merged)) + 0.999999))
lr_top = merged["rank_LogisticRegression"] <= n_top \
    if "rank_LogisticRegression" in merged.columns else None

if lr_top is None:
    merged["rank_LogisticRegression"] = (
        merged["score_LogisticRegression"]
        .rank(method="first", ascending=False)
        .astype(int)
    )
    lr_top = merged["rank_LogisticRegression"] <= n_top

merged["lr_top20"] = lr_top

if "rank_HeuristicRules" not in merged.columns:
    merged["rank_HeuristicRules"] = (
        merged["score_HeuristicRules"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

merged["heuristic_top20"] = merged["rank_HeuristicRules"] <= n_top

merged["review_group"] = "Other"
merged.loc[
    (merged["y_primary"] == 1)
    & (~merged["lr_top20"])
    & (~merged["heuristic_top20"]),
    "review_group",
] = "Critical_missed_by_both"

merged.loc[
    (merged["y_primary"] == 1)
    & merged["lr_top20"]
    & (~merged["heuristic_top20"]),
    "review_group",
] = "Critical_only_LogReg"

merged.loc[
    (merged["y_primary"] == 1)
    & (~merged["lr_top20"])
    & merged["heuristic_top20"],
    "review_group",
] = "Critical_only_heuristic"

merged.loc[
    (merged["y_primary"] == 0)
    & merged["lr_top20"],
    "review_group",
] = "Noncritical_top20_LogReg"

review_columns = [
    "review_group", "system", "doc", "doc_id", "seg_id",
    "source", "target", "y_primary", "y_recomputed",
    "serious_votes_recomputed", "mqm_categories", "mqm_severities",
    "score_LogisticRegression", "rank_LogisticRegression",
    "score_HeuristicRules", "rank_HeuristicRules",
    "mqm_match", "label_match",
]

review = merged[review_columns].copy()
review.to_csv(
    OUT_DIR / "manual_review_with_mqm.csv",
    index=False,
)

# Report join and label consistency diagnostics.
print("\n=== MQM JOIN DIAGNOSTICS ===")
print("MQM rows after excluding human systems:", len(mqm))
print("Test prediction rows:", len(pred))
print("Matched test rows:", int(merged["mqm_match"].sum()))
print("Unmatched test rows:", int((~merged["mqm_match"]).sum()))
print("Primary-label mismatches:", int((~merged["label_match"]).sum()))

print("\n=== MANUAL REVIEW GROUPS ===")
print(merged["review_group"].value_counts().to_string())

print("\nSaved files:")
print(full_path)
print(OUT_DIR / "manual_review_with_mqm.csv")
