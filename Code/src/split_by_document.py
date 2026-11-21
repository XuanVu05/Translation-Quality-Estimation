
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "results" / "week10" / "model_data" / "mt_segment_level_original_outputs.csv"
OUT_DIR = ROOT / "results" / "week10" / "model_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH, dtype={"doc": str, "system": str})

required = {"doc", "system", "y_primary", "source", "target"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

if df["y_primary"].isna().any():
    raise ValueError("Missing labels detected.")

# Split by document to prevent document leakage.
split1 = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
train_dev_idx, test_idx = next(
    split1.split(df, groups=df["doc"])
)
train_dev = df.iloc[train_dev_idx].copy()
test = df.iloc[test_idx].copy()

# Approximately 15% of all documents for development.
split2 = GroupShuffleSplit(
    n_splits=1, test_size=0.15 / 0.85, random_state=43
)
train_idx, dev_idx = next(
    split2.split(train_dev, groups=train_dev["doc"])
)
train = train_dev.iloc[train_idx].copy()
dev = train_dev.iloc[dev_idx].copy()

splits = {"train": train, "dev": dev, "test": test}

# Verify that no document occurs in multiple splits.
for a, b in [("train", "dev"), ("train", "test"), ("dev", "test")]:
    overlap = set(splits[a]["doc"]) & set(splits[b]["doc"])
    if overlap:
        raise ValueError(f"Document leakage between {a} and {b}: {overlap}")

# Save each split and a combined manifest.
df["split"] = ""
for name, part in splits.items():
    df.loc[part.index, "split"] = name
    part.to_csv(OUT_DIR / f"{name}_segments.csv", index=False)

df.to_csv(OUT_DIR / "segments_with_fixed_splits.csv", index=False)

print("=== SPLIT SUMMARY ===")
for name, part in splits.items():
    print(f"\n{name.upper()}")
    print("Rows:", len(part))
    print("Documents:", part["doc"].nunique())
    print("Systems:", part["system"].nunique())
    print("Positive samples:", int(part["y_primary"].sum()))
    print("Positive rate:", round(part["y_primary"].mean(), 5))
    print("Label counts:", part["y_primary"].value_counts().sort_index().to_dict())

print("\n=== DOCUMENT OVERLAP CHECK ===")
for a, b in [("train", "dev"), ("train", "test"), ("dev", "test")]:
    print(f"{a} vs {b}:", len(set(splits[a]["doc"]) & set(splits[b]["doc"])))

print("\nSaved files:")
for name in [
    "train_segments.csv",
    "dev_segments.csv",
    "test_segments.csv",
    "segments_with_fixed_splits.csv",
]:
    print(OUT_DIR / name)
