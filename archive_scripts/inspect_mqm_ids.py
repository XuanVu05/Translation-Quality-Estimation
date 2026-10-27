import pandas as pd
from pathlib import Path

p = Path(r"D:\Translation Quality Estimation\mqm_newstest2020_ende.tsv")
df = pd.read_csv(p, sep="\t", dtype=str, keep_default_na=False)

print("=== FIRST 20 DISTINCT DOCUMENT/ID COMBINATIONS ===")
pairs = df[["doc", "doc_id", "seg_id"]].drop_duplicates()
print(pairs.head(20).to_string(index=False))

print("\n=== EXAMPLE: abcnews.363905 ===")
example = df[df["doc"] == "abcnews.363905"]
print(example[["doc", "doc_id", "seg_id"]]
      .drop_duplicates()
      .head(20).to_string(index=False))

print("\n=== SEGMENT ID RANGE BY DOCUMENT ===")
summary = (
    pairs.groupby("doc", sort=False)
    .agg(
        doc_id_values=("doc_id", lambda x: ", ".join(pd.unique(x)[:5])),
        unique_seg_ids=("seg_id", "nunique"),
        min_seg_id=("seg_id", lambda x: min(map(int, x))),
        max_seg_id=("seg_id", lambda x: max(map(int, x))),
    )
    .reset_index()
)
print(summary.head(20).to_string(index=False))

print("\n=== CHECK WHETHER doc_id IS CONSTANT WITHIN EACH doc ===")
counts = pairs.groupby("doc")["doc_id"].nunique()
print("Documents with exactly one doc_id:", int((counts == 1).sum()))
print("Documents with multiple doc_id values:", int((counts > 1).sum()))
print("Examples with multiple doc_id values:")
print(counts[counts > 1].head(10).to_string())
