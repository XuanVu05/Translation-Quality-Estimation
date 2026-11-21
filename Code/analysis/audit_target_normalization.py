
from pathlib import Path
import re
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = PROJECT_ROOT / "mqm_newstest2020_ende.tsv"
OUTPUT_DIR = PROJECT_ROOT / "analysis" / "data_quality_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mqm = pd.read_csv(MQM_PATH, sep="\t")

segment_key = ["system", "doc", "doc_id", "seg_id"]

def normalize_target(text):
    if pd.isna(text):
        return ""

    text = str(text)

    # Remove MQM span markup.
    text = re.sub(r"</?v>", "", text)

    # Normalize whitespace without changing words or punctuation.
    text = re.sub(r"\s+", " ", text).strip()

    return text

mqm["target_normalized"] = mqm["target"].apply(normalize_target)

# Count raw and normalized variants for each system-segment.
variants = (
    mqm.groupby(segment_key)
    .agg(
        raw_target_variants=("target", "nunique"),
        normalized_target_variants=("target_normalized", "nunique"),
        annotation_rows=("target", "size")
    )
    .reset_index()
)

# Classify the source of variation.
variants["variant_status"] = variants.apply(
    lambda row:
        "Markup-only variation"
        if row["raw_target_variants"] > 1
        and row["normalized_target_variants"] == 1
        else (
            "Content variation"
            if row["normalized_target_variants"] > 1
            else "No variation"
        ),
    axis=1
)

status_counts = (
    variants["variant_status"]
    .value_counts()
    .rename_axis("variant_status")
    .reset_index(name="number_of_system_segments")
)

# Save detailed results.
variants.to_csv(
    OUTPUT_DIR / "target_normalization_audit.csv",
    index=False
)

status_counts.to_csv(
    OUTPUT_DIR / "target_normalization_summary.csv",
    index=False
)

# Extract examples where raw targets differ but normalized targets match.
markup_only = variants[
    variants["variant_status"] == "Markup-only variation"
].head(20)

example_keys = markup_only[segment_key]

examples = mqm.merge(
    example_keys,
    on=segment_key,
    how="inner"
)

examples = examples[
    segment_key + [
        "rater",
        "target",
        "target_normalized",
        "category",
        "severity"
    ]
]

examples.to_csv(
    OUTPUT_DIR / "target_markup_examples.csv",
    index=False
)

summary = {
    "n_system_segments": int(len(variants)),
    "raw_variant_distribution": {
        str(k): int(v)
        for k, v in variants["raw_target_variants"].value_counts().sort_index().items()
    },
    "normalized_variant_distribution": {
        str(k): int(v)
        for k, v in variants["normalized_target_variants"].value_counts().sort_index().items()
    },
    "variant_status_counts": {
        str(k): int(v)
        for k, v in variants["variant_status"].value_counts().items()
    }
}

with open(
    OUTPUT_DIR / "target_normalization_summary.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(summary, f, indent=4, ensure_ascii=False)

print("=" * 60)
print("TARGET NORMALIZATION AUDIT")
print("=" * 60)

print("Total system-segments:", len(variants))

print("\nVARIATION STATUS")
print(status_counts.to_string(index=False))

print("\nRAW TARGET VARIANT DISTRIBUTION")
print(
    variants["raw_target_variants"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nNORMALIZED TARGET VARIANT DISTRIBUTION")
print(
    variants["normalized_target_variants"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nResults saved to:")
print(OUTPUT_DIR)
