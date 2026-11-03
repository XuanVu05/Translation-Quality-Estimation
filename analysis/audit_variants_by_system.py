
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "analysis" / "data_quality_results"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(MQM_PATH, sep="\t")

def normalize_target(text):
    if pd.isna(text):
        return ""
    text = re.sub(r"</?v>", "", str(text))
    return re.sub(r"\s+", " ", text).strip()

df["target_normalized"] = df["target"].apply(normalize_target)
df["system_type"] = df["system"].apply(
    lambda x: "Human" if str(x).startswith("Human-") else "MT"
)

segment_key = ["system", "doc", "doc_id", "seg_id"]

# Count normalized variants at system-segment level.
segment_stats = (
    df.groupby(segment_key + ["system_type"])
    .agg(
        normalized_variants=("target_normalized", "nunique"),
        raw_variants=("target", "nunique"),
        n_raters=("rater", "nunique"),
        annotation_rows=("target", "size")
    )
    .reset_index()
)

segment_stats["has_content_variation"] = (
    segment_stats["normalized_variants"] > 1
)

# Check whether a single rater has multiple normalized targets
# for the same system-segment.
within_rater = (
    df.groupby(segment_key + ["rater"])["target_normalized"]
    .nunique()
    .reset_index(name="variants_within_rater")
)

within_rater["within_rater_variation"] = (
    within_rater["variants_within_rater"] > 1
)

within_segment = (
    within_rater.groupby(segment_key)
    .agg(
        raters_with_multiple_targets=(
            "within_rater_variation", "sum"
        )
    )
    .reset_index()
)

segment_stats = segment_stats.merge(
    within_segment,
    on=segment_key,
    how="left"
)

# Summary by system.
by_system = (
    segment_stats.groupby(["system_type", "system"])
    .agg(
        total_segments=("seg_id", "size"),
        segments_with_content_variation=(
            "has_content_variation", "sum"
        ),
        mean_normalized_variants=(
            "normalized_variants", "mean"
        ),
        segments_with_within_rater_variation=(
            "raters_with_multiple_targets",
            lambda x: (x > 0).sum()
        )
    )
    .reset_index()
)

by_system["content_variation_rate"] = (
    by_system["segments_with_content_variation"]
    / by_system["total_segments"]
)

# Summary by system type.
by_type = (
    segment_stats.groupby("system_type")
    .agg(
        total_segments=("seg_id", "size"),
        segments_with_content_variation=(
            "has_content_variation", "sum"
        ),
        mean_normalized_variants=(
            "normalized_variants", "mean"
        )
    )
    .reset_index()
)

by_type["content_variation_rate"] = (
    by_type["segments_with_content_variation"]
    / by_type["total_segments"]
)

# Save detailed outputs.
segment_stats.to_csv(
    OUT / "target_variants_by_segment.csv", index=False
)
by_system.to_csv(
    OUT / "target_variants_by_system.csv", index=False
)
by_type.to_csv(
    OUT / "target_variants_by_type.csv", index=False
)
within_rater.to_csv(
    OUT / "target_variants_within_rater.csv", index=False
)

print("=" * 60)
print("TARGET VARIANTS BY SYSTEM TYPE")
print("=" * 60)
print(by_type.to_string(index=False))

print("\nTARGET VARIANTS BY SYSTEM")
print(by_system.to_string(index=False))

print("\nWITHIN-RATER VARIATION")
print(
    "System-segments with at least one rater having "
    "multiple normalized targets:",
    int((segment_stats["raters_with_multiple_targets"] > 0).sum())
)

print("\nResults saved to:")
print(OUT)
