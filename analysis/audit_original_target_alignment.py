
from pathlib import Path
import re
import pandas as pd

# ============================================================
# 1. PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
ORIGINAL_OUTPUT_DIR = ROOT / "original_outputs"

OUTPUT_DIR = (
    ROOT / "results"
    / "week10"
    / "data_quality"
    / "target_alignment"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MT_SYSTEMS = [
    "eTranslation.737",
    "Huoshan_Translate.832",
    "Online-A.1574",
    "Online-B.1590",
    "OPPO.1535",
    "Tencent_Translation.1520",
    "Tohoku-AIP-NTT.890",
]

KEYS = ["system", "doc", "doc_id", "seg_id"]

OUTPUT_FILE_PATTERN = "newstest2020.en-de.{}.txt"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def remove_v_markup(text):
    """
    Remove only MQM <v> and </v> annotation tags.
    Do not remove quotation marks or punctuation.
    """
    return re.sub(
        r"</?v>",
        "",
        str(text),
        flags=re.IGNORECASE
    )


def normalize_whitespace(text):
    """
    Normalize whitespace only.
    Preserve words and punctuation.
    """
    return re.sub(r"\s+", " ", str(text)).strip()


def load_original_outputs():
    """
    Load all 7 original MT output files.
    Check that every file has exactly 1418 lines.
    """

    outputs = {}

    for system in MT_SYSTEMS:

        filename = OUTPUT_FILE_PATTERN.format(system)

        filepath = ORIGINAL_OUTPUT_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"Original output file not found: {filepath}"
            )

        lines = filepath.read_text(
            encoding="utf-8-sig"
        ).splitlines()

        if len(lines) != 1418:
            raise ValueError(
                f"{system}: expected 1418 lines, "
                f"found {len(lines)}"
            )

        outputs[system] = lines

        print(
            f"Loaded {system}: {len(lines)} lines"
        )

    return outputs


# ============================================================
# 3. LOAD MQM DATA
# ============================================================

print("=" * 70)
print("ORIGINAL MT TARGET ALIGNMENT AUDIT")
print("=" * 70)

if not MQM_PATH.exists():
    raise FileNotFoundError(
        f"MQM file not found: {MQM_PATH}"
    )

if not MAPPING_PATH.exists():
    raise FileNotFoundError(
        f"Mapping file not found: {MAPPING_PATH}"
    )

mqm = pd.read_csv(
    MQM_PATH,
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3,
    encoding="utf-8"
)

required_mqm_columns = [
    "system",
    "doc",
    "doc_id",
    "seg_id",
    "rater",
    "target",
    "category",
    "severity"
]

missing_columns = [
    col for col in required_mqm_columns
    if col not in mqm.columns
]

if missing_columns:
    raise ValueError(
        f"Missing MQM columns: {missing_columns}"
    )

for col in KEYS:
    mqm[col] = mqm[col].astype(str).str.strip()

print("\n=== MQM DATA ===")
print("Raw annotation rows:", len(mqm))
print("Raw systems:", mqm["system"].nunique())
print("Documents:", mqm["doc"].nunique())


# ============================================================
# 4. LOAD AND PREPARE MAPPING
# ============================================================

mapping = pd.read_csv(
    MAPPING_PATH,
    sep="\t",
    header=None,
    names=[
        "line_id",
        "testset",
        "lang_pair",
        "document_id",
        "segment_id"
    ],
    dtype=str,
    keep_default_na=False,
    encoding="utf-8"
)

if len(mapping) != 1418:
    raise ValueError(
        f"Expected 1418 mapping rows, found {len(mapping)}"
    )

mapping = mapping.rename(
    columns={
        "document_id": "doc",
        "segment_id": "doc_id"
    }
)

for col in ["line_id", "doc", "doc_id"]:
    mapping[col] = (
        mapping[col].astype(str).str.strip()
    )

# Check mapping line IDs
mapping["line_id_num"] = pd.to_numeric(
    mapping["line_id"],
    errors="raise"
).astype(int)

expected_ids = set(range(1, 1419))
actual_ids = set(mapping["line_id_num"])

if actual_ids != expected_ids:
    raise ValueError(
        "Mapping line IDs are not continuous from 1 to 1418."
    )

# Check mapping uniqueness
if mapping["line_id"].duplicated().any():
    raise ValueError("Duplicate mapping line IDs found.")

if mapping.duplicated(["doc", "doc_id"]).any():
    raise ValueError(
        "Duplicate document-segment mapping keys found."
    )

print("\n=== MAPPING ===")
print("Mapping rows:", len(mapping))
print("Unique documents:", mapping["doc"].nunique())
print("Unique document-segment pairs:",
      mapping[["doc", "doc_id"]].drop_duplicates().shape[0])


# ============================================================
# 5. FILTER MT SYSTEMS
# ============================================================

mt = mqm[
    mqm["system"].isin(MT_SYSTEMS)
].copy()

if mt["system"].nunique() != 7:
    raise ValueError(
        f"Expected 7 MT systems, found {mt['system'].nunique()}"
    )

mt_segment_count = mt[KEYS].drop_duplicates().shape[0]

if mt_segment_count != 9926:
    raise ValueError(
        f"Expected 9926 MT segments, found {mt_segment_count}"
    )

print("\n=== MT DATA ===")
print("MT annotation rows:", len(mt))
print("MT systems:", mt["system"].nunique())
print("MT unique segment keys:", mt_segment_count)


# ============================================================
# 6. ALIGN MQM SEGMENTS WITH MAPPING
# ============================================================

# Join:
# MQM.doc     -> mapping.doc
# MQM.doc_id  -> mapping.doc_id
# MQM.seg_id  -> mapping.line_id

mt = mt.merge(
    mapping[
        ["doc", "doc_id", "line_id", "line_id_num"]
    ],
    left_on=["doc", "doc_id", "seg_id"],
    right_on=["doc", "doc_id", "line_id"],
    how="left",
    validate="many_to_one",
    indicator=True
)

unmatched = mt[
    mt["_merge"] != "both"
].copy()

print("\n=== MQM TO MAPPING ALIGNMENT ===")
print("MT annotation rows:", len(mt))
print("Matched annotation rows:",
      (mt["_merge"] == "both").sum())
print("Unmatched annotation rows:", len(unmatched))

if len(unmatched) > 0:

    unmatched.to_csv(
        OUTPUT_DIR / "unmatched_mqm_rows.csv",
        index=False,
        encoding="utf-8-sig"
    )

    raise ValueError(
        f"Found {len(unmatched)} unmatched MQM rows. "
        "See unmatched_mqm_rows.csv."
    )

mt["line_id"] = mt["line_id_num"].astype(int)

mt = mt.drop(
    columns=["_merge", "line_id_num"]
)


# ============================================================
# 7. CHECK ALIGNMENT BY SYSTEM
# ============================================================

system_alignment = (
    mt.groupby("system")
    .agg(
        annotation_rows=("seg_id", "size"),
        unique_segments=("seg_id", "nunique"),
        matched_rows=("line_id", "count")
    )
    .reset_index()
)

system_alignment.to_csv(
    OUTPUT_DIR / "mapping_alignment_by_system.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== ALIGNMENT BY SYSTEM ===")
print(system_alignment.to_string(index=False))


# ============================================================
# 8. LOAD ORIGINAL MT OUTPUTS
# ============================================================

print("\n=== LOADING ORIGINAL OUTPUTS ===")

original_outputs = load_original_outputs()


# ============================================================
# 9. ATTACH ORIGINAL TARGET TO MQM ROWS
# ============================================================

# Use the mapping line_id to retrieve the original output.
# Python index starts at 0, mapping line_id starts at 1.

mt["original_target"] = [
    original_outputs[system][line_id - 1]
    for system, line_id in zip(
        mt["system"],
        mt["line_id"]
    )
]

if mt["original_target"].isna().any():
    raise ValueError(
        "Missing original target values were found."
    )

# Remove only MQM annotation markup
mt["target_without_v_markup"] = (
    mt["target"].map(remove_v_markup)
)

# Normalize whitespace for secondary comparison
mt["original_normalized"] = (
    mt["original_target"].map(normalize_whitespace)
)

mt["target_normalized"] = (
    mt["target_without_v_markup"].map(normalize_whitespace)
)


# ============================================================
# 10. COMPARE TARGETS
# ============================================================

# Strict comparison after removing only <v> tags
mt["match_after_markup_removal"] = (
    mt["target_without_v_markup"]
    == mt["original_target"]
)

# Comparison after removing markup and normalizing whitespace
mt["match_after_whitespace_normalization"] = (
    mt["target_normalized"]
    == mt["original_normalized"]
)


# ============================================================
# 11. ROW-LEVEL MATCH SUMMARY
# ============================================================

row_summary = (
    mt.groupby("system")
    .agg(
        annotation_rows=("target", "size"),
        exact_matches_after_markup=(
            "match_after_markup_removal",
            "sum"
        ),
        matches_after_whitespace=(
            "match_after_whitespace_normalization",
            "sum"
        )
    )
    .reset_index()
)

row_summary["exact_match_rate"] = (
    row_summary["exact_matches_after_markup"]
    / row_summary["annotation_rows"]
)

row_summary["whitespace_match_rate"] = (
    row_summary["matches_after_whitespace"]
    / row_summary["annotation_rows"]
)

row_summary.to_csv(
    OUTPUT_DIR / "target_row_match_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== ROW-LEVEL TARGET MATCH ===")
print(row_summary.to_string(index=False))


# ============================================================
# 12. SEGMENT-LEVEL TARGET VARIANTS
# ============================================================

segment_summary = (
    mt.groupby(KEYS)
    .agg(
        annotation_rows=("target", "size"),
        unique_raw_targets=("target", "nunique"),
        unique_targets_after_markup=(
            "target_without_v_markup",
            "nunique"
        ),
        unique_original_targets=(
            "original_target",
            "nunique"
        ),
        all_rows_match=(
            "match_after_whitespace_normalization",
            "all"
        )
    )
    .reset_index()
)

segment_summary.to_csv(
    OUTPUT_DIR / "target_segment_match_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== SEGMENT-LEVEL SUMMARY ===")
print("MT segments:", len(segment_summary))

print(
    "Segments with multiple raw targets:",
    (segment_summary["unique_raw_targets"] > 1).sum()
)

print(
    "Segments with multiple targets after markup removal:",
    (segment_summary["unique_targets_after_markup"] > 1).sum()
)

print(
    "Segments with multiple original targets:",
    (segment_summary["unique_original_targets"] > 1).sum()
)

print(
    "Segments where all annotation rows match original:",
    segment_summary["all_rows_match"].sum()
)


# ============================================================
# 13. EXPORT MISMATCH CASES
# ============================================================

mismatches = mt[
    ~mt["match_after_whitespace_normalization"]
].copy()

mismatch_columns = [
    "system",
    "doc",
    "doc_id",
    "seg_id",
    "line_id",
    "rater",
    "category",
    "severity",
    "target",
    "target_without_v_markup",
    "original_target"
]

mismatches[mismatch_columns].to_csv(
    OUTPUT_DIR / "target_mismatch_cases.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== MISMATCHES ===")
print("Mismatch annotation rows:", len(mismatches))

if len(mismatches) > 0:

    print("\nFirst 10 mismatch examples:")

    for _, row in mismatches.head(10).iterrows():

        print("\n" + "-" * 70)
        print("System:", row["system"])
        print("Document:", row["doc"])
        print("doc_id:", row["doc_id"])
        print("seg_id:", row["seg_id"])
        print("line_id:", row["line_id"])
        print("Rater:", row["rater"])
        print("Category:", row["category"])
        print("Severity:", row["severity"])

        print("Target raw:")
        print(repr(row["target"]))

        print("Target without markup:")
        print(repr(row["target_without_v_markup"]))

        print("Original output:")
        print(repr(row["original_target"]))

else:
    print("No target mismatches found.")


# ============================================================
# 14. RAW ANNOTATION ROWS BY SYSTEM
# ============================================================

raw_system_counts = (
    mqm.groupby("system")
    .size()
    .reset_index(name="annotation_rows")
)

raw_system_counts.to_csv(
    OUTPUT_DIR / "raw_annotation_rows_by_system.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== RAW ANNOTATION ROWS BY SYSTEM ===")
print(raw_system_counts.to_string(index=False))


# ============================================================
# 15. FINAL AUDIT SUMMARY
# ============================================================

final_checks = {
    "seven_mt_systems_present": mt["system"].nunique() == 7,
    "expected_mt_segments": mt_segment_count == 9926,
    "all_mqm_rows_mapped": len(unmatched) == 0,
    "seven_original_outputs_loaded": len(original_outputs) == 7,
    "all_original_outputs_have_1418_lines": all(
        len(lines) == 1418
        for lines in original_outputs.values()
    ),
    "all_mqms_have_original_targets": (
        mt["original_target"].notna().all()
    )
}

final_check_df = pd.DataFrame([
    {"check": name, "passed": passed}
    for name, passed in final_checks.items()
])

final_check_df.to_csv(
    OUTPUT_DIR / "target_alignment_final_checks.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== FINAL CHECKS ===")
print(final_check_df.to_string(index=False))

print(
    "\nPassed:",
    sum(final_checks.values()),
    "/",
    len(final_checks)
)

print("\n=== OUTPUT FILES ===")

for path in sorted(OUTPUT_DIR.glob("*.csv")):
    print(path.name)

print("\nOutput directory:", OUTPUT_DIR)

print("\nTARGET ALIGNMENT AUDIT COMPLETED.")
