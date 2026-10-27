from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "model_data"
OUT.mkdir(parents=True, exist_ok=True)

HUMAN_SYSTEMS = {"Human-A.0", "Human-B.0", "Human-P.0"}
SEGMENT_KEYS = ["system", "doc", "doc_id", "seg_id"]
RATER_KEYS = SEGMENT_KEYS + ["rater"]

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")
df = df[~df["system"].isin(HUMAN_SYSTEMS)].copy()

severity = df["severity"].fillna("").astype(str).str.strip().str.casefold()
category = df["category"].fillna("").astype(str).str.strip()

df["is_serious"] = (
    severity.eq("major")
    & (
        category.str.startswith("Accuracy/", na=False)
        | category.eq("Non-translation!")
    )
).astype(int)

# One vote per segment and rater.
votes = (
    df.groupby(RATER_KEYS, dropna=False)
    .agg(serious_vote=("is_serious", "max"))
    .reset_index()
)

labels = (
    votes.groupby(SEGMENT_KEYS, dropna=False)
    .agg(
        distinct_raters=("rater", "nunique"),
        serious_votes=("serious_vote", "sum"),
    )
    .reset_index()
)

labels["y_primary"] = (labels["serious_votes"] >= 2).astype(int)

# Inspect source/target consistency independently of the labels.
texts = (
    df.groupby(SEGMENT_KEYS, dropna=False)
    .agg(
        source_values=("source", "nunique"),
        target_values=("target", "nunique"),
        source=("source", "first"),
        target=("target", "first"),
    )
    .reset_index()
)

data = labels.merge(texts, on=SEGMENT_KEYS, how="left")

data["text_consistency_issue"] = (
    (data["source_values"] != 1)
    | (data["target_values"] != 1)
    | data["source"].isna()
    | data["target"].isna()
)

issues = data[data["text_consistency_issue"]].copy()
clean = data[~data["text_consistency_issue"]].copy()

data.to_csv(
    OUT / "mt_segment_level_all.csv",
    index=False,
    encoding="utf-8-sig",
)
issues.to_csv(
    OUT / "mt_segment_text_consistency_issues.csv",
    index=False,
    encoding="utf-8-sig",
)
clean.to_csv(
    OUT / "mt_segment_level_consistent_text.csv",
    index=False,
    encoding="utf-8-sig",
)

print("=== Segment-level data preparation ===")
print("All MT segment keys:", len(data))
print("Text consistency issues:", len(issues))
print("Segments with consistent source/target:", len(clean))
print("Positive labels, all segments:", int(data["y_primary"].sum()))
print("Positive rate, all segments:", round(data["y_primary"].mean(), 6))
print("Segments with exactly 3 raters:", int((data["distinct_raters"] == 3).sum()))
print("Segments with other rater counts:", int((data["distinct_raters"] != 3).sum()))
print("Output directory:", OUT)
