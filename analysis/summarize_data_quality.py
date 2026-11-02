
from pathlib import Path
import logging
import json

import pandas as pd


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "mqm_newstest2020_ende.tsv"

OUT = ROOT / "results" / "week10" / "data_quality"
LOG = ROOT / "results" / "week10" / "logs"

OUT.mkdir(parents=True, exist_ok=True)
LOG.mkdir(parents=True, exist_ok=True)


# Seven MT systems used in the model dataset.
MT_SYSTEMS = {
    "eTranslation.737",
    "Huoshan_Translate.832",
    "Online-A.1574",
    "Online-B.1590",
    "OPPO.1535",
    "Tencent_Translation.1520",
    "Tohoku-AIP-NTT.890",
}

# Segment identification key.
KEYS = ["system", "doc", "doc_id", "seg_id"]

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
# 2. LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG / "data_quality_summary.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def save_csv(df, filename):
    """Save a DataFrame as UTF-8 CSV."""
    path = OUT / filename

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )

    return path


def count_unique_segments(df, group_column):
    """
    Count unique segment keys within each group.

    Segment identity:
    system + doc + doc_id + seg_id
    """
    result = (
        df[KEYS]
        .drop_duplicates()
        .groupby(group_column)
        .size()
        .rename("segment_keys")
        .reset_index()
    )

    return result


def make_distribution(series, column_name):
    """Create a frequency distribution."""
    return (
        series.value_counts(dropna=False)
        .sort_index()
        .rename_axis(column_name)
        .reset_index(name="segment_count")
    )


# ============================================================
# 4. LOAD RAW MQM DATA
# ============================================================

def load_data():

    if not DATA.exists():
        raise FileNotFoundError(
            f"Cannot find MQM dataset: {DATA}"
        )

    df = pd.read_csv(
        DATA,
        sep="\t",
        encoding="utf-8",
        dtype=str,
        keep_default_na=False,
    )

    missing_columns = (
        set(REQUIRED_COLUMNS) - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing_columns)}"
        )

    return df


# ============================================================
# 5. MISSINGNESS AUDIT
# ============================================================

def audit_missingness(df):

    # Empty strings and whitespace-only strings are treated
    # as missing for audit purposes.
    missing_mask = df.apply(
        lambda col: col.str.strip().eq("")
    )

    missingness = pd.DataFrame({
        "column": df.columns,
        "missing_count": [
            int(missing_mask[col].sum())
            for col in df.columns
        ],
        "missing_rate": [
            float(missing_mask[col].mean())
            for col in df.columns
        ],
    })

    save_csv(
        missingness,
        "missingness_by_column.csv",
    )

    # Rows with missing segment identification keys.
    missing_key_mask = missing_mask[KEYS].any(axis=1)

    missing_key_rows = df.loc[
        missing_key_mask
    ].copy()

    save_csv(
        missing_key_rows,
        "rows_with_missing_keys.csv",
    )

    # Rows with missing values in any required field.
    missing_required_mask = missing_mask[
        REQUIRED_COLUMNS
    ].any(axis=1)

    missing_required_rows = df.loc[
        missing_required_mask
    ].copy()

    save_csv(
        missing_required_rows,
        "rows_with_missing_required_values.csv",
    )

    return missing_mask, missing_key_rows, missing_required_rows


# ============================================================
# 6. DUPLICATE AUDIT
# ============================================================

def audit_duplicates(df):

    # Exact duplicate rows across all columns.
    duplicate_mask = df.duplicated(
        keep=False
    )

    exact_duplicates = df.loc[
        duplicate_mask
    ].copy()

    save_csv(
        exact_duplicates,
        "exact_duplicate_rows.csv",
    )

    # Count exact duplicate rows.
    exact_duplicate_count = int(
        df.duplicated().sum()
    )

    # Report repeated segment-rater combinations.
    # These are NOT automatically treated as errors:
    # one rater may legitimately assign multiple annotations
    # to the same segment.
    valid = df.loc[
        ~df[KEYS].apply(
            lambda col: col.str.strip().eq("")
        ).any(axis=1)
    ].copy()

    rater_keys = KEYS + ["rater"]

    rater_annotation_counts = (
        valid.groupby(rater_keys, dropna=False)
        .size()
        .reset_index(name="annotation_rows")
    )

    multiple_annotation_rows = (
        rater_annotation_counts[
            rater_annotation_counts["annotation_rows"] > 1
        ]
    )

    save_csv(
        multiple_annotation_rows,
        "multiple_annotations_per_rater_segment.csv",
    )

    return exact_duplicate_count, multiple_annotation_rows


# ============================================================
# 7. DOCUMENT-LEVEL SUMMARY
# ============================================================

def summarize_documents(valid):

    doc_summary = (
        valid.groupby("doc")
        .agg(
            unique_doc_ids=("doc_id", "nunique"),
            unique_segments=("seg_id", "nunique"),
            unique_systems=("system", "nunique"),
            annotation_rows=("rater", "size"),
        )
        .reset_index()
    )

    save_csv(
        doc_summary,
        "document_level_summary.csv",
    )

    return doc_summary


# ============================================================
# 8. SEGMENT-LEVEL SUMMARY
# ============================================================

def summarize_segments(valid):

    segment_summary = (
        valid.groupby(KEYS, dropna=False)
        .agg(
            annotation_rows=("rater", "size"),
            unique_raters=("rater", "nunique"),
            unique_sources=("source", "nunique"),
            unique_targets=("target", "nunique"),
        )
        .reset_index()
    )

    save_csv(
        segment_summary,
        "segment_level_summary.csv",
    )

    return segment_summary


# ============================================================
# 9. RATER-LEVEL SUMMARY
# ============================================================

def summarize_raters(valid):

    rater_keys = KEYS + ["rater"]

    rater_summary = (
        valid.groupby(rater_keys, dropna=False)
        .agg(
            annotation_rows=("severity", "size"),
            categories=(
                "category",
                lambda x: " | ".join(
                    sorted(set(x))
                ),
            ),
            severities=(
                "severity",
                lambda x: " | ".join(
                    sorted(set(x))
                ),
            ),
        )
        .reset_index()
    )

    save_csv(
        rater_summary,
        "rater_level_annotation_summary.csv",
    )

    return rater_summary


# ============================================================
# 10. SEGMENT ANOMALY AUDIT
# ============================================================

def audit_segment_anomalies(segment_summary):

    # A segment is flagged when:
    # 1. It does not have exactly three distinct raters.
    # 2. It has more than one source variant.
    #
    # Multiple target variants are reported separately.
    # They are NOT automatically classified as data errors.

    anomalies = segment_summary[
        (
            segment_summary["unique_raters"] != 3
        )
        | (
            segment_summary["unique_sources"] != 1
        )
    ].copy()

    save_csv(
        anomalies,
        "segment_anomalies.csv",
    )

    # Target variants for manual inspection.
    target_variants = segment_summary[
        segment_summary["unique_targets"] > 1
    ].copy()

    save_csv(
        target_variants,
        "target_variants_for_inspection.csv",
    )

    return anomalies, target_variants


# ============================================================
# 11. ANNOTATION AND RATER DISTRIBUTIONS
# ============================================================

def summarize_distributions(segment_summary):

    columns = [
        "annotation_rows",
        "unique_raters",
        "unique_sources",
        "unique_targets",
    ]

    for column in columns:

        distribution = make_distribution(
            segment_summary[column],
            column,
        )

        save_csv(
            distribution,
            f"{column}_distribution.csv",
        )


def summarize_rater_coverage(valid):

    # Count distinct raters for every segment.
    segment_raters = (
        valid.groupby(KEYS, dropna=False)["rater"]
        .nunique()
        .reset_index(name="unique_raters")
    )

    # Distribution of number of raters by system.
    rater_coverage = (
        segment_raters.groupby("system")["unique_raters"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )

    rater_coverage.columns = [
        (
            f"raters_{col}"
            if isinstance(col, int)
            else col
        )
        for col in rater_coverage.columns
    ]

    save_csv(
        rater_coverage,
        "rater_coverage_by_system.csv",
    )

    # Overall distribution.
    overall = (
        segment_raters["unique_raters"]
        .value_counts()
        .sort_index()
        .rename_axis("unique_raters")
        .reset_index(name="segment_count")
    )

    save_csv(
        overall,
        "rater_coverage_overall.csv",
    )

    return segment_raters, rater_coverage, overall


# ============================================================
# 12. SYSTEM COVERAGE AUDIT
# ============================================================

def summarize_systems(valid):

    # Count annotation rows and documents.
    system_summary = (
        valid.groupby("system")
        .agg(
            annotation_rows=("rater", "size"),
            documents=("doc", "nunique"),
        )
        .reset_index()
    )

    # Count unique segment keys per system.
    unique_segments = count_unique_segments(
        valid,
        "system",
    )

    system_summary = system_summary.merge(
        unique_segments,
        on="system",
        how="left",
        validate="one_to_one",
    )

    system_summary["system_type"] = (
        system_summary["system"].apply(
            lambda x: (
                "MT"
                if x in MT_SYSTEMS
                else "Other/Human"
            )
        )
    )

    system_summary = system_summary[
        [
            "system",
            "system_type",
            "annotation_rows",
            "documents",
            "segment_keys",
        ]
    ]

    save_csv(
        system_summary,
        "system_coverage_summary.csv",
    )

    # Separate MT systems from other systems.
    mt_system_summary = system_summary[
        system_summary["system_type"] == "MT"
    ].copy()

    save_csv(
        mt_system_summary,
        "mt_system_coverage_summary.csv",
    )

    # Model-scope dataset: seven MT systems only.
    mt = valid[
        valid["system"].isin(MT_SYSTEMS)
    ].copy()

    mt_segment_summary = (
        mt.groupby(KEYS, dropna=False)
        .agg(
            annotation_rows=("rater", "size"),
            unique_raters=("rater", "nunique"),
            unique_sources=("source", "nunique"),
            unique_targets=("target", "nunique"),
        )
        .reset_index()
    )

    save_csv(
        mt_segment_summary,
        "mt_segment_level_summary.csv",
    )

    return system_summary, mt, mt_segment_summary


# ============================================================
# 13. SOURCE AND TARGET CONSISTENCY
# ============================================================

def summarize_text_variants(segment_summary):

    source_variants = segment_summary[
        segment_summary["unique_sources"] > 1
    ].copy()

    target_variants = segment_summary[
        segment_summary["unique_targets"] > 1
    ].copy()

    save_csv(
        source_variants,
        "source_variants_by_segment.csv",
    )

    save_csv(
        target_variants,
        "target_variants_for_inspection.csv",
    )

    return source_variants, target_variants


# ============================================================
# 14. OVERALL DATA QUALITY SUMMARY
# ============================================================

def create_overview(
    df,
    valid,
    segment_summary,
    mt,
    mt_segment_summary,
    missing_key_rows,
    missing_required_rows,
    exact_duplicate_count,
    anomalies,
    target_variants,
    source_variants,
    rater_summary,
):

    summary = {
        "raw_annotation_rows": int(len(df)),

        "rows_with_valid_segment_keys": int(len(valid)),

        "raw_systems": int(valid["system"].nunique()),

        "raw_documents": int(valid["doc"].nunique()),

        "raw_segment_keys": int(len(segment_summary)),

        "mt_systems": int(mt["system"].nunique()),

        "mt_annotation_rows": int(len(mt)),

        "mt_segment_keys": int(len(mt_segment_summary)),

        "missing_segment_key_rows": int(
            len(missing_key_rows)
        ),

        "missing_required_value_rows": int(
            len(missing_required_rows)
        ),

        "exact_duplicate_rows": int(
            exact_duplicate_count
        ),

        "segments_not_three_raters": int(
            (segment_summary["unique_raters"] != 3).sum()
        ),

        "segments_with_multiple_sources": int(
            len(source_variants)
        ),

        "segments_with_multiple_targets": int(
            len(target_variants)
        ),

        "segments_flagged_as_anomalies": int(
            len(anomalies)
        ),

        "rater_segment_groups": int(
            len(rater_summary)
        ),
    }

    overview = pd.DataFrame([
        {
            "metric": key,
            "value": value,
        }
        for key, value in summary.items()
    ])

    save_csv(
        overview,
        "data_quality_overview.csv",
    )

    # Save machine-readable JSON summary.
    with open(
        OUT / "data_quality_overview.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            summary,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return summary


# ============================================================
# 15. MAIN
# ============================================================

def main():

    print("=" * 65)
    print("WMT 2020 MQM DATA QUALITY AUDIT")
    print("=" * 65)

    # Load raw dataset.
    df = load_data()

    print(f"Raw annotation rows: {len(df):,}")

    # Missingness.
    (
        missing_mask,
        missing_key_rows,
        missing_required_rows,
    ) = audit_missingness(df)

    # Valid segment keys.
    valid = df.loc[
        ~missing_mask[KEYS].any(axis=1)
    ].copy()

    # Duplicates.
    (
        exact_duplicate_count,
        multiple_annotation_rows,
    ) = audit_duplicates(df)

    # Document summary.
    doc_summary = summarize_documents(valid)

    # Segment summary.
    segment_summary = summarize_segments(valid)

    # Rater summary.
    rater_summary = summarize_raters(valid)

    # Anomalies and variants.
    (
        anomalies,
        target_variants,
    ) = audit_segment_anomalies(segment_summary)

    source_variants, target_variants = (
        summarize_text_variants(segment_summary)
    )

    # Distributions.
    summarize_distributions(segment_summary)

    (
        segment_raters,
        rater_coverage,
        overall_rater_coverage,
    ) = summarize_rater_coverage(valid)

    # System coverage and model scope.
    (
        system_summary,
        mt,
        mt_segment_summary,
    ) = summarize_systems(valid)

    # Overall summary.
    summary = create_overview(
        df=df,
        valid=valid,
        segment_summary=segment_summary,
        mt=mt,
        mt_segment_summary=mt_segment_summary,
        missing_key_rows=missing_key_rows,
        missing_required_rows=missing_required_rows,
        exact_duplicate_count=exact_duplicate_count,
        anomalies=anomalies,
        target_variants=target_variants,
        source_variants=source_variants,
        rater_summary=rater_summary,
    )

    # Log summary.
    logging.info("Dataset shape: %s", df.shape)
    logging.info("Data quality overview: %s", summary)

    logging.info(
        "Exact duplicate rows: %d",
        exact_duplicate_count,
    )

    logging.info(
        "Multiple annotation rows per rater-segment groups: %d",
        len(multiple_annotation_rows),
    )

    logging.info(
        "Outputs saved to: %s",
        OUT,
    )

    # Print results.
    print("\n=== DATA QUALITY OVERVIEW ===")

    for key, value in summary.items():
        print(f"{key}: {value:,}")

    print("\n=== RATER COVERAGE ===")
    print(
        overall_rater_coverage.to_string(index=False)
    )

    print("\n=== SYSTEM COVERAGE ===")
    print(
        system_summary.to_string(index=False)
    )

    print("\n=== MODEL SCOPE ===")
    print(
        f"MT systems: {mt['system'].nunique()}"
    )

    print(
        f"MT annotation rows: {len(mt):,}"
    )

    print(
        f"MT segment keys: {len(mt_segment_summary):,}"
    )

    print("\n=== OUTPUT DIRECTORY ===")
    print(OUT)

    print("\nData quality audit completed.")


if __name__ == "__main__":

    try:
        main()

    except Exception:

        logging.exception(
            "Data quality summary failed"
        )

        raise
