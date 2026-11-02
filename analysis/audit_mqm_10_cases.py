
from pathlib import Path
import csv
import sys

import pandas as pd


# ============================================================
# 1. PATHS
# ============================================================

# File hiện tại nằm trong analysis/
# parents[1] chính là thư mục gốc Translation-Quality-Estimation/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = PROJECT_ROOT / "mqm_newstest2020_ende.tsv"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "week11"
    / "error_analysis_dev"
    / "mqm_10_cases_audit"
)

ANNOTATION_OUTPUT = OUTPUT_DIR / "mqm_10_cases_annotation_rows.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "mqm_10_cases_audit_summary.csv"
REPORT_OUTPUT = OUTPUT_DIR / "mqm_10_cases_audit_report.txt"


# ============================================================
# 2. TEN SELECTED CASES
#    Full key: system + doc + doc_id + seg_id
# ============================================================

CASES = [
    {
        "case_id": 1,
        "system": "Online-B.1590",
        "doc": "abcnews.363994",
        "doc_id": "5",
        "seg_id": "1317",
    },
    {
        "case_id": 2,
        "system": "eTranslation.737",
        "doc": "standard.co.uk.14516",
        "doc_id": "1",
        "seg_id": "1386",
    },
    {
        "case_id": 3,
        "system": "Huoshan_Translate.832",
        "doc": "standard.co.uk.14516",
        "doc_id": "2",
        "seg_id": "1387",
    },
    {
        "case_id": 4,
        "system": "Tohoku-AIP-NTT.890",
        "doc": "reuters.276702",
        "doc_id": "4",
        "seg_id": "538",
    },
    {
        "case_id": 5,
        "system": "eTranslation.737",
        "doc": "cnn.385556",
        "doc_id": "17",
        "seg_id": "1182",
    },
    {
        "case_id": 6,
        "system": "Online-B.1590",
        "doc": "latimes.431856",
        "doc_id": "7",
        "seg_id": "293",
    },
    {
        "case_id": 7,
        "system": "eTranslation.737",
        "doc": "brisbanetimes.com.au.225989",
        "doc_id": "8",
        "seg_id": "1066",
    },
    {
        "case_id": 8,
        "system": "Tencent_Translation.1520",
        "doc": "telegraph.421295",
        "doc_id": "8",
        "seg_id": "1360",
    },
    {
        "case_id": 9,
        "system": "Huoshan_Translate.832",
        "doc": "express.co.uk.10983",
        "doc_id": "9",
        "seg_id": "213",
    },
    {
        "case_id": 10,
        "system": "OPPO.1535",
        "doc": "stv.tv.21636",
        "doc_id": "6",
        "seg_id": "66",
    },
]

KEY_COLUMNS = ["system", "doc", "doc_id", "seg_id"]

REQUIRED_COLUMNS = [
    "system",
    "doc",
    "doc_id",
    "seg_id",
    "rater",
    "source",
    "target",
    "category",
    "severity",
]


# ============================================================
# 3. LOAD RAW MQM DATA
# ============================================================

def load_mqm_data():
    if not MQM_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy dữ liệu MQM:\n{MQM_PATH}"
        )

    df = pd.read_csv(
        MQM_PATH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
    )

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Thiếu các cột bắt buộc trong MQM: {missing_columns}"
        )

    # Chuẩn hóa kiểu dữ liệu dạng chuỗi, không thay đổi nội dung.
    for col in KEY_COLUMNS + ["rater", "category", "severity"]:
        df[col] = df[col].astype(str).str.strip()

    return df


# ============================================================
# 4. BUILD CASE TABLE
# ============================================================

def build_case_table():
    return pd.DataFrame(CASES).astype(
        {
            "case_id": int,
            "system": str,
            "doc": str,
            "doc_id": str,
            "seg_id": str,
        }
    )


# ============================================================
# 5. FILTER RAW ANNOTATIONS USING FULL KEY
# ============================================================

def extract_annotations(mqm, cases):
    parts = []

    for case in CASES:
        mask = pd.Series(True, index=mqm.index)

        for col in KEY_COLUMNS:
            mask &= mqm[col].eq(str(case[col]))

        matched = mqm.loc[mask].copy()

        if not matched.empty:
            matched.insert(0, "case_id", case["case_id"])
            parts.append(matched)

    if parts:
        annotations = pd.concat(parts, ignore_index=True)
    else:
        annotations = pd.DataFrame(
            columns=["case_id"] + list(mqm.columns)
        )

    return annotations


# ============================================================
# 6. APPLY PROJECT'S OPERATIONAL SERIOUS-ERROR RULE
#
# Serious error:
#   severity == Major AND (
#       category starts with "Accuracy/"
#       OR category == "Non-translation!"
#   )
#
# One vote per rater per segment.
# y_primary = 1 if at least 2 raters vote serious.
# ============================================================

def calculate_serious_labels(annotations):
    annotations = annotations.copy()

    if annotations.empty:
        annotations["is_serious_error"] = pd.Series(dtype=int)
        return annotations, pd.DataFrame()

    annotations["is_serious_error"] = (
        annotations["severity"].eq("Major")
        & (
            annotations["category"].str.startswith(
                "Accuracy/", na=False
            )
            | annotations["category"].eq("Non-translation!")
        )
    ).astype(int)

    # One vote per rater per case.
    # If a rater has multiple annotation rows, any qualifying
    # serious annotation gives that rater one serious vote.
    rater_votes = (
        annotations
        .groupby(["case_id"] + KEY_COLUMNS + ["rater"],
                 as_index=False)
        ["is_serious_error"]
        .max()
        .rename(columns={"is_serious_error": "rater_serious_vote"})
    )

    vote_summary = (
        rater_votes
        .groupby(["case_id"] + KEY_COLUMNS, as_index=False)
        .agg(
            n_raters=("rater", "nunique"),
            serious_votes=("rater_serious_vote", "sum"),
        )
    )

    vote_summary["y_primary_recomputed"] = (
        vote_summary["serious_votes"] >= 2
    ).astype(int)

    return annotations, vote_summary


# ============================================================
# 7. SUMMARIZE EACH CASE
# ============================================================

def summarize_cases(annotations, vote_summary):
    summaries = []

    for case in CASES:
        case_id = case["case_id"]

        subset = annotations[
            annotations["case_id"] == case_id
        ].copy()

        vote_row = vote_summary[
            vote_summary["case_id"] == case_id
        ]

        if subset.empty:
            summaries.append({
                **case,
                "annotation_rows": 0,
                "n_raters": 0,
                "n_major_annotations": 0,
                "n_serious_annotation_rows": 0,
                "serious_votes": 0,
                "y_primary_recomputed": 0,
                "categories": "",
                "severities": "",
                "status": "NO_MATCH",
            })
            continue

        if not vote_row.empty:
            n_raters = int(vote_row.iloc[0]["n_raters"])
            serious_votes = int(
                vote_row.iloc[0]["serious_votes"]
            )
            y_primary = int(
                vote_row.iloc[0]["y_primary_recomputed"]
            )
        else:
            n_raters = 0
            serious_votes = 0
            y_primary = 0

        summaries.append({
            **case,
            "annotation_rows": len(subset),
            "n_raters": n_raters,
            "n_major_annotations": int(
                subset["severity"].eq("Major").sum()
            ),
            "n_serious_annotation_rows": int(
                subset["is_serious_error"].sum()
            ),
            "serious_votes": serious_votes,
            "y_primary_recomputed": y_primary,
            "categories": " | ".join(
                sorted(set(
                    x for x in subset["category"].tolist() if x
                ))
            ),
            "severities": " | ".join(
                sorted(set(
                    x for x in subset["severity"].tolist() if x
                ))
            ),
            "status": "MATCHED",
        })

    return pd.DataFrame(summaries)


# ============================================================
# 8. WRITE HUMAN-READABLE REPORT
# ============================================================

def write_report(mqm, annotations, summary):
    total_cases = len(CASES)
    matched_cases = int((summary["status"] == "MATCHED").sum())
    unmatched_cases = total_cases - matched_cases

    total_annotation_rows = len(annotations)

    total_major = int(
        annotations["severity"].eq("Major").sum()
    ) if not annotations.empty else 0

    total_serious_rows = int(
        annotations["is_serious_error"].sum()
    ) if not annotations.empty else 0

    lines = [
        "MQM AUDIT REPORT – 10 SELECTED DEV CASES",
        "=" * 60,
        "",
        f"Raw MQM file: {MQM_PATH}",
        f"Total raw MQM rows: {len(mqm)}",
        f"Selected cases: {total_cases}",
        f"Matched cases: {matched_cases}",
        f"Unmatched cases: {unmatched_cases}",
        f"Matched annotation rows: {total_annotation_rows}",
        f"Major annotation rows: {total_major}",
        f"Serious annotation rows: {total_serious_rows}",
        "",
        "Operational serious-error rule:",
        'severity == "Major" AND (category starts with "Accuracy/"',
        'OR category == "Non-translation!")',
        "",
        "One serious vote per rater per segment.",
        "y_primary = 1 when serious_votes >= 2.",
        "",
        "CASE-LEVEL RESULTS",
        "-" * 60,
    ]

    for _, row in summary.iterrows():
        lines.extend([
            "",
            f"Case {row['case_id']}:",
            f"  Key: {row['system']} | {row['doc']} | "
            f"{row['doc_id']} | {row['seg_id']}",
            f"  Status: {row['status']}",
            f"  Annotation rows: {row['annotation_rows']}",
            f"  Raters: {row['n_raters']}",
            f"  Major annotations: {row['n_major_annotations']}",
            f"  Serious annotation rows: "
            f"{row['n_serious_annotation_rows']}",
            f"  Serious votes: {row['serious_votes']}",
            f"  Recomputed y_primary: "
            f"{row['y_primary_recomputed']}",
            f"  Categories: {row['categories']}",
            f"  Severities: {row['severities']}",
        ])

    lines.extend([
        "",
        "=" * 60,
        "IMPORTANT NOTES",
        "- This script audits raw MQM annotations only.",
        "- It does not retrain or modify any model.",
        "- It does not modify the locked Train/Dev/Test split.",
        "- It does not evaluate or tune against the Test set.",
        "- Category and severity are inspected row by row;",
        "  aggregated category/severity lists are not paired by position.",
        "",
    ])

    REPORT_OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


# ============================================================
# 9. MAIN
# ============================================================

def main():
    print("=" * 60)
    print("MQM AUDIT – 10 SELECTED DEV CASES")
    print("=" * 60)

    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"MQM file: {MQM_PATH}")

    mqm = load_mqm_data()
    cases = build_case_table()

    annotations = extract_annotations(mqm, cases)

    annotations, vote_summary = calculate_serious_labels(
        annotations
    )

    summary = summarize_cases(
        annotations,
        vote_summary
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    annotations.to_csv(
        ANNOTATION_OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    write_report(mqm, annotations, summary)

    print("\nAUDIT COMPLETED")
    print("-" * 60)
    print(f"Selected cases: {len(CASES)}")
    print(
        "Matched cases:",
        int((summary["status"] == "MATCHED").sum())
    )
    print(
        "Unmatched cases:",
        int((summary["status"] == "NO_MATCH").sum())
    )
    print(f"Annotation rows: {len(annotations)}")
    print(
        "Major annotation rows:",
        int(annotations["severity"].eq("Major").sum())
        if not annotations.empty else 0
    )
    print(
        "Serious annotation rows:",
        int(annotations["is_serious_error"].sum())
        if not annotations.empty else 0
    )

    print("\nOutput files:")
    print(ANNOTATION_OUTPUT)
    print(SUMMARY_OUTPUT)
    print(REPORT_OUTPUT)

    print("\nCase summary:")
    print(
        summary[
            [
                "case_id",
                "status",
                "annotation_rows",
                "n_raters",
                "n_major_annotations",
                "n_serious_annotation_rows",
                "serious_votes",
                "y_primary_recomputed",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
