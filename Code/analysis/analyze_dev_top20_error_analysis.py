
from pathlib import Path
import re
import unicodedata
import pandas as pd

# =========================================================
# 1. PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"

ERROR_DIR = ROOT / "results" / "week10" / "error_analysis_dev"

ZERO_SEGMENTS_PATH = (
    ERROR_DIR / "dev_top20_zero_vote_segments.csv"
)

ZERO_ANNOTATIONS_PATH = (
    ERROR_DIR / "dev_top20_zero_vote_annotations.csv"
)

OUT_DIR = ROOT / "results" / "week11" / "error_analysis_dev"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Các hệ thống MT được sử dụng trong nghiên cứu
MT_SYSTEMS = {
    "eTranslation.737",
    "Huoshan_Translate.832",
    "Online-A.1574",
    "Online-B.1590",
    "OPPO.1535",
    "Tencent_Translation.1520",
    "Tohoku-AIP-NTT.890",
}

KEYS = ["system", "doc", "doc_id", "seg_id"]

# =========================================================
# 2. HELPER FUNCTIONS
# =========================================================

def normalize_text(value):
    """Chuẩn hóa văn bản để phục vụ kiểm tra."""
    value = "" if pd.isna(value) else str(value)

    # Xóa MQM markup
    value = re.sub(r"</?v>", "", value)

    # Unicode normalization
    value = unicodedata.normalize("NFKC", value)

    # Chuẩn hóa khoảng trắng
    value = re.sub(r"\s+", " ", value).strip()

    return value


def clean_keys(df):
    """Chuẩn hóa các khóa nối dữ liệu."""
    for col in KEYS:
        if col not in df.columns:
            raise ValueError(f"Missing required key: {col}")

        df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def save_csv(df, filename):
    path = OUT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print("Saved:", path)


# =========================================================
# 3. LOAD 180 ZERO-SERIOUS-VOTE SEGMENTS
# =========================================================

if not ZERO_SEGMENTS_PATH.exists():
    raise FileNotFoundError(ZERO_SEGMENTS_PATH)

segments = pd.read_csv(
    ZERO_SEGMENTS_PATH,
    dtype=str,
    keep_default_na=False
)

segments = clean_keys(segments)

# Chỉ giữ mỗi segment key một lần
segments = segments.drop_duplicates(subset=KEYS).copy()

print("Unique selected segments:", len(segments))

if len(segments) != 180:
    raise ValueError(
        f"Expected 180 unique segments, got {len(segments)}"
    )

# =========================================================
# 4. LOAD ORIGINAL MQM ANNOTATIONS
# =========================================================

mqm = pd.read_csv(
    MQM_PATH,
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3
)

required = set(
    KEYS + ["rater", "category", "severity", "target"]
)

missing = required - set(mqm.columns)

if missing:
    raise ValueError(
        f"Missing MQM columns: {sorted(missing)}"
    )

mqm = clean_keys(mqm)

for col in ["rater", "category", "severity"]:
    mqm[col] = mqm[col].fillna("").astype(str).str.strip()

# Chỉ phân tích 7 hệ thống MT
mqm = mqm[mqm["system"].isin(MT_SYSTEMS)].copy()

# Chuẩn hóa category và severity
mqm["category_norm"] = (
    mqm["category"].str.strip().str.casefold()
)

mqm["severity_norm"] = (
    mqm["severity"].str.strip().str.casefold()
)

# =========================================================
# 5. CLASSIFY EACH ANNOTATION ROW
# =========================================================

# No-error được nhận diện từ category hoặc severity.
is_no_error = (
    mqm["category_norm"].isin(
        {"no-error", "no error", "no_error"}
    )
    | mqm["severity_norm"].isin(
        {"no-error", "no error", "no_error"}
    )
)

mqm["is_no_error"] = is_no_error

mqm["is_minor"] = (
    mqm["severity_norm"] == "minor"
)

mqm["is_major"] = (
    mqm["severity_norm"] == "major"
)

mqm["is_neutral"] = (
    mqm["severity_norm"] == "neutral"
)

# Chỉ tính Minor/Major là lỗi MQM trong phân loại chính.
# Neutral được giữ thành nhóm riêng, không tự động xem là lỗi.
mqm["is_other_error"] = (
    mqm["is_minor"] | mqm["is_major"]
)

# Định nghĩa critical error của dự án
mqm["is_serious_row"] = (
    mqm["is_major"]
    & (
        mqm["category"].str.startswith(
            "Accuracy/", na=False
        )
        | mqm["category"].eq("Non-translation!")
    )
)

# =========================================================
# 6. JOIN SELECTED SEGMENTS WITH MQM BY SEGMENT KEYS
# =========================================================

annotations = segments[KEYS].merge(
    mqm,
    on=KEYS,
    how="left",
    indicator=True
)

annotations["matched"] = (
    annotations["_merge"] == "both"
)

matched = annotations[
    annotations["matched"]
].copy()

unmatched_keys = annotations[
    ~annotations["matched"]
][KEYS].drop_duplicates()

print("\n=== MATCH AUDIT ===")
print("Selected segments:", len(segments))
print("Matched segments:", matched[KEYS].drop_duplicates().shape[0])
print("Unmatched segments:", len(unmatched_keys))
print("Matched annotation rows:", len(matched))

# =========================================================
# 7. RATER-LEVEL AGGREGATION
# =========================================================

rater_detail = (
    matched.groupby(
        KEYS + ["rater"],
        dropna=False,
        as_index=False
    )
    .agg(
        has_minor=("is_minor", "max"),
        has_major=("is_major", "max"),
        has_neutral=("is_neutral", "max"),
        has_no_error=("is_no_error", "max"),
        has_other_error=("is_other_error", "max"),
        serious_vote=("is_serious_row", "max"),
        annotation_rows=("category", "size")
    )
)

# Bất đồng giữa annotators:
# Có ít nhất một rater ghi nhận lỗi Minor/Major
# và ít nhất một rater có No-error.
rater_segment = (
    rater_detail.groupby(
        KEYS,
        as_index=False
    )
    .agg(
        distinct_raters=("rater", "nunique"),
        raters_with_minor=("has_minor", "sum"),
        raters_with_major=("has_major", "sum"),
        raters_with_neutral=("has_neutral", "sum"),
        raters_with_no_error=("has_no_error", "sum"),
        raters_with_other_error=("has_other_error", "sum"),
        serious_votes_recomputed=("serious_vote", "sum"),
        annotation_rows=("annotation_rows", "sum")
    )
)

rater_segment["annotator_disagreement"] = (
    (rater_segment["raters_with_other_error"] > 0)
    & (rater_segment["raters_with_no_error"] > 0)
)

# =========================================================
# 8. SEGMENT-LEVEL ANNOTATION SUMMARY
# =========================================================

segment_summary = (
    matched.groupby(KEYS, as_index=False)
    .agg(
        annotation_rows=("category", "size"),
        distinct_categories=("category", "nunique"),
        has_minor=("is_minor", "max"),
        has_major=("is_major", "max"),
        has_neutral=("is_neutral", "max"),
        has_no_error=("is_no_error", "max"),
        has_other_error=("is_other_error", "max")
    )
)

# Tạo danh sách category và severity để dễ đọc
category_summary = (
    matched.groupby(KEYS)
    .agg(
        mqm_categories=(
            "category",
            lambda x: " | ".join(
                sorted(set(v for v in x if v))
            )
        ),
        mqm_severities=(
            "severity",
            lambda x: " | ".join(
                sorted(set(v for v in x if v))
            )
        )
    )
    .reset_index()
)

segment_summary = segment_summary.merge(
    category_summary,
    on=KEYS,
    how="left"
)

segment_summary = segment_summary.merge(
    rater_segment,
    on=KEYS,
    how="left",
    suffixes=("", "_rater")
)

# =========================================================
# 9. ASSIGN MQM ERROR STATUS
# =========================================================

def classify_status(row):

    if not row["has_other_error"] and row["has_no_error"]:
        return "No_MQM_Error_Recorded"

    if row["has_major"] and row["has_minor"]:
        return "Minor_and_Major_Error"

    if row["has_major"]:
        return "Major_NonCritical_Error"

    if row["has_minor"]:
        return "Minor_Error"

    if row["has_neutral"]:
        return "Neutral_Only_or_Unclear"

    return "Unclassified_or_No_Error_Record"


segment_summary["mqm_error_status"] = (
    segment_summary.apply(classify_status, axis=1)
)

# =========================================================
# 10. MERGE BACK WITH ALL 180 SELECTED SEGMENTS
# =========================================================

final = segments.merge(
    segment_summary,
    on=KEYS,
    how="left",
    validate="one_to_one"
)

# Nếu không có annotation khớp thì không gán là No-error.
final["mqm_error_status"] = (
    final["mqm_error_status"].fillna("Unmatched")
)

# =========================================================
# 11. CHECK SERIOUS VOTES
# =========================================================

if "serious_votes" in final.columns:
    final["serious_votes"] = pd.to_numeric(
        final["serious_votes"],
        errors="coerce"
    )

    if not final["serious_votes"].eq(0).all():
        raise ValueError(
            "Some selected segments do not have zero serious_votes."
        )

if "serious_votes_recomputed" in final.columns:
    if not final["serious_votes_recomputed"].fillna(0).eq(0).all():
        print(
            "WARNING: Recomputed serious votes differ from zero "
            "for some selected segments. Inspect these rows."
        )

# =========================================================
# 12. SUMMARY TABLE
# =========================================================

status_summary = (
    final["mqm_error_status"]
    .value_counts(dropna=False)
    .rename_axis("mqm_error_status")
    .reset_index(name="segment_count")
)

status_summary["percentage"] = (
    status_summary["segment_count"] / len(final) * 100
).round(2)

# Thống kê tổng quát
general_summary = pd.DataFrame([
    {
        "metric": "Selected unique segments",
        "value": len(final)
    },
    {
        "metric": "Matched segments",
        "value": int(final["annotation_rows"].notna().sum())
    },
    {
        "metric": "Segments with Minor error",
        "value": int(final["has_minor"].fillna(False).sum())
    },
    {
        "metric": "Segments with Major error",
        "value": int(final["has_major"].fillna(False).sum())
    },
    {
        "metric": "Segments with any Minor/Major error",
        "value": int(final["has_other_error"].fillna(False).sum())
    },
    {
        "metric": "Segments with No-error annotation",
        "value": int(final["has_no_error"].fillna(False).sum())
    },
    {
        "metric": "Segments with annotator disagreement",
        "value": int(
            final["annotator_disagreement"].fillna(False).sum()
        )
    },
    {
        "metric": "Unmatched segments",
        "value": int(
            final["mqm_error_status"].eq("Unmatched").sum()
        )
    }
])

# =========================================================
# 13. SELECT 10 CASES FOR MANUAL REVIEW
# =========================================================

# Ưu tiên:
# 1. Major non-critical
# 2. Minor + Major
# 3. Minor
# 4. Annotator disagreement
# 5. Neutral only / No-error

priority = {
    "Major_NonCritical_Error": 1,
    "Minor_and_Major_Error": 2,
    "Minor_Error": 3,
    "Neutral_Only_or_Unclear": 4,
    "No_MQM_Error_Recorded": 5,
    "Unmatched": 6
}

final["review_priority"] = (
    final["mqm_error_status"].map(priority).fillna(99)
)

# Chọn đa dạng theo tình trạng MQM.
# Trong từng nhóm, ưu tiên điểm LR cao nếu có cột điểm.
score_candidates = [
    "score_LR_Base",
    "score_LogisticRegression",
    "score_lr_base",
    "lr_score",
    "prediction_score"
]

score_col = next(
    (c for c in score_candidates if c in final.columns),
    None
)

if score_col:
    final[score_col] = pd.to_numeric(
        final[score_col],
        errors="coerce"
    )

    final = final.sort_values(
        ["review_priority", score_col],
        ascending=[True, False]
    )
else:
    final = final.sort_values(
        ["review_priority", "system", "doc", "seg_id"]
    )

# Lấy tối đa 10 trường hợp, ưu tiên các nhóm khác nhau
selected_cases = []

for status in [
    "Major_NonCritical_Error",
    "Minor_and_Major_Error",
    "Minor_Error",
    "Neutral_Only_or_Unclear",
    "No_MQM_Error_Recorded",
    "Unmatched"
]:
    group = final[
        final["mqm_error_status"] == status
    ]

    for _, row in group.iterrows():
        if len(selected_cases) >= 10:
            break

        selected_cases.append(row)

    if len(selected_cases) >= 10:
        break

cases = pd.DataFrame(selected_cases)

# Các cột để nhóm điền đánh giá thủ công
cases["manual_error_assessment"] = ""
cases["why_ranked_top20"] = ""
cases["team_interpretation"] = ""
cases["evidence_checked"] = ""

# =========================================================
# 14. EXPORT
# =========================================================

save_csv(
    final,
    "dev_top20_error_analysis.csv"
)

save_csv(
    cases,
    "dev_top20_error_analysis_10_cases.csv"
)

save_csv(
    status_summary,
    "dev_top20_error_analysis_status_summary.csv"
)

save_csv(
    general_summary,
    "dev_top20_error_analysis_summary.csv"
)

save_csv(
    rater_detail,
    "dev_top20_error_analysis_rater_detail.csv"
)

save_csv(
    unmatched_keys,
    "dev_top20_error_analysis_unmatched.csv"
)

# =========================================================
# 15. PRINT RESULTS
# =========================================================

print("\n=== MQM STATUS DISTRIBUTION ===")
print(status_summary.to_string(index=False))

print("\n=== GENERAL SUMMARY ===")
print(general_summary.to_string(index=False))

print("\n=== MANUAL REVIEW CASES ===")
print(
    cases[
        KEYS + ["mqm_error_status"]
    ].to_string(index=False)
)

print("\nAnalysis completed.")
