
from pathlib import Path
import pandas as pd

# =========================================================
# 1. PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

DEV_PATH = (
    ROOT / "results" / "week11"
    / "error_analysis_dev"
    / "dev_top20_error_analysis.csv"
)

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"

OUTPUT_DIR = (
    ROOT / "results" / "week11"
    / "error_analysis_dev"
    / "final_10_case_analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUTPUT_DIR / "dev_10_case_summary.csv"
OUTPUT_ANNOTATIONS = OUTPUT_DIR / "dev_10_case_raw_annotations.csv"

# =========================================================
# 2. SELECTED 10 CASES
# =========================================================

CASES = [
    (1, "Online-B.1590", "abcnews.363994", 5, 1317),
    (2, "eTranslation.737", "standard.co.uk.14516", 1, 1386),
    (3, "Huoshan_Translate.832", "standard.co.uk.14516", 2, 1387),
    (4, "Tohoku-AIP-NTT.890", "reuters.276702", 4, 538),
    (5, "eTranslation.737", "cnn.385556", 17, 1182),
    (6, "Online-B.1590", "latimes.431856", 7, 293),
    (7, "eTranslation.737", "brisbanetimes.com.au.225989", 8, 1066),
    (8, "Tencent_Translation.1520", "telegraph.421295", 8, 1360),
    (9, "Huoshan_Translate.832", "express.co.uk.10983", 9, 213),
    (10, "OPPO.1535", "stv.tv.21636", 6, 66),
]

KEYS = ["system", "doc", "doc_id", "seg_id"]

# Manual observations based on the original MT outputs
# and neighboring-segment checks already performed.
MANUAL_OBSERVATIONS = {
    1: (
        "Several Minor Accuracy/Mistranslation annotations; "
        "one Fluency/Grammar Major annotation. "
        "No specific critical omission confirmed."
    ),
    2: (
        "Visible missing whitespace in target: "
        "'Drogendeliktenangeklagt'."
    ),
    3: (
        "One annotator recorded Accuracy/Omission-Minor; "
        "two annotators recorded No-error."
    ),
    4: (
        "Fluency/Grammar-Minor recorded by two annotators; "
        "one annotator recorded No-error."
    ),
    5: (
        "Final source clause about political divisiveness is absent "
        "from target and next segment. One annotator recorded "
        "Accuracy/Omission-Minor."
    ),
    6: (
        "Visible missing whitespace in target: "
        "'Körperzurückgeführt'; multiple Minor annotations."
    ),
    7: (
        "Final source sentence about the EU taking the opportunity "
        "is absent from target and next segment. No explicit "
        "Accuracy/Omission annotation."
    ),
    8: (
        "No visible major issue identified in preliminary inspection; "
        "all three annotators recorded No-error."
    ),
    9: (
        "Visible missing whitespace in target: 'inihrer'; "
        "all three annotators recorded No-error."
    ),
    10: (
        "No omission confirmed by neighboring-segment inspection; "
        "MQM includes Accuracy/Omission-Minor."
    ),
}

INTERPRETATIONS = {
    1: "Major annotation belongs to Fluency, not the project's critical-error definition.",
    2: "Major annotation belongs to Style, not the project's critical-error definition.",
    3: "Annotator disagreement on a Minor omission.",
    4: "Minor fluency issue with one No-error judgment.",
    5: "Manually observed omission is also recorded as Minor by one annotator.",
    6: "Multiple Minor quality issues; no serious votes.",
    7: "Manual omission observation is not explicitly categorized as Omission in MQM.",
    8: "High-ranked example with unanimous No-error annotations.",
    9: "Surface-level spacing issue despite unanimous No-error annotations.",
    10: "MQM records Minor omission, but manual inspection did not confirm the suspected omission.",
}

# =========================================================
# 3. LOAD DATA
# =========================================================

print("Loading Dev top-20% CSV...")
dev = pd.read_csv(DEV_PATH)

print("Loading original MQM annotations...")
mqm = pd.read_csv(MQM_PATH, sep="\t")

for col in ["doc_id", "seg_id"]:
    dev[col] = pd.to_numeric(dev[col], errors="raise").astype(int)
    mqm[col] = pd.to_numeric(mqm[col], errors="raise").astype(int)

assert len(dev) == 180, f"Expected 180 Dev samples, got {len(dev)}"

required_dev_columns = [
    *KEYS,
    "rank_LR_Base",
    "score_LR_Base",
    "y_primary",
    "serious_votes",
]

missing = [c for c in required_dev_columns if c not in dev.columns]
if missing:
    raise ValueError(f"Missing columns in Dev CSV: {missing}")

# =========================================================
# 4. SELECT THE 10 CASES FROM DEV CSV
# =========================================================

selected_records = []

for case_no, system, doc, doc_id, seg_id in CASES:

    match = dev[
        (dev["system"] == system)
        & (dev["doc"] == doc)
        & (dev["doc_id"] == doc_id)
        & (dev["seg_id"] == seg_id)
    ]

    if len(match) != 1:
        raise ValueError(
            f"Case {case_no}: expected exactly 1 Dev row, "
            f"found {len(match)}"
        )

    row = match.iloc[0].to_dict()
    row["case"] = case_no
    selected_records.append(row)

selected = pd.DataFrame(selected_records)

# =========================================================
# 5. JOIN ORIGINAL MQM ANNOTATIONS
# =========================================================

annotation_frames = []

for _, row in selected.iterrows():

    subset = mqm[
        (mqm["system"] == row["system"])
        & (mqm["doc"] == row["doc"])
        & (mqm["doc_id"] == row["doc_id"])
        & (mqm["seg_id"] == row["seg_id"])
    ].copy()

    if subset.empty:
        raise ValueError(
            f"No original MQM rows for case {row['case']}"
        )

    subset["case"] = int(row["case"])
    annotation_frames.append(subset)

raw_annotations = pd.concat(
    annotation_frames,
    ignore_index=True
)

# Save raw annotation rows for auditability
raw_annotations.to_csv(
    OUTPUT_ANNOTATIONS,
    index=False,
    encoding="utf-8-sig"
)

# =========================================================
# 6. CALCULATE ANNOTATION-LEVEL METRICS
# =========================================================

summary_records = []

for _, row in selected.iterrows():

    case_no = int(row["case"])

    ann = raw_annotations[
        raw_annotations["case"] == case_no
    ].copy()

    ann["category"] = ann["category"].fillna("").astype(str)
    ann["severity"] = ann["severity"].fillna("").astype(str)

    # Serious rule used by the project:
    # Major Accuracy/* OR exact category Non-translation!
    ann["is_serious"] = (
        (
            (ann["severity"] == "Major")
            & ann["category"].str.startswith("Accuracy/")
        )
        |
        (ann["category"] == "Non-translation!")
    )

    votes_by_rater = (
        ann.groupby("rater")["is_serious"]
        .any()
        .astype(int)
    )

    serious_votes = int(votes_by_rater.sum())
    y_primary_recomputed = int(serious_votes >= 2)

    categories = sorted(
        set(ann["category"].dropna()) - {""}
    )

    severities = sorted(
        set(ann["severity"].dropna()) - {""}
    )

    has_major = bool((ann["severity"] == "Major").any())

    has_omission = bool(
        ann["category"].str.contains(
            "Omission", case=False, na=False
        ).any()
    )

    has_no_error = bool(
        (ann["category"] == "No-error").any()
    )

    has_accuracy = bool(
        ann["category"].str.startswith("Accuracy/").any()
    )

    annotation_details = []
    for _, a in ann.iterrows():
        annotation_details.append(
            f"{a['rater']}: {a['category']} ({a['severity']})"
        )

    # Check consistency with the saved Dev CSV
    saved_serious_votes = int(row["serious_votes"])
    saved_y = int(row["y_primary"])

    if serious_votes != saved_serious_votes:
        raise ValueError(
            f"Case {case_no}: serious_votes mismatch. "
            f"Raw MQM={serious_votes}, Dev CSV={saved_serious_votes}"
        )

    if y_primary_recomputed != saved_y:
        raise ValueError(
            f"Case {case_no}: y_primary mismatch. "
            f"Recomputed={y_primary_recomputed}, Dev CSV={saved_y}"
        )

    summary_records.append({
        "case": case_no,
        "system": row["system"],
        "document": row["doc"],
        "local_segment": int(row["doc_id"]),
        "global_segment": int(row["seg_id"]),
        "rank_LR_Base": row["rank_LR_Base"],
        "score_LR_Base": row["score_LR_Base"],
        "annotation_rows": len(ann),
        "annotator_count": ann["rater"].nunique(),
        "mqm_categories": " | ".join(categories),
        "mqm_severities": " | ".join(severities),
        "has_major": has_major,
        "has_omission": has_omission,
        "has_accuracy_error": has_accuracy,
        "has_no_error": has_no_error,
        "serious_votes": serious_votes,
        "y_primary": y_primary_recomputed,
        "annotation_details": " || ".join(annotation_details),
        "manual_observation": MANUAL_OBSERVATIONS[case_no],
        "interpretation": INTERPRETATIONS[case_no],
    })

summary = pd.DataFrame(summary_records)

# =========================================================
# 7. VALIDATION
# =========================================================

assert len(summary) == 10
assert summary["case"].nunique() == 10
assert summary["y_primary"].eq(0).all()
assert summary["serious_votes"].eq(0).all()

# =========================================================
# 8. EXPORT
# =========================================================

summary = summary.sort_values("case")

summary.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 80)
print("10-CASE SUMMARY COMPLETED")
print("=" * 80)

print("Cases:", len(summary))
print("All cases matched:", True)
print("All serious votes:", summary["serious_votes"].tolist())
print("All y_primary:", summary["y_primary"].tolist())

print("\nSUMMARY:")
print(
    summary[
        [
            "case",
            "rank_LR_Base",
            "score_LR_Base",
            "annotation_rows",
            "has_major",
            "has_omission",
            "has_no_error",
            "serious_votes",
            "y_primary",
        ]
    ].to_string(index=False)
)

print("\nOUTPUT FILES:")
print(OUTPUT_CSV)
print(OUTPUT_ANNOTATIONS)
