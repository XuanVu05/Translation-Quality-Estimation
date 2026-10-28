
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

source_path = (
    ROOT / "results" / "week10" / "model_data"
    / "segments_with_fixed_splits.csv"
)
snapshot_path = (
    ROOT / "results" / "week10" / "locked_split"
    / "segments_week10_90_20_20.csv"
)
assign_path = (
    ROOT / "results" / "week10" / "locked_split"
    / "document_assignments.csv"
)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for path in [source_path, snapshot_path, assign_path]:
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")

df = pd.read_csv(source_path, dtype={"doc": str, "system": str})
snapshot = pd.read_csv(snapshot_path, dtype={"doc": str, "system": str})
assignments = pd.read_csv(assign_path, dtype={"doc": str})

print("=== FILE AND HASH CHECK ===")
print("Source rows:", len(df))
print("Snapshot rows:", len(snapshot))
print("Source SHA-256:", sha256(source_path))
print("Snapshot SHA-256:", sha256(snapshot_path))
print("Hashes equal:", sha256(source_path) == sha256(snapshot_path))

print("\n=== SPLIT COUNTS ===")
print(
    df.groupby("split").agg(
        rows=("y_primary", "size"),
        docs=("doc", "nunique"),
        positives=("y_primary", "sum"),
        positive_rate=("y_primary", "mean"),
    ).to_string()
)

print("\n=== DOCUMENT ASSIGNMENTS ===")
print("Assignment rows:", len(assignments))
print("Unique documents:", assignments["doc"].nunique())
print("Duplicate document assignments:", assignments["doc"].duplicated().sum())
print(assignments["split"].value_counts().to_string())

# Verify source and snapshot have identical content.
print("\n=== DATAFRAME EQUALITY ===")
print("Same columns:", list(df.columns) == list(snapshot.columns))
print("Same shape:", df.shape == snapshot.shape)
print("Same data in same row order:", df.equals(snapshot))

# Verify that each document has only one split.
doc_split_counts = df.groupby("doc")["split"].nunique()
print("\nDocuments assigned to multiple splits:", int((doc_split_counts > 1).sum()))

# Verify assignments agree with the combined CSV.
expected_assignments = (
    df[["doc", "split"]]
    .drop_duplicates()
    .sort_values(["doc", "split"])
    .reset_index(drop=True)
)
actual_assignments = (
    assignments[["doc", "split"]]
    .sort_values(["doc", "split"])
    .reset_index(drop=True)
)
print(
    "Assignments match combined CSV:",
    expected_assignments.equals(actual_assignments),
)
