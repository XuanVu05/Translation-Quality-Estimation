
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "results" / "week10" / "model_data"

FILES = {
    "train": DATA_DIR / "train_segments.csv",
    "dev": DATA_DIR / "dev_segments.csv",
    "test": DATA_DIR / "test_segments.csv",
}

expected_systems = {
    "Huoshan_Translate.832",
    "OPPO.1535",
    "Online-A.1574",
    "Online-B.1590",
    "Tencent_Translation.1520",
    "Tohoku-AIP-NTT.890",
    "eTranslation.737",
}

frames = {}
all_ok = True

for split_name, path in FILES.items():
    df = pd.read_csv(path, dtype={"doc": str, "system": str})
    frames[split_name] = df

    print(f"\n=== {split_name.upper()} ===")
    print("Rows:", len(df))
    print("Documents:", df["doc"].nunique())
    print("Systems:", df["system"].nunique())
    print("Missing values in key fields:")
    print(df[["doc", "doc_id", "seg_id", "system", "source",
              "target", "y_primary"]].isna().sum().to_dict())

    assert set(df["system"]) == expected_systems, (
        f"Unexpected systems in {split_name}"
    )
    assert df["y_primary"].isin([0, 1]).all(), (
        f"Invalid labels in {split_name}"
    )
    assert df["source"].fillna("").str.strip().ne("").all(), (
        f"Empty source in {split_name}"
    )
    assert df["target"].fillna("").str.strip().ne("").all(), (
        f"Empty target in {split_name}"
    )

    # One row per system/document/segment.
    duplicated = df.duplicated(
        subset=["system", "doc", "doc_id"], keep=False
    )
    print("Duplicate system/doc/doc_id rows:", int(duplicated.sum()))
    assert not duplicated.any(), f"Duplicate rows in {split_name}"

    # Each document/segment should have all seven MT systems.
    systems_per_segment = df.groupby(["doc", "doc_id"])["system"].nunique()
    print("Segments not represented by all 7 systems:",
          int((systems_per_segment != 7).sum()))
    assert systems_per_segment.eq(7).all(), (
        f"Incomplete system coverage in {split_name}"
    )

# Ensure document-level separation.
names = list(frames)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        overlap = set(frames[a]["doc"]) & set(frames[b]["doc"])
        print(f"\nDocument overlap {a}/{b}:", len(overlap))
        assert not overlap, f"Document leakage between {a} and {b}"

# Check combined counts and label totals.
total_rows = sum(len(df) for df in frames.values())
total_positive = sum(int(df["y_primary"].sum()) for df in frames.values())

print("\n=== FINAL VALIDATION ===")
print("Total rows:", total_rows)
print("Total positive labels:", total_positive)
print("Expected rows: 9926")
print("Expected positive labels: 1183")

assert total_rows == 9926, "Unexpected total number of rows"
assert total_positive == 1183, "Unexpected total number of positive labels"

print("\nPASS: data splits passed all validation checks.")
