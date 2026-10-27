
from pathlib import Path
import logging
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
LOG = ROOT / "results" / "week10" / "logs"

OUT.mkdir(parents=True, exist_ok=True)
LOG.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG / "data_quality_summary.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)

def main():
    df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

    # Summary by document
    doc_summary = (
        df.groupby("doc")
        .agg(
            unique_doc_ids=("doc_id", "nunique"),
            unique_segments=("seg_id", "nunique"),
            unique_systems=("system", "nunique"),
        )
        .reset_index()
    )
    doc_summary.to_csv(
        OUT / "document_level_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Segment-level summary
    keys = ["system", "doc", "doc_id", "seg_id"]
    segment_summary = (
        df.groupby(keys)
        .agg(
            annotation_rows=("rater", "size"),
            unique_raters=("rater", "nunique"),
            unique_sources=("source", "nunique"),
            unique_targets=("target", "nunique"),
        )
        .reset_index()
    )
    segment_summary.to_csv(
        OUT / "segment_level_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Rater-level aggregation check
    rater_keys = keys + ["rater"]
    rater_summary = (
        df.groupby(rater_keys)
        .agg(
            annotation_rows=("severity", "size"),
            categories=("category", lambda x: " | ".join(sorted(set(x)))),
            severities=("severity", lambda x: " | ".join(sorted(set(x)))),
        )
        .reset_index()
    )
    rater_summary.to_csv(
        OUT / "rater_level_annotation_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Report anomalies
    anomalies = segment_summary[
        (segment_summary["unique_raters"] != 3)
        | (segment_summary["unique_sources"] != 1)
        | (segment_summary["unique_targets"] != 1)
    ]
    anomalies.to_csv(
        OUT / "segment_anomalies.csv",
        index=False,
        encoding="utf-8-sig",
    )

    logging.info("Dataset shape: %s", df.shape)
    logging.info("Unique documents: %d", df["doc"].nunique())
    logging.info("Unique doc_id values: %d", df["doc_id"].nunique())
    logging.info("Unique doc-doc_id pairs: %d",
                 len(df[["doc", "doc_id"]].drop_duplicates()))
    logging.info("Unique segment keys: %d", len(segment_summary))
    logging.info("Segment anomalies: %d", len(anomalies))
    logging.info("Exact duplicate rows: %d", int(df.duplicated().sum()))
    logging.info("Outputs saved to %s", OUT)

    print("Data-quality summary completed.")
    print(f"Documents: {df['doc'].nunique()}")
    print(f"Segment keys: {len(segment_summary)}")
    print(f"Anomalous segments: {len(anomalies)}")
    print(f"Outputs: {OUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Data-quality summary failed")
        raise
