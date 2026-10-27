
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

def remove_markers(text):
    if pd.isna(text):
        return text
    text = re.sub(r"</?v>", "", str(text))
    return text

keys = ["system", "doc", "doc_id", "seg_id"]

# Normalize target by removing only MQM span markers
df["target_normalized"] = df["target"].map(remove_markers)

target_stats = (
    df.groupby(keys, dropna=False)
    .agg(
        target_versions=("target", "nunique"),
        normalized_target_versions=("target_normalized", "nunique"),
        raters=("rater", "nunique"),
        rows=("rater", "size"),
    )
    .reset_index()
)

target_stats["markers_explain_all_variants"] = (
    target_stats["normalized_target_versions"] == 1
)

target_stats.to_csv(
    OUT / "target_variant_normalization.csv",
    index=False,
    encoding="utf-8-sig",
)

# Sample segments whose target variants remain different after normalization
remaining = target_stats[
    target_stats["normalized_target_versions"] > 1
].head(20)

sample_rows = df.merge(remaining[keys], on=keys, how="inner")
sample_rows[
    keys + [
        "rater", "category", "severity",
        "target", "target_normalized"
    ]
].to_csv(
    OUT / "target_variants_remaining_examples.tsv",
    sep="\t",
    index=False,
    encoding="utf-8-sig",
)

summary = pd.DataFrame([
    {
        "metric": "segments",
        "value": len(target_stats),
    },
    {
        "metric": "segments_with_multiple_targets",
        "value": int((target_stats["target_versions"] > 1).sum()),
    },
    {
        "metric": "segments_with_multiple_targets_after_normalization",
        "value": int(
            (target_stats["normalized_target_versions"] > 1).sum()
        ),
    },
    {
        "metric": "segments_where_markers_explain_all_variants",
        "value": int(target_stats["markers_explain_all_variants"].sum()),
    },
])

summary.to_csv(
    OUT / "target_variant_normalization_summary.csv",
    index=False,
    encoding="utf-8-sig",
)

print("Target variant check completed.")
print(summary.to_string(index=False))
print(f"Outputs: {OUT}")
