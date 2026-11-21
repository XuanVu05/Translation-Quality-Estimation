
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "data_quality_results"

comparison = pd.read_csv(
    OUT / "mqm_vs_original_all_segments.csv"
)

variants = pd.read_csv(
    OUT / "target_variants_by_segment.csv"
)

# Only MT systems.
comparison = comparison[
    ~comparison["system"].str.startswith("Human-")
].copy()

# Compare the two independent audit results.
check = comparison.merge(
    variants[
        [
            "system", "doc", "doc_id", "seg_id",
            "normalized_variants"
        ]
    ],
    on=["system", "doc", "doc_id", "seg_id"],
    how="left",
    validate="one_to_one"
)

print("=" * 65)
print("CONSISTENCY CHECK")
print("=" * 65)

print("MT system-segments:", len(check))
print(
    "Segments with multiple normalized targets:",
    int((check["normalized_variants"] > 1).sum())
)
print(
    "Segments with Some match:",
    int((check["comparison_status"] == "Some match").sum())
)
print(
    "Segments with None match:",
    int((check["comparison_status"] == "None match").sum())
)

print("\nSTATUS CROSS-TABULATION")
print(
    pd.crosstab(
        check["comparison_status"],
        check["normalized_variants"] > 1,
        rownames=["Comparison status"],
        colnames=["Multiple normalized targets"]
    ).to_string()
)

# Inspect all cases with no matching MQM target.
none_match = check[
    check["comparison_status"] == "None match"
].copy()

none_match.to_csv(
    OUT / "inspect_none_match_segments.csv",
    index=False
)

# Inspect a sample of Some match cases.
some_match = check[
    check["comparison_status"] == "Some match"
].head(30)

some_match.to_csv(
    OUT / "inspect_some_match_sample.csv",
    index=False
)

print("\nNONE MATCH CASES:", len(none_match))
print(
    none_match[
        [
            "system", "doc", "doc_id", "seg_id",
            "normalized_variants",
            "original_target", "mqm_targets"
        ]
    ].to_string(index=False)
)

print("\nSaved:")
print(OUT)
