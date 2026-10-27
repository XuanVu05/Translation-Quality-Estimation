import pandas as pd
import csv

path = "mqm_newstest2020_ende.tsv"

configs = [
    ("default", {}),
    ("QUOTE_NONE", {"quoting": csv.QUOTE_NONE}),
]

for name, extra in configs:
    print("\n" + "=" * 70)
    print("PARSER:", name)

    df = pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        **extra
    )

    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())

    mask = (
        (df["system"] == "Huoshan_Translate.832") &
        (df["doc"] == "abcnews.363905") &
        (df["seg_id"] == "1129")
    )

    print("Matching rows:", int(mask.sum()))

    cols = ["rater", "source", "target", "category", "severity"]
    print(df.loc[mask, cols].to_string(index=False))
