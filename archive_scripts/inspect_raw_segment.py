import csv
import pandas as pd

path = "mqm_newstest2020_ende.tsv"

doc = "abcnews.363905"
system = "Huoshan_Translate.832"
seg_id = 1129

df = pd.read_csv(
    path,
    sep="\t",
    quoting=csv.QUOTE_NONE,
    dtype=str,
    keep_default_na=False
)

print("Columns:", df.columns.tolist())
print("Rows:", len(df))

mask = (
    (df["system"] == system) &
    (df["doc"] == doc) &
    (df["seg_id"] == str(seg_id))
)

cols = [
    c for c in [
        "system", "doc", "doc_id", "seg_id", "rater",
        "source", "target", "category", "severity"
    ]
    if c in df.columns
]

print("\nMatching annotation rows:", int(mask.sum()))
print(df.loc[mask, cols].to_string(index=False))
