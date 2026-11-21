
from pathlib import Path
import pandas as pd

# =========================================================
# 1. PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = (
    ROOT
    / "results"
    / "week11"
    / "error_analysis_dev"
    / "neighbor_segment_inspection"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# 2. CASES TO INSPECT
# Format:
# (case_number, system, document, local_segment, global_seg_id)
# =========================================================

CASES = [
    (5, "eTranslation.737", "cnn.385556", 17, 1182),
    (7, "eTranslation.737", "brisbanetimes.com.au.225989", 8, 1066),
    (10, "OPPO.1535", "stv.tv.21636", 6, 66),
]

# =========================================================
# 3. LOAD DATA
# =========================================================

print("Loading MQM data...")
mqm = pd.read_csv(MQM_PATH, sep="\t")

print("Loading mapping...")
mapping = pd.read_csv(
    MAPPING_PATH,
    sep="\t",
    header=None,
    names=[
        "global_id",
        "dataset",
        "language_pair",
        "document",
        "local_segment",
    ],
)

# Normalize key columns
mapping["global_id"] = pd.to_numeric(
    mapping["global_id"], errors="coerce"
)
mapping["local_segment"] = pd.to_numeric(
    mapping["local_segment"], errors="coerce"
)

mqm["doc_id"] = pd.to_numeric(mqm["doc_id"], errors="coerce")
mqm["seg_id"] = pd.to_numeric(mqm["seg_id"], errors="coerce")

# =========================================================
# 4. INSPECT NEIGHBORING SEGMENTS
# =========================================================

records = []

for case_no, system, document, local_seg, global_id in CASES:

    print("\n" + "=" * 90)
    print(f"CASE {case_no}: {document}")
    print(f"System: {system}")
    print(f"Target local segment: {local_seg}")
    print("=" * 90)

    # Check mapping for the original case
    check = mapping[
        (mapping["global_id"] == global_id)
        & (mapping["document"] == document)
        & (mapping["local_segment"] == local_seg)
    ]

    if check.empty:
        print("ERROR: Original mapping not found.")
        continue

    # Inspect previous, current, next segment
    for neighbor_local in range(local_seg - 1, local_seg + 2):

        map_row = mapping[
            (mapping["document"] == document)
            & (mapping["local_segment"] == neighbor_local)
        ]

        if map_row.empty:
            print(f"\nLOCAL SEGMENT {neighbor_local}: NOT FOUND IN MAPPING")
            continue

        # There should normally be one mapping row
        map_row = map_row.iloc[0]
        neighbor_global = int(map_row["global_id"])

        # Retrieve source from MQM
        source_rows = mqm[
            (mqm["doc"] == document)
            & (mqm["doc_id"] == neighbor_local)
            & (mqm["seg_id"] == neighbor_global)
        ]

        if source_rows.empty:
            source = "[SOURCE NOT FOUND IN MQM]"
        else:
            source_values = source_rows["source"].dropna().unique()
            source = source_values[0] if len(source_values) else ""

        # Retrieve original MT target
        output_path = ROOT / "original_outputs" / (
            f"newstest2020.en-de.{system}.txt"
        )

        if not output_path.exists():
            target = f"[OUTPUT FILE NOT FOUND: {output_path}]"
        else:
            output_lines = output_path.read_text(
                encoding="utf-8"
            ).splitlines()

            if neighbor_global < 1 or neighbor_global > len(output_lines):
                target = "[GLOBAL ID OUT OF RANGE]"
            else:
                target = output_lines[neighbor_global - 1]

        label = (
            "PREVIOUS"
            if neighbor_local < local_seg
            else "CURRENT"
            if neighbor_local == local_seg
            else "NEXT"
        )

        print(f"\n--- {label}: LOCAL SEGMENT {neighbor_local} "
              f"| GLOBAL ID {neighbor_global} ---")
        print("\nSOURCE:")
        print(source)
        print("\nORIGINAL MT TARGET:")
        print(target)

        records.append({
            "case": case_no,
            "system": system,
            "document": document,
            "position": label,
            "local_segment": neighbor_local,
            "global_seg_id": neighbor_global,
            "source": source,
            "original_mt_target": target,
        })

# =========================================================
# 5. SAVE RESULTS
# =========================================================

result_df = pd.DataFrame(records)

csv_path = OUTPUT_DIR / "neighbor_segments_3_cases.csv"
txt_path = OUTPUT_DIR / "neighbor_segments_3_cases.txt"

result_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

with open(txt_path, "w", encoding="utf-8") as f:
    for _, row in result_df.iterrows():
        f.write("\n" + "=" * 80 + "\n")
        f.write(
            f"CASE {row['case']} | {row['position']} | "
            f"LOCAL {row['local_segment']} | "
            f"GLOBAL {row['global_seg_id']}\n"
        )
        f.write(f"SYSTEM: {row['system']}\n")
        f.write(f"DOCUMENT: {row['document']}\n\n")
        f.write("SOURCE:\n")
        f.write(str(row["source"]) + "\n\n")
        f.write("ORIGINAL MT TARGET:\n")
        f.write(str(row["original_mt_target"]) + "\n")

print("\n" + "=" * 90)
print("INSPECTION COMPLETED")
print(f"Segments extracted: {len(result_df)}")
print(f"CSV: {csv_path}")
print(f"TXT: {txt_path}")
print("=" * 90)
