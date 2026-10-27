
from pathlib import Path
import pandas as pd

ROOT = Path(r"D:\Translation Quality Estimation")
INPUT = (
    ROOT / "results" / "week10" / "error_analysis"
    / "selected_cases_rater_annotations.csv"
)
OUT = (
    ROOT / "results" / "week10" / "error_analysis"
    / "manual_cases_summary.csv"
)

df = pd.read_csv(INPUT)

KEYS = [
    "review_group", "system", "doc", "doc_id", "seg_id",
    "y_primary", "source_pred", "target_pred",
    "score_LogisticRegression", "rank_LogisticRegression",
    "score_HeuristicRules", "rank_HeuristicRules",
]

def join_unique(series):
    vals = sorted({
        str(x).strip()
        for x in series.dropna()
        if str(x).strip()
    })
    return " | ".join(vals)

summary = (
    df.groupby(KEYS, dropna=False)
    .agg(
        raters=("rater", "nunique"),
        annotation_rows=("rater", "size"),
        categories=("category", join_unique),
        severities=("severity", join_unique),
        serious_major_raters=(
            "rater",
            lambda s: df.loc[
                s.index,
                "rater"
            ][
                df.loc[s.index, "severity"].eq("Major")
                & (
                    df.loc[s.index, "category"].fillna("").str.startswith("Accuracy/")
                    | df.loc[s.index, "category"].eq("Non-translation!")
                )
            ].nunique()
        ),
    )
    .reset_index()
)

summary.to_csv(OUT, index=False)

print("Unique translation cases:", len(summary))
print("\nCases by group:")
print(summary["review_group"].value_counts().to_string())
print("\nSummary:")
print(summary.to_string(index=False))
print("\nSaved to:", OUT)
