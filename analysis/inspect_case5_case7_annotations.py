
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"

cases = [
    (1, "Online-B.1590", "abcnews.363994", 5, 1317),
    (2, "eTranslation.737", "standard.co.uk.14516", 1, 1386),
    (3, "Huoshan_Translate.832", "standard.co.uk.14516", 2, 1387),
    (4, "Tohoku-AIP-NTT.890", "reuters.276702", 4, 538),
    (5, "eTranslation.737", "cnn.385556", 17, 1182),
    (6, "Online-B.1590", "latimes.431856", 7, 293),
    (7, "eTranslation.737", "brisbanetimes.com.au.225989", 8, 1066),
    (8, "Tencent_Translation.1520", "telegraph.421295", 8, 1360),
    (9, "Huoshan_Translate.832", "express.co.uk.10983", 9, 213),
    (10, "OPPO.1535", "stv.tv.21636", 6, 66),
]

df = pd.read_csv(MQM_PATH, sep="\t")

for case_no, system, doc, doc_id, seg_id in cases:
    subset = df[
        (df["system"] == system)
        & (df["doc"] == doc)
        & (df["doc_id"] == doc_id)
        & (df["seg_id"] == seg_id)
    ].copy()

    print("\n" + "=" * 90)
    print(f"CASE {case_no}: {doc}")
    print(f"System: {system}")
    print(f"Local segment: {doc_id} | Global segment: {seg_id}")
    print("=" * 90)

    if subset.empty:
        print("No MQM annotation found.")
        continue

    print("Annotation rows:", len(subset))
    print("Annotators:", subset["rater"].nunique())

    print("\nRAW ANNOTATIONS:")
    print(
        subset[["rater", "category", "severity"]]
        .sort_values(["rater", "severity", "category"])
        .to_string(index=False)
    )

    subset["is_serious"] = (
        (
            (subset["severity"] == "Major")
            & subset["category"].fillna("").str.startswith("Accuracy/")
        )
        |
        (subset["category"] == "Non-translation!")
    )

    votes = (
        subset.groupby("rater")["is_serious"]
        .any()
        .astype(int)
    )

    print("\nSERIOUS VOTES:")
    print(votes.to_string())
    print("Total serious votes:", int(votes.sum()))
    print("y_primary:", int(votes.sum() >= 2))