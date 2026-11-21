
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

SOURCE = (
    ROOT / "results" / "week10" / "model_data"
    / "segments_with_fixed_splits.csv"
)

OUT_DIR = ROOT / "results" / "week10" / "locked_split"

EXPECTED = {
    "train": {"rows": 6797, "docs": 90, "positive": 803},
    "dev":   {"rows": 1554, "docs": 20, "positive": 218},
    "test":  {"rows": 1575, "docs": 20, "positive": 162},
}

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

if not SOURCE.exists():
    raise FileNotFoundError(f"Không tìm thấy CSV: {SOURCE}")

df = pd.read_csv(SOURCE, dtype={"doc": str, "system": str})

required = {
    "doc", "system", "seg_id", "source", "target",
    "y_primary", "split"
}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Thiếu cột bắt buộc: {sorted(missing)}")

if df[list(required)].isna().any().any():
    raise ValueError("Có giá trị thiếu trong các cột bắt buộc.")

if set(df["split"].unique()) != {"train", "dev", "test"}:
    raise ValueError("Giá trị split không đúng.")

if not set(df["y_primary"].unique()).issubset({0, 1}):
    raise ValueError("y_primary phải chỉ chứa nhãn 0 và 1.")

if df.duplicated(["system", "doc", "seg_id"]).any():
    raise ValueError("Phát hiện bản ghi trùng theo system/doc/seg_id.")

summary = {}
for name, expected in EXPECTED.items():
    part = df[df["split"] == name]
    actual = {
        "rows": int(len(part)),
        "docs": int(part["doc"].nunique()),
        "positive": int(part["y_primary"].sum()),
    }

    if actual != expected:
        raise ValueError(
            f"{name}: thực tế {actual}, "
            f"khác kỳ vọng {expected}. Không khóa split."
        )

    summary[name] = {
        **actual,
        "systems": int(part["system"].nunique()),
        "positive_rate": round(float(part["y_primary"].mean()), 6),
    }

doc_sets = {
    name: set(df.loc[df["split"] == name, "doc"])
    for name in EXPECTED
}

overlaps = {
    "train_dev": sorted(doc_sets["train"] & doc_sets["dev"]),
    "train_test": sorted(doc_sets["train"] & doc_sets["test"]),
    "dev_test": sorted(doc_sets["dev"] & doc_sets["test"]),
}

if any(overlaps.values()):
    raise ValueError(f"Phát hiện rò rỉ tài liệu: {overlaps}")

# Chỉ tạo thư mục và snapshot nếu các kiểm tra đều đạt.
OUT_DIR.mkdir(parents=True, exist_ok=True)

snapshot = OUT_DIR / "segments_week10_90_20_20.csv"
if snapshot.exists():
    raise FileExistsError(
        f"Snapshot đã tồn tại: {snapshot}\n"
        "Không ghi đè; hãy kiểm tra bản khóa trước."
    )

df.to_csv(snapshot, index=False)

# Danh sách tài liệu theo split để kiểm tra và tái sử dụng.
assignments = (
    df[["doc", "split"]]
    .drop_duplicates()
    .sort_values(["split", "doc"])
)

if assignments["doc"].duplicated().any():
    raise ValueError("Một tài liệu xuất hiện ở nhiều split.")

assignments.to_csv(
    OUT_DIR / "document_assignments.csv", index=False
)

manifest = {
    "status": "candidate_locked",
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "split_method": "GroupShuffleSplit by doc",
    "random_state_first_split": 42,
    "random_state_second_split": 43,
    "split_ratios_target": {
        "train": 0.70, "dev": 0.15, "test": 0.15
    },
    "label_column": "y_primary",
    "source_csv": str(SOURCE.relative_to(ROOT)),
    "source_sha256": sha256_file(SOURCE),
    "snapshot_csv": str(snapshot.relative_to(ROOT)),
    "snapshot_sha256": sha256_file(snapshot),
    "total_rows": int(len(df)),
    "total_documents": int(df["doc"].nunique()),
    "total_positive": int(df["y_primary"].sum()),
    "summary": summary,
    "document_overlap": {
        key: len(value) for key, value in overlaps.items()
    },
}

with open(OUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

report = [
    "WEEK 10 SPLIT QA REPORT",
    "Status: candidate_locked",
    f"Total rows: {len(df)}",
    f"Total documents: {df['doc'].nunique()}",
    f"Total positive labels: {int(df['y_primary'].sum())}",
    "",
]

for name, stats in summary.items():
    report.append(f"{name.upper()}: {stats}")

report += [
    "",
    f"Missing required values: {int(df[list(required)].isna().sum().sum())}",
    f"Duplicate system/doc/seg_id rows: "
    f"{int(df.duplicated(['system', 'doc', 'seg_id']).sum())}",
    f"Document overlaps: {manifest['document_overlap']}",
    f"Source SHA-256: {manifest['source_sha256']}",
    f"Snapshot SHA-256: {manifest['snapshot_sha256']}",
    "",
    "NOTE: This script validates and snapshots the existing split.",
    "It does not independently regenerate the split from raw input.",
]

(OUT_DIR / "qa_report.txt").write_text(
    "\n".join(report), encoding="utf-8"
)

print("\n".join(report))
print(f"\nSnapshot and audit files saved to: {OUT_DIR}")
