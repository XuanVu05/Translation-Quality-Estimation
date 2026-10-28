from pathlib import Path
import json
import re
import unicodedata
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(".")
DEV_PATH = ROOT / "results/week10/model_data/dev_segments.csv"
PRED_PATH = ROOT / "results/week10/ablation_dev/dev_ablation_predictions.csv"
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "results/week10/error_analysis_dev"

KEYS = ["system", "doc", "seg_id"]
REQUIRED_DEV = KEYS + ["source", "target", "serious_votes", "y_primary"]
REQUIRED_PRED = KEYS + ["score_LR_Base"]
REQUIRED_MQM = KEYS + ["rater", "target", "category", "severity"]


def normalize_target(value):
    if pd.isna(value):
        return ""
    value = str(value)
    value = re.sub(r"</?v>", "", value, flags=re.IGNORECASE)
    value = unicodedata.normalize("NFKC", value)
    return " ".join(value.split())


for path in [DEV_PATH, PRED_PATH, MQM_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")

dev = pd.read_csv(DEV_PATH)
pred = pd.read_csv(PRED_PATH)
mqm = pd.read_csv(MQM_PATH, sep="\t")

for name, df, required in [
    ("Dev", dev, REQUIRED_DEV),
    ("Predictions", pred, REQUIRED_PRED),
    ("MQM", mqm, REQUIRED_MQM),
]:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")

for name, df in [("Dev", dev), ("Predictions", pred)]:
    if df.duplicated(KEYS).any():
        raise ValueError(f"{name} has duplicate system/doc/seg_id keys")

# Join the saved Dev split to its saved ablation predictions.
dev = dev.merge(
    pred[KEYS + ["score_LR_Base"]],
    on=KEYS,
    how="left",
    validate="one_to_one",
    indicator=True,
)
if not dev["_merge"].eq("both").all():
    raise ValueError("Some Dev rows do not have an LR_Base prediction.")
dev = dev.drop(columns="_merge")

if len(dev) != 1554:
    raise ValueError(f"Expected 1554 Dev rows, found {len(dev)}")

# Stable ordering makes ties deterministic.
dev = dev.sort_values(
    "score_LR_Base", ascending=False, kind="mergesort"
).reset_index(drop=True)
dev["rank_LR_Base"] = range(1, len(dev) + 1)

top_n = int(__import__("math").ceil(0.20 * len(dev)))
top = dev.head(top_n).copy()
selected = top.loc[top["serious_votes"].eq(0)].copy()

if len(top) != 311:
    raise ValueError(f"Expected top 20% to contain 311 rows, found {len(top)}")
if len(selected) != 180:
    raise ValueError(
        f"Expected 180 zero-vote rows in top 20%, found {len(selected)}. "
        "Stop and inspect the split, predictions, and ranking convention."
    )

# Prepare MQM annotations and normalized target strings.
mqm = mqm.copy()
mqm["target_normalized"] = mqm["target"].map(normalize_target)
selected["target_normalized"] = selected["target"].map(normalize_target)

# Keep annotations for the selected segment keys, then check target matching.
annotations = selected[
    KEYS + ["target_normalized"]
].merge(
    mqm,
    on=KEYS,
    how="left",
    suffixes=("_dev", "_mqm"),
    validate="one_to_many",
)

annotations["target_match"] = (
    annotations["target_normalized_dev"]
    == annotations["target_normalized_mqm"]
)
annotations["target_match"] = annotations["target_match"].fillna(False)

matched = annotations.loc[annotations["target_match"]].copy()

# Per-segment summary: annotation counts are separate from segment counts.
summary_rows = []
for _, row in selected.iterrows():
    group = matched.loc[
        (matched["system"] == row["system"])
        & (matched["doc"] == row["doc"])
        & (matched["seg_id"] == row["seg_id"])
    ]

    categories = sorted(
        group["category"].dropna().astype(str).unique().tolist()
    )
    severities = sorted(
        group["severity"].dropna().astype(str).unique().tolist()
    )
    raters = group["rater"].dropna().astype(str).nunique()

    # Descriptive flags only; do not redefine the primary label.
    major_categories = group.loc[
        group["severity"].astype(str).str.casefold().eq("major"),
        "category",
    ].dropna().astype(str).tolist()

    summary_rows.append({
        "system": row["system"],
        "doc": row["doc"],
        "doc_id": row["doc_id"],
        "seg_id": row["seg_id"],
        "rank_LR_Base": row["rank_LR_Base"],
        "score_LR_Base": row["score_LR_Base"],
        "source": row["source"],
        "target": row["target"],
        "y_primary": row["y_primary"],
        "serious_votes": row["serious_votes"],
        "n_annotation_rows_matched": len(group),
        "n_distinct_raters_matched": raters,
        "categories_matched": " | ".join(categories),
        "severities_matched": " | ".join(severities),
        "has_any_major_annotation": bool(major_categories),
        "major_annotation_categories": " | ".join(sorted(set(major_categories))),
        "mqm_target_match": len(group) > 0,
    })

segment_summary = pd.DataFrame(summary_rows)

# Keep every candidate annotation row, including non-matching targets,
# so that unmatched annotations remain auditable.
annotation_columns = [
    "system", "doc", "doc_id", "seg_id", "rater",
    "source", "target", "category", "severity",
    "target_match", "target_normalized_mqm",
]

annotation_columns = [
    c for c in annotation_columns if c in annotations.columns
]

annotation_output = annotations[annotation_columns].copy()

annotation_output = annotation_output.rename(
    columns={
        "target": "target_annotation",
        "target_normalized_mqm": "target_normalized_annotation",
    }
)

category_summary = (
    matched.groupby(["category", "severity"], dropna=False)
    .size()
    .reset_index(name="annotation_rows")
    .sort_values("annotation_rows", ascending=False)
)

OUT_DIR.mkdir(parents=True, exist_ok=True)
segment_path = OUT_DIR / "dev_top20_zero_vote_segments.csv"
annotation_path = OUT_DIR / "dev_top20_zero_vote_annotations.csv"
summary_path = OUT_DIR / "dev_top20_zero_vote_summary.csv"
manifest_path = OUT_DIR / "dev_error_analysis_manifest.json"

segment_summary.to_csv(segment_path, index=False, encoding="utf-8-sig")
annotation_output.to_csv(annotation_path, index=False, encoding="utf-8-sig")
category_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

manifest = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "split": "development",
    "ranking_score": "score_LR_Base",
    "ranking_order": "descending; stable mergesort",
    "review_budget": "ceil(20% of 1554) = 311",
    "selected_condition": "serious_votes == 0 within top 20%",
    "expected_selected_segments": 180,
    "actual_selected_segments": int(len(segment_summary)),
    "unique_segment_keys": int(segment_summary[KEYS].drop_duplicates().shape[0]),
    "segments_with_matched_mqm_target": int(segment_summary["mqm_target_match"].sum()),
    "segments_without_matched_mqm_target": int((~segment_summary["mqm_target_match"]).sum()),
    "matched_annotation_rows": int(annotations["target_match"].sum()),
    "unmatched_candidate_annotation_rows": int((~annotations["target_match"]).sum()),
    "inputs": [str(DEV_PATH), str(PRED_PATH), str(MQM_PATH)],
    "outputs": [str(segment_path), str(annotation_path), str(summary_path)],
    "normalization": "Remove <v> span tags, Unicode NFKC, collapse whitespace",
    "note": (
        "serious_votes == 0 means the operational critical-error voting "
        "criterion was not met; it does not mean the translation is error-free. "
        "Annotation counts are not independent segment counts."
    ),
}

manifest_path.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("Analysis completed.")
print("Selected segments:", len(segment_summary))
print("Unique keys:", segment_summary[KEYS].drop_duplicates().shape[0])
print("Matched segments:", int(segment_summary["mqm_target_match"].sum()))
print("Unmatched segments:", int((~segment_summary["mqm_target_match"]).sum()))
print("Matched annotation rows:", int(annotations["target_match"].sum()))
print("\nOutputs:")
for path in [segment_path, annotation_path, summary_path, manifest_path]:
    print(path)
print("\nCategory/severity summary:")
print(category_summary.to_string(index=False))
