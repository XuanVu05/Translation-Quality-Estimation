
from pathlib import Path
import pandas as pd

data_path = Path("mqm_newstest2020_ende.tsv")

if not data_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {data_path.resolve()}")

df = pd.read_csv(data_path, sep="\t", encoding="utf-8")

print("=" * 60)
print("FILE:", data_path.resolve())
print("KÍCH THƯỚC:", df.shape)
print("SỐ DÒNG:", len(df))
print("SỐ CỘT:", len(df.columns))

print("\nTÊN CÁC CỘT:")
for col in df.columns:
    print("-", repr(col))

print("\n5 DÒNG ĐẦU:")
print(df.head().to_string(index=False))

print("\nSỐ GIÁ TRỊ THIẾU:")
print(df.isna().sum().to_string())

print("\nSỐ GIÁ TRỊ KHÁC NHAU Ở MỘT SỐ CỘT:")
for col in ["system", "doc", "doc_id", "seg_id", "rater",
            "category", "severity"]:
    if col in df.columns:
        print(f"{col}: {df[col].nunique(dropna=True)}")
