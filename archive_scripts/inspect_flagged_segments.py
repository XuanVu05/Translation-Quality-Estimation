import pandas as pd

path = "mqm_newstest2020_ende.tsv"
df = pd.read_csv(
    path, sep="\t", dtype=str, keep_default_na=False,
    quoting=3, on_bad_lines="warn"
)

required = {"system", "doc_id", "seg_id", "rater", "target"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Thieu cot: {sorted(missing)}")

cases = [("4", "204"), ("3", "660")]

for doc_id, seg_id in cases:
    rows = df[
        (df["doc_id"] == doc_id) &
        (df["seg_id"] == seg_id) &
        (~df["system"].str.startswith("Human-"))
    ]

    print(f"\n=== doc_id={doc_id}, seg_id={seg_id} ===")
    print("So dong:", len(rows))

    for _, row in rows.drop_duplicates(["system", "target"]).iterrows():
        target = " ".join(row["target"].split())
        preview = target[:180] + ("..." if len(target) > 180 else "")
        print(f'{row["system"]} | rater={row["rater"]} | {preview}')
