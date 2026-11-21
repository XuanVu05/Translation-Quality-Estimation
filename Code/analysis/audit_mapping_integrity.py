
from pathlib import Path
import pandas as pd

# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = ROOT / "results" / "week10" / "data_quality" / "mapping_integrity"

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

MQM_KEYS = ["system", "doc", "doc_id", "seg_id"]
MAPPING_KEYS = ["document_id", "segment_id", "line_id"]


# ============================================================
# 1. LOAD DATA
# ============================================================

print("=" * 70)
print("MAPPING INTEGRITY AUDIT")
print("=" * 70)

mqm = pd.read_csv(
    MQM_PATH,
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3,
    encoding="utf-8"
)

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

for col in MQM_KEYS:
    mqm[col] = mqm[col].str.strip()

for col in MAPPING_KEYS:
    mapping[col] = mapping[col].str.strip()

print("MQM rows:", len(mqm))
print("Mapping rows:", len(mapping))


# ============================================================
# 2. CHECK MAPPING STRUCTURE
# ============================================================

required_mapping = [
    "line_id",
    "testset",
    "lang_pair",
    "document_id",
    "segment_id"
]

missing_mapping_values = (
    mapping[required_mapping] == ""
).any(axis=1)

mapping_duplicate_line = mapping["line_id"].duplicated(keep=False)

mapping_duplicate_document_segment = mapping.duplicated(
    ["document_id", "segment_id"],
    keep=False
)

mapping_summary = pd.DataFrame([{
    "mapping_rows": len(mapping),
    "unique_line_ids": mapping["line_id"].nunique(),
    "unique_documents": mapping["document_id"].nunique(),
    "unique_document_segments": mapping[
        ["document_id", "segment_id"]
    ].drop_duplicates().shape[0],
    "missing_value_rows": int(missing_mapping_values.sum()),
    "duplicate_line_id_rows": int(mapping_duplicate_line.sum()),
    "duplicate_document_segment_rows": int(
        mapping_duplicate_document_segment.sum()
    ),
    "testsets": " | ".join(sorted(mapping["testset"].unique())),
    "language_pairs": " | ".join(sorted(mapping["lang_pair"].unique()))
}])

mapping_summary.to_csv(
    OUTPUT_DIR / "mapping_structure_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== MAPPING STRUCTURE ===")
print(mapping_summary.to_string(index=False))


# ============================================================
# 3. CHECK MAPPING LINE IDS
# ============================================================

mapping["line_id_num"] = pd.to_numeric(
    mapping["line_id"], errors="coerce"
)

expected_line_ids = set(range(1, len(mapping) + 1))
actual_line_ids = set(mapping["line_id_num"].dropna().astype(int))

missing_line_ids = sorted(expected_line_ids - actual_line_ids)
unexpected_line_ids = sorted(actual_line_ids - expected_line_ids)

print("\n=== LINE ID CHECK ===")
print("Missing line IDs:", missing_line_ids[:20])
print("Unexpected line IDs:", unexpected_line_ids[:20])

mapping_line_check = pd.DataFrame({
    "check": ["missing_line_ids", "unexpected_line_ids"],
    "count": [len(missing_line_ids), len(unexpected_line_ids)]
})

mapping_line_check.to_csv(
    OUTPUT_DIR / "mapping_line_id_check.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 4. EXTRACT UNIQUE MT SEGMENTS
# ============================================================

mt = mqm[mqm["system"].isin(MT_SYSTEMS)].copy()

mt_segments = mt[MQM_KEYS].drop_duplicates().copy()

print("\n=== MT SEGMENTS ===")
print("MT annotation rows:", len(mt))
print("MT unique system-segment keys:", len(mt_segments))
print("MT systems found:", mt["system"].nunique())


# ============================================================
# 5. CHECK MQM -> MAPPING ALIGNMENT
# ============================================================

# Hypothesized correspondence:
# MQM doc     -> mapping document_id
# MQM doc_id  -> mapping segment_id
# MQM seg_id  -> mapping line_id

mapping_for_join = mapping[
    ["line_id", "document_id", "segment_id"]
].copy()

mapping_for_join = mapping_for_join.rename(columns={
    "line_id": "seg_id",
    "document_id": "doc",
    "segment_id": "doc_id"
})

joined = mt_segments.merge(
    mapping_for_join,
    on=["doc", "doc_id", "seg_id"],
    how="left",
    indicator=True,
    validate="many_to_one"
)

matched = joined[joined["_merge"] == "both"].copy()
unmatched = joined[joined["_merge"] == "left_only"].copy()

print("\n=== MQM TO MAPPING ALIGNMENT ===")
print("Unique MT segment keys:", len(mt_segments))
print("Matched:", len(matched))
print("Unmatched:", len(unmatched))

unmatched.to_csv(
    OUTPUT_DIR / "mqm_unmatched_mapping.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 6. CHECK EACH MT SYSTEM
# ============================================================

system_results = []

for system in MT_SYSTEMS:
    system_segments = mt_segments[
        mt_segments["system"] == system
    ].copy()

    system_joined = system_segments.merge(
        mapping_for_join,
        on=["doc", "doc_id", "seg_id"],
        how="left",
        indicator=True,
        validate="many_to_one"
    )

    system_results.append({
        "system": system,
        "mqm_segments": len(system_segments),
        "matched_segments": int(
            (system_joined["_merge"] == "both").sum()
        ),
        "unmatched_segments": int(
            (system_joined["_merge"] == "left_only").sum()
        )
    })

system_summary = pd.DataFrame(system_results)

system_summary.to_csv(
    OUTPUT_DIR / "mapping_alignment_by_system.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== ALIGNMENT BY MT SYSTEM ===")
print(system_summary.to_string(index=False))


# ============================================================
# 7. CHECK DOCUMENT AND SEGMENT ID CONSISTENCY
# ============================================================

mqm_documents = set(mt_segments["doc"].unique())
mapping_documents = set(mapping["document_id"].unique())

missing_documents = sorted(mqm_documents - mapping_documents)
extra_documents = sorted(mapping_documents - mqm_documents)

document_summary = pd.DataFrame([{
    "mqm_documents": len(mqm_documents),
    "mapping_documents": len(mapping_documents),
    "documents_missing_in_mapping": len(missing_documents),
    "documents_not_in_mqm_mt": len(extra_documents)
}])

document_summary.to_csv(
    OUTPUT_DIR / "document_alignment_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== DOCUMENT ALIGNMENT ===")
print(document_summary.to_string(index=False))

print("\nDocuments missing in mapping:", missing_documents)
print("Mapping documents not in MT MQM:", extra_documents)


# ============================================================
# 8. FINAL SUMMARY
# ============================================================

checks = {
    "mapping_has_1418_rows": len(mapping) == 1418,
    "mapping_has_no_missing_values": not missing_mapping_values.any(),
    "mapping_line_ids_unique": not mapping_duplicate_line.any(),
    "mapping_document_segment_unique": not (
        mapping_duplicate_document_segment.any()
    ),
    "mapping_line_ids_contiguous": (
        len(missing_line_ids) == 0
        and len(unexpected_line_ids) == 0
    ),
    "all_mt_segments_matched": len(unmatched) == 0,
    "all_seven_systems_present": mt["system"].nunique() == 7,
    "each_system_has_1418_segments": (
        (system_summary["mqm_segments"] == 1418).all()
    ),
    "each_system_fully_matched": (
        (system_summary["unmatched_segments"] == 0).all()
    ),
    "all_documents_matched": len(missing_documents) == 0
}

check_df = pd.DataFrame([
    {"check": name, "passed": passed}
    for name, passed in checks.items()
])

check_df.to_csv(
    OUTPUT_DIR / "mapping_integrity_checks.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n=== FINAL CHECKS ===")
print(check_df.to_string(index=False))

print("\nPassed:", sum(checks.values()), "/", len(checks))
print("Output directory:", OUTPUT_DIR)

if all(checks.values()):
    print("\nMAPPING STRUCTURE AND KEY ALIGNMENT: PASSED")
else:
    print("\nMAPPING AUDIT: REQUIRES INVESTIGATION")
