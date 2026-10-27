import pandas as pd
import re
from pathlib import Path

src = Path("mqm_newstest2020_ende.tsv")
out = Path("results/week10/data_quality/possible_repeated_text_full.tsv")

df = pd.read_csv(src, sep="\t", dtype=str, keep_default_na=False,
                 quoting=3, on_bad_lines="warn")

def repeated_prefix(text):
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()

    for n in range(min(12, len(words) // 2), 2, -1):
        a = " ".join(words[:n])
        b = " ".join(words[n:2*n])
        if a.casefold() == b.casefold():
            return a

    # Phát hiện cụm từ bị lặp dính liền ở đầu câu
    m = re.match(r"^(.{10,100}?)\1", text, flags=re.IGNORECASE)
    return m.group(1) if m else ""

if "target" not in df.columns:
    raise ValueError("Không tìm thấy cột target trong TSV.")

df["repeat_match"] = df["target"].map(repeated_prefix)
hits = df[df["repeat_match"] != ""].copy()

cols = [c for c in [
    "system", "doc", "doc_id", "seg_id", "rater",
    "category", "severity", "repeat_match"
] if c in hits.columns]

hits[cols].to_csv(out, sep="\t", index=False, encoding="utf-8")

print("Tong so dong doc duoc:", len(df))
print("So dong co dau hieu lap:", len(hits))
if {"system", "doc_id", "seg_id"}.issubset(hits.columns):
    print("So segment duy nhat co dau hieu lap:",
          hits[["system", "doc_id", "seg_id"]].drop_duplicates().shape[0])
print("File ket qua:", out)
