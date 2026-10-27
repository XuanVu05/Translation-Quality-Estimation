
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

keys = ["system", "doc", "doc_id", "seg_id"]

summary = (
    df.groupby(keys, dropna=False)
    .agg(
        rows=("rater", "size"),
        raters=("rater", "nunique"),
        sources=("source", "nunique"),
        targets=("target", "nunique"),
    )
    .reset_index()
)

summary["wrong_rater_count"] = summary["raters"] != 3
summary["multiple_sources"] = summary["sources"] > 1
summary["multiple_targets"] = summary["targets"] > 1

summary.to_csv(
    OUT / "segment_anomaly_diagnostics.csv",
    index=False,
    encoding="utf-8-sig",
)

conditions = pd.DataFrame([
    {
        "condition": "raters_not_equal_3",
        "segments": int(summary["wrong_rater_count"].sum()),
    },
    {
        "condition": "multiple_source_values",
        "segments": int(summary["multiple_sources"].sum()),
    },
    {
        "condition": "multiple_target_values",
        "segments": int(summary["multiple_targets"].sum()),
    },
    {
        "condition": "multiple_sources_and_targets",
        "segments": int(
            (summary["multiple_sources"] & summary["multiple_targets"]).sum()
        ),
    },
    {
        "condition": "rater_count_and_target_differ",
        "segments": int(
            (summary["wrong_rater_count"] & summary["multiple_targets"]).sum()
        ),
    },
])

conditions.to_csv(
    OUT / "anomaly_condition_counts.csv",
    index=False,
    encoding="utf-8-sig",
)

# Save a few examples for manual inspection
examples = summary[summary["multiple_targets"]].head(10)
sample_keys = examples[keys]

sample_rows = df.merge(sample_keys, on=keys, how="inner")
sample_rows.to_csv(
    OUT / "multiple_target_examples.tsv",
    sep="\t",
    index=False,
    encoding="utf-8-sig",
)

print("Anomaly diagnosis completed.")
print(conditions.to_string(index=False))
print(f"Outputs saved to: {OUT}")
