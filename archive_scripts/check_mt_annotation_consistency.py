from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

human = {"Human-A.0", "Human-B.0", "Human-P.0"}
df = df[~df["system"].isin(human)].copy()

df["target_clean"] = (
    df["target"].fillna("").astype(str)
    .map(lambda x: re.sub(r"</?v>", "", x))
)

segment_keys = ["system", "doc", "doc_id", "seg_id"]
rater_keys = segment_keys + ["rater"]

segment_stats = (
    df.groupby(segment_keys, dropna=False)
    .agg(
        annotation_rows=("rater", "size"),
        distinct_raters=("rater", "nunique"),
        target_variants=("target_clean", "nunique")
    )
    .reset_index()
)

rater_stats = (
    df.groupby(rater_keys, dropna=False)
    .agg(
        annotation_rows=("target_clean", "size"),
        target_variants=("target_clean", "nunique"),
        categories=("category", "nunique")
    )
    .reset_index()
)

same_rater_multiple_targets = rater_stats[
    rater_stats["target_variants"] > 1
].copy()

same_rater_multiple_annotations = rater_stats[
    rater_stats["annotation_rows"] > 1
].copy()

summary = pd.DataFrame([
    {
        "metric": "MT segments",
        "value": len(segment_stats)
    },
    {
        "metric": "Segments with multiple target variants",
        "value": int((segment_stats["target_variants"] > 1).sum())
    },
    {
        "metric": "Segment-rater groups with multiple targets",
        "value": len(same_rater_multiple_targets)
    },
    {
        "metric": "Segment-rater groups with multiple annotation rows",
        "value": len(same_rater_multiple_annotations)
    }
])

summary.to_csv(
    OUT / "mt_annotation_consistency_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

same_rater_multiple_targets.to_csv(
    OUT / "mt_same_rater_multiple_targets.csv",
    index=False,
    encoding="utf-8-sig"
)

same_rater_multiple_annotations.to_csv(
    OUT / "mt_same_rater_multiple_annotations.csv",
    index=False,
    encoding="utf-8-sig"
)

print(summary.to_string(index=False))
print("\nSaved to:", OUT)
