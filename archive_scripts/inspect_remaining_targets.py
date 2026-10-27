
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

def normalize_target(text):
    if pd.isna(text):
        return ""
    # Only remove MQM span markers; preserve all other text
    return re.sub(r"</?v>", "", str(text))

df["target_normalized"] = df["target"].map(normalize_target)

keys = ["system", "doc", "doc_id", "seg_id"]

stats = (
    df.groupby(keys, dropna=False)
    .agg(
        normalized_variants=("target_normalized", "nunique"),
        raters=("rater", "nunique"),
    )
    .reset_index()
)

remaining = (
    stats[stats["normalized_variants"] > 1]
    .sort_values(keys)
    .head(20)
)

examples = df.merge(remaining[keys], on=keys, how="inner")

columns = keys + [
    "rater", "category", "severity", "target", "target_normalized"
]

examples[columns].to_csv(
    OUT / "remaining_target_examples.tsv",
    sep="\t",
    index=False,
    encoding="utf-8-sig",
)

print("So segment can xem:", len(remaining))
print("So dong annotation duoc trich:", len(examples))
print("File ket qua:", OUT / "remaining_target_examples.tsv")

# Luu mot bang tom tat cac bien the de so sanh
variant_summary = (
    examples.groupby(keys, dropna=False)
    .agg(
        raters=("rater", "nunique"),
        annotation_rows=("rater", "size"),
        normalized_variants=("target_normalized", "nunique"),
    )
    .reset_index()
)

variant_summary.to_csv(
    OUT / "remaining_target_summary.csv",
    index=False,
    encoding="utf-8-sig",
)
