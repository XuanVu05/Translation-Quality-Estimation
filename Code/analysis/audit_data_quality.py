
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = ROOT / "analysis" / "data_quality_results"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 1. Load data
# --------------------------------------------------

mqm = pd.read_csv(MQM_PATH, sep="\t")

mapping = pd.read_csv(
    MAPPING_PATH,
    sep="\t",
    header=None,
    names=[
        "line_id",
        "testset",
        "langpair",
        "document_id",
        "segment_id",
    ],
)

# --------------------------------------------------
# 2. Basic structure
# --------------------------------------------------

report = {
    "mqm_shape": list(mqm.shape),
    "mapping_shape": list(mapping.shape),
    "mqm_columns": mqm.columns.tolist(),
    "mapping_columns": mapping.columns.tolist(),
}

# --------------------------------------------------
# 3. Missing values
# --------------------------------------------------

missing = pd.DataFrame({
    "column": mqm.columns,
    "missing_count": [
        int(mqm[col].isna().sum()) for col in mqm.columns
    ],
    "missing_percent": [
        round(float(mqm[col].isna().mean() * 100), 4)
        for col in mqm.columns
    ],
})

missing.to_csv(
    OUTPUT_DIR / "missing_values.csv",
    index=False
)

report["missing_total"] = int(mqm.isna().sum().sum())

# --------------------------------------------------
# 4. Exact duplicate rows
# --------------------------------------------------

exact_duplicates = int(mqm.duplicated().sum())

report["exact_duplicate_rows"] = exact_duplicates

# --------------------------------------------------
# 5. Duplicate annotation keys
# --------------------------------------------------

annotation_key = [
    "system", "doc", "doc_id", "seg_id", "rater"
]

duplicate_annotation_keys = int(
    mqm.duplicated(subset=annotation_key).sum()
)

report["duplicate_annotation_keys"] = (
    duplicate_annotation_keys
)

# --------------------------------------------------
# 6. Dataset distribution
# --------------------------------------------------

report["n_systems"] = int(mqm["system"].nunique())
report["n_documents"] = int(mqm["doc"].nunique())
report["n_raters"] = int(mqm["rater"].nunique())

report["n_unique_mqm_segments"] = int(
    mqm[["system", "doc", "doc_id", "seg_id"]]
    .drop_duplicates()
    .shape[0]
)

report["n_unique_segment_keys"] = int(
    mqm[["doc", "doc_id", "seg_id"]]
    .drop_duplicates()
    .shape[0]
)

# --------------------------------------------------
# 7. Category and severity distributions
# --------------------------------------------------

category_counts = (
    mqm["category"]
    .value_counts(dropna=False)
    .rename_axis("category")
    .reset_index(name="count")
)

severity_counts = (
    mqm["severity"]
    .value_counts(dropna=False)
    .rename_axis("severity")
    .reset_index(name="count")
)

category_counts.to_csv(
    OUTPUT_DIR / "category_distribution.csv",
    index=False
)

severity_counts.to_csv(
    OUTPUT_DIR / "severity_distribution.csv",
    index=False
)

# --------------------------------------------------
# 8. Mapping consistency
# --------------------------------------------------

mqm_keys = mqm[["doc", "doc_id", "seg_id"]].drop_duplicates()

mapping_keys = mapping[
    ["document_id", "segment_id", "line_id"]
].drop_duplicates()

mqm_keys = mqm_keys.rename(columns={
    "doc": "document_id",
    "doc_id": "segment_id",
    "seg_id": "line_id",
})

mapping_check = mqm_keys.merge(
    mapping_keys,
    on=["document_id", "segment_id", "line_id"],
    how="left",
    indicator=True,
)

unmatched = mapping_check[
    mapping_check["_merge"] == "left_only"
]

report["unique_mqm_mapping_keys"] = int(len(mqm_keys))
report["unmatched_mqm_mapping_keys"] = int(len(unmatched))

unmatched.to_csv(
    OUTPUT_DIR / "unmatched_mapping_keys.csv",
    index=False
)

# --------------------------------------------------
# 9. Mapping uniqueness
# --------------------------------------------------

report["mapping_duplicate_rows"] = int(
    mapping.duplicated().sum()
)

report["mapping_duplicate_line_ids"] = int(
    mapping["line_id"].duplicated().sum()
)

report["mapping_unique_documents"] = int(
    mapping["document_id"].nunique()
)

# --------------------------------------------------
# 10. Save report
# --------------------------------------------------

with open(
    OUTPUT_DIR / "data_quality_summary.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(report, f, indent=4, ensure_ascii=False)

print("=" * 60)
print("DATA QUALITY AUDIT")
print("=" * 60)

for key, value in report.items():
    print(f"{key}: {value}")

print("\nMISSING VALUES")
print(missing.to_string(index=False))

print("\nCATEGORY DISTRIBUTION")
print(category_counts.to_string(index=False))

print("\nSEVERITY DISTRIBUTION")
print(severity_counts.to_string(index=False))

print("\nResults saved to:")
print(OUTPUT_DIR)
