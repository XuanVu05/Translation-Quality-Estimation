from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

# Retain the seven MT systems; exclude human translations.
human = {"Human-A.0", "Human-B.0", "Human-P.0"}
df = df[~df["system"].isin(human)].copy()

segment_keys = ["system", "doc", "doc_id", "seg_id"]
rater_keys = segment_keys + ["rater"]

severity = df["severity"].fillna("").astype(str).str.strip().str.casefold()
category = df["category"].fillna("").astype(str).str.strip()

# Primary rule: Major severity AND Accuracy/* or Non-translation!
is_serious = (
    severity.eq("major")
    & (
        category.str.startswith("Accuracy/", na=False)
        | category.eq("Non-translation!")
    )
)

df["is_serious"] = is_serious.astype(int)
df["is_major_any_category"] = severity.eq("major").astype(int)
df["is_minor"] = severity.eq("minor").astype(int)

# One vote per segment and rater, regardless of annotation-row count.
rater_votes = (
    df.groupby(rater_keys, dropna=False)
    .agg(
        has_serious=("is_serious", "max"),
        has_major_any_category=("is_major_any_category", "max"),
        has_minor=("is_minor", "max"),
        annotation_rows=("severity", "size"),
    )
    .reset_index()
)

# Count votes at the segment level.
segment_votes = (
    rater_votes.groupby(segment_keys, dropna=False)
    .agg(
        distinct_raters=("rater", "nunique"),
        serious_votes=("has_serious", "sum"),
        major_votes_any_category=("has_major_any_category", "sum"),
        minor_votes=("has_minor", "sum"),
    )
    .reset_index()
)

# Primary binary label: at least 2 raters vote for a serious error.
segment_votes["y_primary"] = (
    segment_votes["serious_votes"] >= 2
).astype(int)

distribution = (
    segment_votes["serious_votes"]
    .value_counts()
    .sort_index()
    .rename_axis("serious_votes")
    .reset_index(name="segment_count")
)

label_distribution = (
    segment_votes["y_primary"]
    .value_counts()
    .sort_index()
    .rename_axis("y_primary")
    .reset_index(name="segment_count")
)

rater_votes.to_csv(
    OUT / "mt_rater_level_votes_diagnostic_corrected.csv",
    index=False,
    encoding="utf-8-sig",
)
segment_votes.to_csv(
    OUT / "mt_segment_serious_vote_diagnostic_corrected.csv",
    index=False,
    encoding="utf-8-sig",
)
distribution.to_csv(
    OUT / "mt_serious_vote_distribution_corrected.csv",
    index=False,
    encoding="utf-8-sig",
)
label_distribution.to_csv(
    OUT / "mt_primary_label_distribution_corrected.csv",
    index=False,
    encoding="utf-8-sig",
)

print("=== Serious votes per MT segment ===")
print(distribution.to_string(index=False))
print("\n=== Primary binary label (serious_votes >= 2) ===")
print(label_distribution.to_string(index=False))
print("\nMT segments:", len(segment_votes))
print("Segments with exactly 3 raters:",
      int(segment_votes["distinct_raters"].eq(3).sum()))
print("Segments with other rater counts:",
      int(segment_votes["distinct_raters"].ne(3).sum()))
print("Positive samples:", int(segment_votes["y_primary"].sum()))
print("Positive rate:",
      round(float(segment_votes["y_primary"].mean()), 6))
print("\nSaved corrected diagnostics to:", OUT)
