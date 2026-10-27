from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")
human = {"Human-A.0", "Human-B.0", "Human-P.0"}
df = df[~df["system"].isin(human)].copy()

keys = ["system", "doc", "doc_id", "seg_id"]

# Một rater có nhiều dòng annotation vẫn chỉ là một rater.
rater_segment = df[keys + ["rater"]].drop_duplicates()

rater_summary = (
    rater_segment.groupby("system")
    .agg(
        segment_rater_pairs=("rater", "size"),
        unique_raters=("rater", "nunique")
    )
    .reset_index()
)

segment_raters = (
    rater_segment.groupby(keys)
    .agg(distinct_raters=("rater", "nunique"))
    .reset_index()
)

rater_distribution = (
    segment_raters["distinct_raters"]
    .value_counts()
    .sort_index()
    .rename_axis("distinct_raters")
    .reset_index(name="segment_count")
)

rater_summary.to_csv(
    OUT / "mt_rater_coverage_by_system.csv",
    index=False,
    encoding="utf-8-sig"
)

rater_distribution.to_csv(
    OUT / "mt_segment_rater_distribution.csv",
    index=False,
    encoding="utf-8-sig"
)

print("=== Rater coverage by MT system ===")
print(rater_summary.to_string(index=False))

print("\n=== Distinct raters per segment ===")
print(rater_distribution.to_string(index=False))

print("\nSaved to:", OUT)
