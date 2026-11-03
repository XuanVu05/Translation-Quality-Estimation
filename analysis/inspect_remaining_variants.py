from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "analysis" / "data_quality_results"
OUT.mkdir(parents=True, exist_ok=True)

mqm = pd.read_csv(MQM_PATH, sep="\t")

keys = ["system", "doc", "doc_id", "seg_id"]

def normalize_target(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"</?v>", "", text)
    return re.sub(r"\s+", " ", text).strip()

mqm["target_normalized"] = mqm["target"].apply(normalize_target)

# 1. Find system-segments with multiple normalized targets.
variant_counts = (
    mqm.groupby(keys)["target_normalized"]
    .nunique()
    .reset_index(name="normalized_variants")
)

content_variants = variant_counts[
    variant_counts["normalized_variants"] > 1
]

# 2. Extract all annotation rows for these cases.
details = mqm.merge(
    content_variants[keys],
    on=keys,
    how="inner"
)

details = details.sort_values(keys + ["rater"])

details.to_csv(
    OUT / "remaining_content_variants_all.csv",
    index=False
)

# 3. Save a manageable sample of 30 system-segments.
sample_keys = content_variants.head(30)[keys]

sample = details.merge(
    sample_keys,
    on=keys,
    how="inner"
)

sample[
    keys + [
        "rater",
        "target",
        "target_normalized",
        "category",
        "severity"
    ]
].to_csv(
    OUT / "remaining_content_variants_sample.csv",
    index=False
)

# 4. Check markup patterns still present after removing <v>.
tag_pattern = re.compile(r"<[^>]+>")

remaining_tags = details[
    details["target_normalized"].str.contains(
        tag_pattern, na=False
    )
]

# 5. Identify the segment with only two raters.
rater_counts = (
    mqm.groupby(keys)["rater"]
    .nunique()
    .reset_index(name="n_raters")
)

two_rater_segments = rater_counts[
    rater_counts["n_raters"] == 2
]

two_rater_details = mqm.merge(
    two_rater_segments[keys],
    on=keys,
    how="inner"
)

two_rater_details.to_csv(
    OUT / "two_rater_segment_details.csv",
    index=False
)

print("=" * 60)
print("REMAINING TARGET VARIANT INSPECTION")
print("=" * 60)

print("System-segments with multiple normalized targets:",
      len(content_variants))

print("Annotation rows in these cases:", len(details))

print("Cases with remaining HTML/XML-like tags:",
      remaining_tags[keys].drop_duplicates().shape[0])

print("\nRemaining tag examples:")
if len(remaining_tags):
    print(
        remaining_tags[
            keys + ["target_normalized"]
        ].drop_duplicates().head(10).to_string(index=False)
    )
else:
    print("No remaining tags detected.")

print("\nSEGMENTS WITH ONLY TWO RATERS")
print("Number of segments:", len(two_rater_segments))

if len(two_rater_details):
    print(
        two_rater_details[
            keys + ["rater", "category", "severity", "target"]
        ].to_string(index=False)
    )

print("\nResults saved to:")
print(OUT)