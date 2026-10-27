import csv
import re
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

KEYS = ["system", "doc", "doc_id", "seg_id"]
HUMAN = {"Human-A.0", "Human-B.0", "Human-P.0"}

df = pd.read_csv(
    DATA, sep="\t", encoding="utf-8",
    quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False
)
df = df[~df["system"].isin(HUMAN)].copy()
df["target_normalized"] = df["target"].map(
    lambda s: re.sub(r"</?v>", "", s).strip()
)

# Chọn các segment có nhiều target sau chuẩn hóa.
counts = (
    df.groupby(KEYS, dropna=False)["target_normalized"]
      .nunique()
      .rename("n_targets")
      .reset_index()
)
problem_keys = counts[counts["n_targets"] > 1][KEYS]

sample_keys = problem_keys.head(30)
sample = df.merge(sample_keys, on=KEYS, how="inner")

cols = KEYS + ["rater", "category", "severity", "target_normalized"]
sample[cols].to_csv(
    OUT / "multiple_normalized_target_sample30.csv",
    index=False, encoding="utf-8-sig"
)

print("Segments with multiple normalized targets:", len(problem_keys))
print("Segments sampled:", len(sample_keys))
print("Annotation rows saved:", len(sample))
print("Output:", OUT / "multiple_normalized_target_sample30.csv")
print("\nFirst 15 annotation rows:")
print(sample[cols].head(15).to_string(index=False))
