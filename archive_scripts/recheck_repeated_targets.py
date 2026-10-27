import pandas as pd
import re
from pathlib import Path

src = Path("mqm_newstest2020_ende.tsv")
out = Path("results/week10/data_quality/repeated_target_candidates.tsv")

df = pd.read_csv(
    src, sep="\t", dtype=str, keep_default_na=False,
    quoting=3, on_bad_lines="warn"
)

# Chỉ giữ 7 hệ thống MT, loại các hệ thống người dịch
df = df[~df["system"].str.startswith("Human-")].copy()

# Xóa thẻ, giữ nguyên nội dung bên trong
df["target_clean"] = df["target"].str.replace(
    r"</?v>", "", regex=True
)
df["target_clean"] = df["target_clean"].str.replace(
    r"\s+", " ", regex=True
).str.strip()

# Mỗi hệ thống và segment chỉ giữ các target khác nhau
unique = df[
    ["system", "doc_id", "seg_id", "target_clean"]
].drop_duplicates()

def repeated_prefix(text):
    words = text.split()
    for n in range(min(12, len(words) // 2), 2, -1):
        a = " ".join(words[:n])
        b = " ".join(words[n:2*n])
        if a.casefold() == b.casefold():
            return a
    # Phát hiện lặp dính liền, không có khoảng trắng
    m = re.match(r"^(.{10,100}?)\1", text, flags=re.IGNORECASE)
    return m.group(1) if m else ""

unique["repeat_match"] = unique["target_clean"].map(repeated_prefix)
hits = unique[unique["repeat_match"] != ""].copy()

hits.to_csv(out, sep="\t", index=False, encoding="utf-8")

print("So target duy nhat cua cac he thong MT:", len(unique))
print("So target co dau hieu lap:", len(hits))
print("So segment MT duy nhat:",
      hits[["system", "doc_id", "seg_id"]].drop_duplicates().shape[0])
print("So segment nguon doc_id/seg_id:",
      hits[["doc_id", "seg_id"]].drop_duplicates().shape[0])
print("Da luu:", out)
