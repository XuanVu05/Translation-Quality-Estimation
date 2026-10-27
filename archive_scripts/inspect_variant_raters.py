from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "mqm_newstest2020_ende.tsv", sep="\t", encoding="utf-8")

cases = [
    ("Huoshan_Translate.832", "abcnews.364001", 1, 1343),
    ("Huoshan_Translate.832", "aj-english.8643", 4, 204),
    ("Huoshan_Translate.832", "cbsnews.302172", 1, 1363),
]

for system, doc, doc_id, seg_id in cases:
    part = df[
        (df["system"] == system)
        & (df["doc"] == doc)
        & (df["doc_id"] == doc_id)
        & (df["seg_id"] == seg_id)
    ]

    print("\n" + "=" * 90)
    print(f"CASE: {system} | {doc} | doc_id={doc_id} | seg_id={seg_id}")
    print("Rows:", len(part))

    cols = ["rater", "target", "category", "severity"]
    print(part[cols].to_string(index=False, max_colwidth=300))
