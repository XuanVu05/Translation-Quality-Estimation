import pandas as pd
import re
from pathlib import Path

root = Path(".")
input_file = root / "results/week10/data_quality/mt_target_variant_annotation_details.tsv"
output_file = root / "results/week10/data_quality/possible_repeated_text.tsv"

df = pd.read_csv(input_file, sep="\t", dtype=str).fillna("")

def find_repeated_prefix(text):
    text = re.sub(r"\s+", " ", text).strip()
    # Tìm cụm từ 3–12 từ bị lặp liên tiếp ở đầu câu
    words = text.split()
    for n in range(min(12, len(words) // 2), 2, -1):
        first = " ".join(words[:n])
        next_part = " ".join(words[n:2*n])
        if first.casefold() == next_part.casefold():
            return first
    # Bắt trường hợp lặp dính liền không có khoảng trắng
    match = re.match(r"^(.{10,100}?)\1", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

if "target_clean" not in df.columns:
    raise ValueError("Không tìm thấy cột target_clean trong file đầu vào.")

df["repeated_prefix"] = df["target_clean"].apply(find_repeated_prefix)
hits = df[df["repeated_prefix"] != ""].copy()

columns = [
    c for c in [
        "system", "doc", "doc_id", "seg_id", "rater",
        "category", "severity", "repeated_prefix"
    ] if c in hits.columns
]
hits[columns].to_csv(output_file, sep="\t", index=False, encoding="utf-8")

print("Tong so dong da kiem tra:", len(df))
print("So dong co dau hieu lap cum tu:", len(hits))
print("So segment duy nhat:", hits[["system", "doc_id", "seg_id"]].drop_duplicates().shape[0]
      if len(hits) else 0)
print("Da luu ket qua tai:", output_file)
