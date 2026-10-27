from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

HUMAN = {"Human-A.0", "Human-B.0", "Human-P.0"}
KEYS = ["system", "doc", "doc_id", "seg_id"]

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")
df = df[~df["system"].isin(HUMAN)].copy()

def normalize_target(value):
    if pd.isna(value):
        return ""
    # Remove only the annotation markup, preserving its text.
    value = re.sub(r"</?v>", "", str(value))
    return re.sub(r"\s+", " ", value).strip()

df["target_normalized"] = df["target"].map(normalize_target)

counts = (
    df.groupby(KEYS, dropna=False)["target_normalized"]
    .nunique()
    .reset_index(name="normalized_target_values")
)

multi = counts[counts["normalized_target_values"] > 1].copy()

# Select a small sample with different variant counts.
sample = pd.concat([
    multi[multi["normalized_target_values"] == 2].head(5),
    multi[multi["normalized_target_values"] == 3].head(3),
    multi[multi["normalized_target_values"] >= 4].head(2),
]).drop_duplicates(KEYS)

rows = df.merge(sample[KEYS], on=KEYS, how="inner")

details = (
    rows.groupby(KEYS, dropna=False)
    .agg(
        source=("source", "first"),
        target_variants=(
            "target_normalized",
            lambda x: " ||| ".join(pd.unique(x))
        ),
        raw_target_count=("target", "nunique"),
        normalized_target_count=("target_normalized", "nunique"),
        raters=("rater", lambda x: ", ".join(sorted(set(map(str, x))))),
    )
    .reset_index()
)

path = OUT / "remaining_target_variant_manual_check.tsv"
details.to_csv(path, sep="\t", index=False, encoding="utf-8-sig")

print("Sample segments:", len(details))
print("Saved:", path)
print(details[
    ["system", "doc", "doc_id", "seg_id",
     "normalized_target_count", "target_variants"]
].to_string(index=False, max_colwidth=500))
