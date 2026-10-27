import csv
import re
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

KEYS = ["system", "doc", "doc_id", "seg_id"]
HUMAN = {"Human-A.0", "Human-B.0", "Human-P.0"}

df = pd.read_csv(
    DATA,
    sep="\t",
    encoding="utf-8",
    quoting=csv.QUOTE_NONE,
    dtype=str,
    keep_default_na=False,
)

df = df[~df["system"].isin(HUMAN)].copy()

def normalize_target(value):
    # Remove MQM span markers, preserving their text.
    value = re.sub(r"</?v>", "", value)
    return value.strip()

df["target_normalized"] = df["target"].map(normalize_target)

summary = (
    df.groupby(KEYS, dropna=False)
      .agg(
          annotation_rows=("target", "size"),
          raw_target_variants=("target", "nunique"),
          normalized_target_variants=("target_normalized", "nunique"),
          has_no_error=("category", lambda s: s.eq("No-error").any()),
          no_error_target_variants=(
              "target_normalized",
              lambda s: s.nunique()
          ),
      )
      .reset_index()
)

# Count normalized target variants among No-error rows separately.
no_error = df[df["category"].eq("No-error")]
no_error_counts = (
    no_error.groupby(KEYS, dropna=False)["target_normalized"]
            .nunique()
            .rename("no_error_target_variants")
            .reset_index()
)

summary = summary.drop(columns=["no_error_target_variants"]).merge(
    no_error_counts, on=KEYS, how="left"
)
summary["no_error_target_variants"] = (
    summary["no_error_target_variants"].fillna(0).astype(int)
)

summary["normalization_status"] = summary[
    "normalized_target_variants"
].map(lambda n: "one_normalized_target" if n == 1 else "multiple_normalized_targets")

summary["no_error_status"] = summary["no_error_target_variants"].map(
    lambda n: "one_no_error_target" if n == 1
    else ("multiple_no_error_targets" if n > 1 else "no_no_error_target")
)

path = OUT / "target_normalization_audit_v2.csv"
summary.to_csv(path, index=False, encoding="utf-8-sig")

print("MT segments:", len(summary))
print("\nNormalized target variants:")
print(summary["normalization_status"].value_counts().to_string())
print("\nNo-error target availability:")
print(summary["no_error_status"].value_counts().to_string())
print("\nSegments with one normalized target and one No-error target:",
      int(((summary["normalized_target_variants"] == 1) &
           (summary["no_error_target_variants"] == 1)).sum()))
print("\nSaved:", path)
