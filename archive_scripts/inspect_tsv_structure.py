import pandas as pd

df = pd.read_csv(
    "mqm_newstest2020_ende.tsv",
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3,
    on_bad_lines="warn"
)

print("Columns:", list(df.columns))
print("Rows:", len(df))

for i, row in df.head(5).iterrows():
    print(f"\nRow {i + 1}")
    for col in ["system", "doc", "doc_id", "seg_id", "rater",
                "category", "severity", "source", "target"]:
        if col in df.columns:
            value = row[col]
            if col in ["source", "target"]:
                print(f"  {col}: length={len(value)}, has_v_tag={'<v>' in value}")
            else:
                print(f"  {col}: {value}")
