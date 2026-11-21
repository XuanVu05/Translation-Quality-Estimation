
from pathlib import Path
import pandas as pd

# =========================================================
# 1. PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

BASE_DIR = (
    ROOT / "results" / "week11"
    / "error_analysis_dev"
)

FINAL_DIR = BASE_DIR / "final_10_case_analysis"

DEV_PATH = BASE_DIR / "dev_top20_error_analysis.csv"

ORIGINAL_PATH = (
    BASE_DIR / "original_mt_verification"
    / "original_mt_10_cases.csv"
)

SUMMARY_PATH = FINAL_DIR / "dev_10_case_summary.csv"

ANNOTATION_PATH = (
    FINAL_DIR / "dev_10_case_raw_annotations.csv"
)

SPAN_PATH = (
    FINAL_DIR / "dev_10_case_annotated_spans.csv"
)

OUTPUT_PATH = FINAL_DIR / "final_10_case_qualitative_evidence.csv"

# =========================================================
# 2. LOAD FILES
# =========================================================

paths = {
    "Dev 180": DEV_PATH,
    "Original MT": ORIGINAL_PATH,
    "Summary": SUMMARY_PATH,
    "Raw annotations": ANNOTATION_PATH,
    "Annotated spans": SPAN_PATH,
}

for name, path in paths.items():
    if not path.exists():
        raise FileNotFoundError(
            f"{name} file not found:\n{path}"
        )

print("Loading source files...")

dev = pd.read_csv(DEV_PATH)
original = pd.read_csv(ORIGINAL_PATH)
summary = pd.read_csv(SUMMARY_PATH)
annotations = pd.read_csv(ANNOTATION_PATH)
spans = pd.read_csv(SPAN_PATH)

# =========================================================
# 3. NORMALIZE ORIGINAL MT COLUMN NAMES
# =========================================================

rename_map = {
    "doc": "document",
    "doc_id": "local_segment",
    "seg_id": "global_segment",
    "global_seg_id": "global_segment",
}

original = original.rename(
    columns={
        old: new
        for old, new in rename_map.items()
        if old in original.columns
        and new not in original.columns
    }
)

# =========================================================
# 4. DEFINE JOIN KEY
# =========================================================

key_columns = [
    "system",
    "doc",
    "doc_id",
    "seg_id",
]

for col in ["doc_id", "seg_id"]:
    dev[col] = pd.to_numeric(dev[col], errors="raise").astype(int)

# Summary uses document/local_segment/global_segment
summary = summary.rename(
    columns={
        "document": "doc",
        "local_segment": "doc_id",
        "global_segment": "seg_id",
    }
)

for col in ["doc_id", "seg_id"]:
    summary[col] = pd.to_numeric(
        summary[col], errors="raise"
    ).astype(int)

# Normalize original MT keys
for col in ["local_segment", "global_segment"]:
    if col in original.columns:
        original[col] = pd.to_numeric(
            original[col], errors="raise"
        ).astype(int)

original = original.rename(
    columns={
        "local_segment": "doc_id",
        "global_segment": "seg_id",
        "document": "doc",
    }
)

# =========================================================
# 5. SELECT EXACT 10 CASES FROM SUMMARY
# =========================================================

selected = summary.copy()

if len(selected) != 10:
    raise ValueError(
        f"Expected 10 summary rows, got {len(selected)}"
    )

if selected[key_columns].duplicated().any():
    raise ValueError("Duplicate case keys in summary.")

# Verify every selected case exists exactly once in Dev 180
check_dev = selected[key_columns].merge(
    dev[key_columns],
    on=key_columns,
    how="left",
    indicator=True,
)

if not check_dev["_merge"].eq("both").all():
    raise ValueError("Some selected cases do not match Dev 180.")

# =========================================================
# 6. JOIN VERIFIED ORIGINAL SOURCE AND TARGET
# =========================================================

needed_original = [
    "system",
    "doc",
    "doc_id",
    "seg_id",
    "source",
    "target_original",
]

missing_original = [
    c for c in needed_original if c not in original.columns
]

if missing_original:
    raise ValueError(
        "Missing columns in original MT file: "
        + str(missing_original)
        + "\nAvailable columns: "
        + str(original.columns.tolist())
    )

original_selected = original[needed_original].copy()

# Standardize target column name for the final evidence table
original_selected = original_selected.rename(
    columns={"target_original": "original_mt_target"}
)

if original_selected[key_columns].duplicated().any():
    raise ValueError("Duplicate keys in original MT verification file.")

result = selected.merge(
    original_selected,
    on=key_columns,
    how="left",
    validate="one_to_one",
)

if result["original_mt_target"].isna().any():
    raise ValueError("Some original MT targets were not matched.")

# =========================================================
# 7. AGGREGATE RAW MQM ANNOTATIONS
# =========================================================

annotation_records = []

for _, row in result.iterrows():

    ann = annotations[
        (annotations["system"] == row["system"])
        & (annotations["doc"] == row["doc"])
        & (annotations["doc_id"] == row["doc_id"])
        & (annotations["seg_id"] == row["seg_id"])
    ].copy()

    if ann.empty:
        raise ValueError(
            f"No annotation rows for case {row['case']}"
        )

    details = []

    for _, a in ann.iterrows():
        details.append(
            f"{a['rater']}: {a['category']} ({a['severity']})"
        )

    annotation_records.append({
        "case": row["case"],
        "raw_annotation_count": len(ann),
        "annotator_count_verified": ann["rater"].nunique(),
        "raw_annotation_details": " || ".join(details),
    })

annotation_summary = pd.DataFrame(annotation_records)

result = result.merge(
    annotation_summary,
    on="case",
    how="left",
    validate="one_to_one",
)

# =========================================================
# 8. AGGREGATE ANNOTATED SPANS
# =========================================================

span_records = []

for _, row in result.iterrows():

    subset = spans[
        (spans["case"] == row["case"])
    ].copy()

    span_details = []

    for _, s in subset.iterrows():

        span_value = str(s.get("annotated_span", ""))

        if span_value and span_value != "nan":
            span_details.append(
                f"{s['rater']} | {s['category']} | "
                f"{s['severity']} | span={span_value}"
            )

    span_records.append({
        "case": row["case"],
        "annotated_span_details": " || ".join(span_details),
    })

span_summary = pd.DataFrame(span_records)

result = result.merge(
    span_summary,
    on="case",
    how="left",
    validate="one_to_one",
)

# =========================================================
# 9. ADD MANUAL EVIDENCE CLASSIFICATION
# =========================================================

manual_classification = {
    1: "No specific omission confirmed; Major annotation is Fluency/Grammar.",
    2: "Visible spacing issue; Major annotation is Style/Awkward.",
    3: "Potential omission of overdose information; one Minor Omission annotation.",
    4: "Minor Fluency/Grammar issues; annotator disagreement.",
    5: "Final clause omitted; confirmed by manual inspection and one Minor Omission annotation.",
    6: "Visible spacing issue and multiple Minor annotations.",
    7: "Final source sentence omitted; no explicit MQM Omission category.",
    8: "All three annotators recorded No-error.",
    9: "Visible spacing issue; all three annotators recorded No-error.",
    10: "MQM Omission-Minor annotation exists, but manual omission not confirmed.",
}

evidence_level = {
    1: "MQM annotation; no confirmed critical omission",
    2: "Surface observation and MQM annotation",
    3: "Manual semantic observation and MQM Minor Omission",
    4: "MQM Minor Fluency annotation",
    5: "Manual omission and MQM Minor Omission",
    6: "Surface observation and MQM Minor annotations",
    7: "Manual omission; MQM category differs",
    8: "Unanimous MQM No-error",
    9: "Surface observation; unanimous MQM No-error",
    10: "MQM Minor Omission; manual evidence inconclusive",
}

result["manual_classification"] = result["case"].map(
    manual_classification
)

result["evidence_level"] = result["case"].map(
    evidence_level
)

# =========================================================
# 10. FINAL VALIDATION
# =========================================================

if len(result) != 10:
    raise ValueError("Final table must contain exactly 10 rows.")

if result[key_columns].duplicated().any():
    raise ValueError("Duplicate cases found in final table.")

if result["source"].isna().any():
    raise ValueError("Missing source text.")

if result["original_mt_target"].isna().any():
    raise ValueError("Missing original MT target.")

if result["rank_LR_Base"].isna().any():
    raise ValueError("Missing LR rank.")

if result["score_LR_Base"].isna().any():
    raise ValueError("Missing LR score.")

# Verify rank and score against original 180-row Dev file
dev_scores = dev[
    key_columns + ["rank_LR_Base", "score_LR_Base"]
]

check_scores = result.merge(
    dev_scores,
    on=key_columns,
    how="left",
    suffixes=("_final", "_dev"),
    validate="one_to_one",
)

if not (
    check_scores["rank_LR_Base_final"]
    == check_scores["rank_LR_Base_dev"]
).all():
    raise ValueError("LR rank mismatch.")

if not (
    check_scores["score_LR_Base_final"]
    == check_scores["score_LR_Base_dev"]
).all():
    raise ValueError("LR score mismatch.")

# =========================================================
# 11. EXPORT
# =========================================================

preferred_columns = [
    "case",
    "system",
    "doc",
    "doc_id",
    "seg_id",
    "rank_LR_Base",
    "score_LR_Base",
    "source",
    "original_mt_target",
    "y_primary",
    "serious_votes",
    "annotation_rows",
    "annotator_count",
    "raw_annotation_count",
    "annotator_count_verified",
    "mqm_categories",
    "mqm_severities",
    "has_major",
    "has_omission",
    "has_no_error",
    "raw_annotation_details",
    "annotated_span_details",
    "manual_classification",
    "evidence_level",
    "interpretation",
]

available_columns = [
    c for c in preferred_columns if c in result.columns
]

result = result[available_columns].sort_values("case")

result.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

print("\n" + "=" * 80)
print("FINAL QUALITATIVE EVIDENCE TABLE CREATED")
print("=" * 80)

print("Number of cases:", len(result))
print("All source texts matched:", result["source"].notna().all())
print("All original MT targets matched:",
      result["original_mt_target"].notna().all())
print("All ranks and scores verified:", True)

print("\nCASE SUMMARY:")
print(
    result[
        [
            "case",
            "rank_LR_Base",
            "score_LR_Base",
            "annotation_rows",
            "mqm_categories",
            "serious_votes",
            "y_primary",
        ]
    ].to_string(index=False)
)

print("\nOUTPUT:")
print(OUTPUT_PATH)
