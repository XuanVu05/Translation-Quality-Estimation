
from pathlib import Path
import csv
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = ROOT / "original_outputs"

RESULT_DIR = (
    ROOT / "results" / "week11" / "error_analysis_dev"
    / "original_mt_verification"
)


# ============================================================
# 2. TEN SELECTED CASES
# ============================================================

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


# ============================================================
# 3. LOAD FILES
# ============================================================

def load_files():
    for path in [MQM_PATH, MAPPING_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy: {path}")

    mqm = pd.read_csv(
        MQM_PATH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
    )

    mapping = pd.read_csv(
        MAPPING_PATH,
        sep="\t",
        header=None,
        dtype=str,
        keep_default_na=False,
    )

    if mapping.shape[1] < 5:
        raise ValueError(
            "File en-de.txt không có đủ 5 cột như dự kiến."
        )

    mapping = mapping.iloc[:, :5].copy()
    mapping.columns = [
        "line_id",
        "dataset",
        "language_pair",
        "doc",
        "local_segment",
    ]

    return mqm, mapping


# ============================================================
# 4. VERIFY MAPPING AND EXTRACT MT OUTPUT
# ============================================================

def main():
    mqm, mapping = load_files()

    results = []

    print("=" * 75)
    print("VERIFY ORIGINAL MT OUTPUTS – 10 DEV CASES")
    print("=" * 75)

    print("MQM rows:", len(mqm))
    print("Mapping rows:", len(mapping))

    for case_id, system, doc, doc_id, seg_id in CASES:

        print("\n" + "-" * 75)
        print(f"CASE {case_id}")
        print(f"System: {system}")
        print(f"Document: {doc}")
        print(f"Local segment: {doc_id}")
        print(f"Global segment ID: {seg_id}")

        # ----------------------------------------------------
        # A. Verify mapping
        # ----------------------------------------------------

        map_row = mapping[
            mapping["line_id"].eq(str(seg_id))
        ]

        if len(map_row) != 1:
            print(
                "MAPPING ERROR:",
                f"Expected 1 row, found {len(map_row)}"
            )
            continue

        map_record = map_row.iloc[0]

        mapping_doc = map_record["doc"]
        mapping_local_segment = map_record["local_segment"]

        mapping_ok = (
            mapping_doc == doc
            and mapping_local_segment == str(doc_id)
        )

        print("Mapping document:", mapping_doc)
        print("Mapping local segment:", mapping_local_segment)
        print("Mapping validation:", "PASS" if mapping_ok else "FAIL")

        if not mapping_ok:
            print("Không đọc output vì mapping không khớp.")
            continue

        # ----------------------------------------------------
        # B. Get source from original MQM data
        # ----------------------------------------------------

        mask = (
            mqm["system"].eq(system)
            & mqm["doc"].eq(doc)
            & mqm["doc_id"].eq(str(doc_id))
            & mqm["seg_id"].eq(str(seg_id))
        )

        mqm_rows = mqm.loc[mask]

        if mqm_rows.empty:
            source = ""
            print("WARNING: Không tìm thấy Source trong MQM.")
        else:
            source_values = mqm_rows["source"].drop_duplicates()
            source = source_values.iloc[0]

            print("\nSOURCE:")
            print(source)

        # ----------------------------------------------------
        # C. Read correct line from original MT output
        # ----------------------------------------------------

        output_file = (
            OUTPUT_DIR
            / f"newstest2020.en-de.{system}.txt"
        )

        if not output_file.exists():
            print("OUTPUT FILE NOT FOUND:", output_file)
            continue

        output_lines = output_file.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()

        line_number = int(seg_id)

        if line_number < 1 or line_number > len(output_lines):
            print(
                f"OUTPUT LINE ERROR: {line_number}, "
                f"total lines = {len(output_lines)}"
            )
            continue

        target = output_lines[line_number - 1]

        print("\nORIGINAL MT TARGET:")
        print(target)

        results.append({
            "case_id": case_id,
            "system": system,
            "doc": doc,
            "doc_id": doc_id,
            "seg_id": seg_id,
            "mapping_ok": mapping_ok,
            "source": source,
            "target_original": target,
            "output_line": line_number,
        })

    # ========================================================
    # 5. EXPORT RESULTS
    # ========================================================

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    result_df = pd.DataFrame(results)

    output_csv = RESULT_DIR / "original_mt_10_cases.csv"

    result_df.to_csv(
        output_csv,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 75)
    print("VERIFICATION COMPLETED")
    print("=" * 75)
    print("Successfully extracted:", len(result_df), "/ 10")
    print("Output:", output_csv)


if __name__ == "__main__":
    main()
