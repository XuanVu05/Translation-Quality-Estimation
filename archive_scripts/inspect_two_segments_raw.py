import csv
import pandas as pd

path = "mqm_newstest2020_ende.tsv"

df = pd.read_csv(
    path,
    sep="\t",
    encoding="utf-8",
    quoting=csv.QUOTE_NONE,
    dtype=str,
    keep_default_na=False,
)

cases = [
    ("Huoshan_Translate.832", "aj-english.8643", "204"),
    ("Huoshan_Translate.832", "cbsnews.302258", "300"),
]

for system, doc, seg_id in cases:
    mask = (
        df["system"].eq(system)
        & df["doc"].eq(doc)
        & df["seg_id"].eq(seg_id)
    )

    print("\n" + "=" * 90)
    print(f"SYSTEM={system} | DOC={doc} | SEG_ID={seg_id}")
    print("Rows:", int(mask.sum()))

    cols = ["rater", "source", "target", "category", "severity"]
    print(df.loc[mask, cols].to_string(index=False))
