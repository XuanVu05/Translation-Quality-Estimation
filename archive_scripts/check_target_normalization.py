from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")
df = df[~df["system"].isin(
    {"Human-A.0", "Human-B.0", "Human-P.0"}
)].copy()

keys = ["system", "doc", "doc_id", "seg_id"]

def strip_v_tags(value):
    if pd.isna(value):
        return ""
    return re.sub(r"</?v>", "", str(value))

df["target_without_v"] = df["target"].map(strip_v_tags)

summary = (
    df.groupby(keys, dropna=False)
    .agg(
        source_values=("source", "nunique"),
        raw_target_values=("target", "nunique"),
        normalized_target_values=("target_without_v", "nunique"),
        annotation_rows=("rater", "size"),
        distinct_raters=("rater", "nunique"),
    )
    .reset_index()
)

print("Total MT segment keys:", len(summary))
print("Segments with multiple raw targets:",
      int((summary["raw_target_values"] > 1).sum()))
print("Segments with multiple targets after removing <v> tags:",
      int((summary["normalized_target_values"] > 1).sum()))
print("Segments with multiple source values:",
      int((summary["source_values"] > 1).sum()))
print("Segments with one normalized target:",
      int((summary["normalized_target_values"] == 1).sum()))

print("\nDistribution of normalized target variants:")
print(
    summary["normalized_target_values"]
    .value_counts()
    .sort_index()
    .to_string()
)

out = ROOT / "results" / "week10" / "data_quality"
out.mkdir(parents=True, exist_ok=True)
summary.to_csv(
    out / "target_normalization_check.csv",
    index=False,
    encoding="utf-8-sig",
)
print("\nSaved:", out / "target_normalization_check.csv")
