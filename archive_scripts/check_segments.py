
from pathlib import Path
import logging
import pandas as pd

# Paths
ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "results" / "week10" / "data_quality"
LOG_DIR = ROOT / "results" / "week10" / "logs"

OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "check_segments.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)

def save_csv(df, filename):
    df.to_csv(OUT_DIR / filename, index=False, encoding="utf-8-sig")

def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay du lieu: {DATA_PATH}")

    logging.info("Reading dataset: %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH, sep="\t", encoding="utf-8")

    required = {
        "system", "doc", "doc_id", "seg_id", "rater",
        "source", "target", "category", "severity"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Thieu cot bat buoc: {sorted(missing)}")

    # 1. Overall data summary
    summary = pd.DataFrame([
        {"metric": "annotation_rows", "value": len(df)},
        {"metric": "columns", "value": len(df.columns)},
        {"metric": "unique_systems", "value": df["system"].nunique()},
        {"metric": "unique_raters", "value": df["rater"].nunique()},
        {"metric": "unique_doc", "value": df["doc"].nunique()},
        {"metric": "unique_doc_id", "value": df["doc_id"].nunique()},
        {"metric": "unique_source", "value": df["source"].nunique()},
        {"metric": "unique_target", "value": df["target"].nunique()},
        {"metric": "exact_duplicate_rows", "value": int(df.duplicated().sum())},
    ])
    save_csv(summary, "data_summary.csv")

    # 2. Relationship between doc and doc_id
    doc_to_id = (
        df.groupby("doc")["doc_id"].nunique()
        .rename("num_doc_ids").reset_index()
    )
    id_to_doc = (
        df.groupby("doc_id")["doc"].nunique()
        .rename("num_docs").reset_index()
    )
    save_csv(
        doc_to_id[doc_to_id["num_doc_ids"] > 1],
        "docs_with_multiple_doc_ids.csv"
    )
    save_csv(
        id_to_doc[id_to_doc["num_docs"] > 1],
        "doc_ids_with_multiple_docs.csv"
    )

    mapping_summary = pd.DataFrame([
        {
            "check": "docs_with_multiple_doc_ids",
            "count": int((doc_to_id["num_doc_ids"] > 1).sum()),
        },
        {
            "check": "doc_ids_with_multiple_docs",
            "count": int((id_to_doc["num_docs"] > 1).sum()),
        },
        {
            "check": "unique_doc_doc_id_pairs",
            "count": len(df[["doc", "doc_id"]].drop_duplicates()),
        },
    ])
    save_csv(mapping_summary, "document_mapping_summary.csv")

    # 3. Candidate segment key
    segment_keys = ["system", "doc", "doc_id", "seg_id"]
    segment_stats = (
        df.groupby(segment_keys, dropna=False)
        .agg(
            annotation_rows=("rater", "size"),
            unique_raters=("rater", "nunique"),
            unique_sources=("source", "nunique"),
            unique_targets=("target", "nunique"),
        )
        .reset_index()
    )
    save_csv(segment_stats, "segment_statistics.csv")

    save_csv(
        segment_stats[
            (segment_stats["unique_sources"] > 1) |
            (segment_stats["unique_targets"] > 1)
        ],
        "segments_with_inconsistent_text.csv"
    )

    save_csv(
        segment_stats[segment_stats["annotation_rows"] != 3],
        "segments_not_having_three_rows.csv"
    )

    # 4. Multiple rows for the same segment and rater
    rater_keys = segment_keys + ["rater"]
    segment_rater_stats = (
        df.groupby(rater_keys, dropna=False)
        .size()
        .rename("rows")
        .reset_index()
    )
    save_csv(segment_rater_stats, "segment_rater_row_counts.csv")
    save_csv(
        segment_rater_stats[segment_rater_stats["rows"] > 1],
        "segment_rater_multiple_rows.csv"
    )

    # 5. Row-count distributions
    save_csv(
        segment_stats["annotation_rows"]
        .value_counts()
        .sort_index()
        .rename_axis("annotation_rows")
        .reset_index(name="num_segments"),
        "annotation_rows_distribution.csv"
    )

    save_csv(
        segment_stats["unique_raters"]
        .value_counts()
        .sort_index()
        .rename_axis("unique_raters")
        .reset_index(name="num_segments"),
        "unique_raters_distribution.csv"
    )

    # 6. System counts
    save_csv(
        df.groupby("system")
        .agg(
            annotation_rows=("rater", "size"),
            unique_segments=("seg_id", "nunique"),
            unique_docs=("doc", "nunique"),
        )
        .reset_index(),
        "system_summary.csv"
    )

    # 7. Exact duplicate rows for manual inspection
    duplicates = df[df.duplicated(keep=False)].sort_values(
        list(df.columns)
    )
    save_csv(duplicates, "exact_duplicate_rows.csv")

    logging.info("Dataset shape: %s", df.shape)
    logging.info("Unique docs: %d", df["doc"].nunique())
    logging.info("Unique doc_ids: %d", df["doc_id"].nunique())
    logging.info("Unique systems: %d", df["system"].nunique())
    logging.info("Unique raters: %d", df["rater"].nunique())
    logging.info("Exact duplicate rows: %d", int(df.duplicated().sum()))
    logging.info("Unique segments by candidate key: %d", len(segment_stats))
    logging.info("Segments with inconsistent source/target: %d",
                 len(segment_stats[
                     (segment_stats["unique_sources"] > 1) |
                     (segment_stats["unique_targets"] > 1)
                 ]))
    logging.info("Segments with multiple rows per segment-rater: %d",
                 int((segment_rater_stats["rows"] > 1).sum()))
    logging.info("Completed successfully. Output: %s", OUT_DIR)

    print("Kiem tra du lieu hoan tat.")
    print(f"So dong: {len(df):,}")
    print(f"So segment theo khoa dang kiem tra: {len(segment_stats):,}")
    print(f"So dong trung hoan toan: {int(df.duplicated().sum()):,}")
    print(f"Ket qua: {OUT_DIR}")
    print(f"Log: {LOG_DIR / 'check_segments.log'}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Data integrity check failed")
        print("LOI: Kiem tra file log de xem chi tiet.")
        raise
