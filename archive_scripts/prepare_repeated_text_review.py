import pandas as pd
from pathlib import Path

src = Path("results/week10/data_quality/repeated_target_candidates.tsv")
out = Path("results/week10/data_quality/repeated_target_manual_review.tsv")

df = pd.read_csv(src, sep="\t", dtype=str, keep_default_na=False)

# Ưu tiên các segment có nhiều hệ thống MT bị gắn cờ
counts = (
    df.groupby(["doc_id", "seg_id"])["system"]
      .nunique()
      .rename("system_count")
      .reset_index()
)

top = counts.sort_values(
    ["system_count", "doc_id", "seg_id"],
    ascending=[False, True, True]
).head(10)

sample = df.merge(top, on=["doc_id", "seg_id"], how="inner")
sample["target_preview"] = sample["target_clean"].str.slice(0, 220)

sample = sample[
    ["doc_id", "seg_id", "system_count", "system",
     "repeat_match", "target_preview"]
].sort_values(
    ["system_count", "doc_id", "seg_id", "system"],
    ascending=[False, True, True, True]
)

sample.to_csv(out, sep="\t", index=False, encoding="utf-8")

print("So dong trong mau:", len(sample))
print("So segment nguon:", sample[["doc_id", "seg_id"]].drop_duplicates().shape[0])
print("Da luu:", out)
