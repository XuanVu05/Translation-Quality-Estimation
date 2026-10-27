
from pathlib import Path
import pandas as pd

root = Path(r"D:\Translation Quality Estimation")
mqm_path = root / "mqm_newstest2020_ende.tsv"
details_path = Path.home() / "Downloads" / "newstest2020txt-v2 (1)" / "txt" / "details" / "en-de.txt"

# Đọc bảng ánh xạ chính thức: line, testset, lang_pair, document_id, segment_id
details = pd.read_csv(
    details_path,
    sep=r"\s+",
    header=None,
    names=["line", "testset", "lang_pair", "document_id", "segment_id"],
    dtype=str
)

# Đọc TSV MQM, giữ nguyên nội dung các trường để kiểm tra
# Read MQM TSV using the same parser as the main data pipeline.
mqm = pd.read_csv(
    mqm_path,
    sep="\t",
    dtype=str,
    keep_default_na=False,
)

print("MQM columns:", mqm.columns.tolist())
print("MQM rows:", len(mqm))
print("Details rows:", len(details))
print("\nMQM sample:")
print(mqm[["doc", "seg_id"]].head(10).to_string(index=False))

print("\nDetails sample:")
print(details[["line", "document_id", "segment_id"]].head(10).to_string(index=False))

# Chuẩn hóa khoảng trắng và so sánh các cặp khóa
mqm_keys = set(zip(
    mqm["doc"].astype(str).str.strip(),
    mqm["seg_id"].astype(str).str.strip()
))
detail_keys = set(zip(
    details["document_id"].astype(str).str.strip(),
    details["line"].astype(str).str.strip()
))

matched = mqm_keys & detail_keys
mqm_only = mqm_keys - detail_keys
details_only = detail_keys - mqm_keys

print("\n=== KEY MATCH CHECK ===")
print("Unique MQM (doc, seg_id) keys:", len(mqm_keys))
print("Unique details (document_id, line) keys:", len(detail_keys))
print("Matched keys:", len(matched))
print("MQM keys absent from details:", len(mqm_only))
print("Details keys absent from MQM:", len(details_only))

print("\nMQM-only examples:", list(sorted(mqm_only))[:10])
print("Details-only examples:", list(sorted(details_only))[:10])

# Lưu báo cáo kiểm tra
out = root / "results" / "week10" / "data_quality"
out.mkdir(parents=True, exist_ok=True)
pd.DataFrame({
    "check": [
        "mqm_rows", "details_rows", "unique_mqm_keys",
        "unique_details_keys", "matched_keys",
        "mqm_only_keys", "details_only_keys"
    ],
    "value": [
        len(mqm), len(details), len(mqm_keys),
        len(detail_keys), len(matched),
        len(mqm_only), len(details_only)
    ]
}).to_csv(out / "official_details_alignment_check.csv", index=False)

print("\nSaved:", out / "official_details_alignment_check.csv")
