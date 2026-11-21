
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUTPUT_DIR = ROOT / "analysis" / "data_quality_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mqm = pd.read_csv(MQM_PATH, sep="\t")

# --------------------------------------------------
# 1. Identify MT and human systems
# --------------------------------------------------

systems = sorted(mqm["system"].unique())

system_type = pd.DataFrame({
    "system": systems,
    "type": [
        "Human" if s.startswith("Human-") else "MT"
        for s in systems
    ],
})

print("SYSTEMS")
print(system_type.to_string(index=False))

system_type.to_csv(
    OUTPUT_DIR / "system_type.csv",
    index=False
)

# --------------------------------------------------
# 2. Annotation rows per system-segment-rater
# --------------------------------------------------

annotation_key = [
    "system", "doc", "doc_id", "seg_id", "rater"
]

group_sizes = (
    mqm.groupby(annotation_key, dropna=False)
    .size()
    .reset_index(name="annotation_rows")
)

group_distribution = (
    group_sizes["annotation_rows"]
    .value_counts()
    .sort_index()
    .rename_axis("rows_per_rater_segment")
    .reset_index(name="number_of_groups")
)

group_distribution.to_csv(
    OUTPUT_DIR / "annotation_group_size_distribution.csv",
    index=False
)

repeated_groups = group_sizes[
    group_sizes["annotation_rows"] > 1
].copy()

repeated_groups.to_csv(
    OUTPUT_DIR / "repeated_annotation_groups.csv",
    index=False
)

# --------------------------------------------------
# 3. Rater coverage per system-segment
# --------------------------------------------------

segment_key = ["system", "doc", "doc_id", "seg_id"]

raters_per_segment = (
    mqm.groupby(segment_key)
    .agg(
        n_raters=("rater", "nunique"),
        annotation_rows=("rater", "size"),
    )
    .reset_index()
)

rater_coverage = (
    raters_per_segment
    .groupby(["system", "n_raters"])
    .size()
    .reset_index(name="number_of_segments")
)

rater_coverage.to_csv(
    OUTPUT_DIR / "rater_coverage_by_system.csv",
    index=False
)

# --------------------------------------------------
# 4. Source consistency
# --------------------------------------------------

source_key = ["doc", "doc_id", "seg_id"]

source_consistency = (
    mqm.groupby(source_key)
    .agg(
        n_source_variants=("source", "nunique"),
        n_systems=("system", "nunique"),
    )
    .reset_index()
)

source_issues = source_consistency[
    source_consistency["n_source_variants"] > 1
]

source_issues.to_csv(
    OUTPUT_DIR / "source_inconsistency.csv",
    index=False
)

# --------------------------------------------------
# 5. Target variants per system-segment
# --------------------------------------------------

target_variants = (
    mqm.groupby(segment_key)
    .agg(
        n_target_variants=("target", "nunique"),
        n_raters=("rater", "nunique"),
        n_annotation_rows=("target", "size"),
    )
    .reset_index()
)

target_distribution = (
    target_variants["n_target_variants"]
    .value_counts()
    .sort_index()
    .rename_axis("target_variants")
    .reset_index(name="number_of_system_segments")
)

target_variants.to_csv(
    OUTPUT_DIR / "target_variants_by_segment.csv",
    index=False
)

target_distribution.to_csv(
    OUTPUT_DIR / "target_variant_distribution.csv",
    index=False
)

# --------------------------------------------------
# 6. Repeated keys: inspect whether annotations differ
# --------------------------------------------------

repeated_rows = mqm.merge(
    repeated_groups[annotation_key],
    on=annotation_key,
    how="inner",
)

repeated_detail = (
    repeated_rows.groupby(annotation_key)
    .agg(
        annotation_rows=("category", "size"),
        unique_categories=("category", "nunique"),
        unique_severities=("severity", "nunique"),
        unique_targets=("target", "nunique"),
    )
    .reset_index()
)

repeated_detail.to_csv(
    OUTPUT_DIR / "repeated_annotation_details.csv",
    index=False
)

# --------------------------------------------------
# 7. Summary
# --------------------------------------------------

summary = {
    "n_systems": int(len(systems)),
    "n_mt_systems": int(
        (system_type["type"] == "MT").sum()
    ),
    "n_human_systems": int(
        (system_type["type"] == "Human").sum()
    ),
    "n_annotation_groups": int(len(group_sizes)),
    "n_repeated_annotation_groups": int(len(repeated_groups)),
    "max_annotations_per_rater_segment": int(
        group_sizes["annotation_rows"].max()
    ),
    "rater_counts_per_segment": {
        str(k): int(v)
        for k, v in raters_per_segment[
            "n_raters"
        ].value_counts().sort_index().items()
    },
    "source_inconsistent_segments": int(len(source_issues)),
    "target_variant_distribution": {
        str(k): int(v)
        for k, v in target_variants[
            "n_target_variants"
        ].value_counts().sort_index().items()
    },
    "repeated_groups_with_multiple_categories": int(
        (
            repeated_detail["unique_categories"] > 1
        ).sum()
    ),
    "repeated_groups_with_multiple_severities": int(
        (
            repeated_detail["unique_severities"] > 1
        ).sum()
    ),
}

with open(
    OUTPUT_DIR / "annotation_structure_summary.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(summary, f, indent=4, ensure_ascii=False)

print("\n" + "=" * 60)
print("ANNOTATION STRUCTURE AUDIT")
print("=" * 60)

for key, value in summary.items():
    print(f"{key}: {value}")

print("\nANNOTATION GROUP SIZE DISTRIBUTION")
print(group_distribution.to_string(index=False))

print("\nRATER COVERAGE BY SYSTEM")
print(rater_coverage.to_string(index=False))

print("\nTARGET VARIANT DISTRIBUTION")
print(target_distribution.to_string(index=False))

print("\nResults saved to:")
print(OUTPUT_DIR)
