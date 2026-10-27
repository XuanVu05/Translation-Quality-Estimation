from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

human = {"Human-A.0", "Human-B.0", "Human-P.0"}
df = df[~df["system"].isin(human)].copy()

df["target_clean"] = (
    df["target"].fillna("").astype(str)
    .map(lambda x: re.sub(r"</?v>", "", x))
)

keys = ["system", "doc", "doc_id", "seg_id"]

stats = (
    df.groupby(keys, dropna=False)["target_clean"]
    .nunique()
    .reset_index(name="target_variants")
)

sample_keys = (
    stats[stats["target_variants"] > 1]
    .sort_values(keys)
    .head(10)[keys]
)

sample = df.merge(sample_keys, on=keys, how="inner")

sample = sample[
    keys + ["rater", "category", "severity", "target_clean"]
]

path = OUT / "mt_target_variant_annotation_details.tsv"
sample.to_csv(path, sep="\t", index=False, encoding="utf-8-sig")

print("So dong annotation:", len(sample))
print("Da luu:", path)
print("\nThong ke so segment duoc kiem tra:")
print(sample[keys].drop_duplicates().shape[0])
