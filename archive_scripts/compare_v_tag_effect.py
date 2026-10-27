import pandas as pd
import re

df = pd.read_csv(
    "mqm_newstest2020_ende.tsv",
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3,
    on_bad_lines="warn"
)

cases = [("4", "204"), ("3", "660")]

for doc_id, seg_id in cases:
    rows = df[
        (df["doc_id"] == doc_id) &
        (df["seg_id"] == seg_id) &
        (~df["system"].str.startswith("Human-"))
    ].drop_duplicates(["system", "rater", "target"])

    print(f"\n=== doc_id={doc_id}, seg_id={seg_id} ===")

    shown = set()
    for _, row in rows.iterrows():
        key = (row["system"], row["rater"])
        if key in shown:
            continue
        shown.add(key)

        raw = row["target"]
        tags_removed = re.sub(r"</?v>", "", raw)
        spans_removed = re.sub(r"<v>.*?</v>", "", raw)

        def preview(text):
            text = re.sub(r"\s+", " ", text).strip()
            return text[:160] + ("..." if len(text) > 160 else "")

        print(f"\n{row['system']} | {row['rater']}")
        print("RAW:          ", preview(raw))
        print("TAGS REMOVED: ", preview(tags_removed))
        print("SPANS REMOVED:", preview(spans_removed))
