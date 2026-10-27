import pandas as pd
from pathlib import Path

files = [
    Path("results/week10/model_data/mt_segment_level_all.csv"),
    Path("results/week10/model_data/mt_segment_level_consistent_text.csv"),
    Path("results/week10/model_data/mt_segment_text_consistency_issues.csv"),
]

for path in files:
    print("\n" + "=" * 80)
    print(f"FILE: {path}")
    if not path.exists():
        print("NOT FOUND")
        continue

    df = pd.read_csv(path)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False, max_cols=12))

    for col in ["y", "label", "serious_votes", "system", "doc"]:
        if col in df.columns:
            print(f"\n{col} distribution:")
            print(df[col].value_counts(dropna=False).head(15).to_string())
