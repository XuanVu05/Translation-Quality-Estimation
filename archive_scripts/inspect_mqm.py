
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "results" / "week10" / "data_quality"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH, sep="\t", encoding="utf-8")

print("Dataset shape:", df.shape)
print("\nFirst 10 rows:")
print(df[["system", "doc", "doc_id", "seg_id", "rater"]].head(10).to_string(index=False))

# Inspect document identifiers
print("\nExamples: doc -> doc_id")
doc_map = (
    df[["doc", "doc_id"]]
    .drop_duplicates()
    .sort_values(["doc", "doc_id"])
)
print(doc_map.head(30).to_string(index=False))

print("\nExamples: doc_id -> doc")
id_map = (
    df[["doc_id", "doc"]]
    .drop_duplicates()
    .sort_values(["doc_id", "doc"])
)
print(id_map.head(30).to_string(index=False))

# Save full mappings for inspection
doc_map.to_csv(OUT_DIR / "doc_to_doc_id_mapping.csv", index=False)
id_map.to_csv(OUT_DIR / "doc_id_to_doc_mapping.csv", index=False)

# Identify segments with fewer than 3 distinct raters
segment_keys = ["system", "doc", "doc_id", "seg_id"]
rater_counts = (
    df.groupby(segment_keys, dropna=False)["rater"]
    .nunique()
    .reset_index(name="unique_raters")
)
incomplete = rater_counts[rater_counts["unique_raters"] < 3]
print("\nSegments with fewer than 3 distinct raters:")
print(incomplete.to_string(index=False))

if not incomplete.empty:
    details = df.merge(incomplete[segment_keys], on=segment_keys, how="inner")
    details.to_csv(OUT_DIR / "incomplete_rater_segments.csv", index=False)

print("\nSaved outputs to:", OUT_DIR)


# Inspect the only segment with fewer than 3 distinct raters
mask = (
    (df["system"] == "Online-A.1574")
    & (df["doc"] == "sky.com.20669")
    & (df["doc_id"] == 7)
    & (df["seg_id"] == 1161)
)

cols = [
    "system", "doc", "doc_id", "seg_id", "rater",
    "source", "target", "category", "severity"
]

print("\n=== Incomplete-rater segment details ===")
print(df.loc[mask, cols].to_string(index=False))

print("\nNumber of annotation rows:", int(mask.sum()))
print("Distinct raters:", df.loc[mask, "rater"].nunique())


# Check document-level split keys
doc_summary = (
    df.groupby("doc", dropna=False)
    .agg(
        n_doc_ids=("doc_id", "nunique"),
        n_segments=("seg_id", "nunique"),
        n_systems=("system", "nunique"),
        n_raters=("rater", "nunique"),
    )
    .reset_index()
)

print("\n=== Document-level summary ===")
print("Unique documents:", df["doc"].nunique())
print("Unique doc_id values:", df["doc_id"].nunique())
print("Documents with multiple doc_id values:",
      int((doc_summary["n_doc_ids"] > 1).sum()))
print("Documents with missing names:",
      int(df["doc"].isna().sum()))

print("\nExample document summaries:")
print(doc_summary.head(10).to_string(index=False))

doc_summary.to_csv(
    OUT_DIR / "document_level_summary.csv",
    index=False
)
