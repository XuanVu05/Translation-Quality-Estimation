
from pathlib import Path
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT / "results" / "week11"
    / "error_analysis_dev"
    / "final_10_case_analysis"
    / "dev_10_case_raw_annotations.csv"
)

OUTPUT_DIR = INPUT.parent
OUTPUT = OUTPUT_DIR / "dev_10_case_annotated_spans.csv"

df = pd.read_csv(INPUT)

def extract_spans(text):
    if pd.isna(text):
        return []

    return re.findall(r"<v>(.*?)</v>", str(text), flags=re.DOTALL)

records = []

for _, row in df.iterrows():
    spans = extract_spans(row["target"])

    # Preserve one row for annotations without an explicit span.
    if not spans:
        records.append({
            "case": row["case"],
            "system": row["system"],
            "doc": row["doc"],
            "doc_id": row["doc_id"],
            "seg_id": row["seg_id"],
            "rater": row["rater"],
            "category": row["category"],
            "severity": row["severity"],
            "annotated_span": "",
            "span_count": 0,
        })
        continue

    for span in spans:
        records.append({
            "case": row["case"],
            "system": row["system"],
            "doc": row["doc"],
            "doc_id": row["doc_id"],
            "seg_id": row["seg_id"],
            "rater": row["rater"],
            "category": row["category"],
            "severity": row["severity"],
            "annotated_span": span,
            "span_count": len(spans),
        })

result = pd.DataFrame(records)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 75)
print("MQM ANNOTATED SPANS EXTRACTED")
print("=" * 75)

print("Original annotation rows:", len(df))
print("Extracted records:", len(result))
print("Annotations with explicit spans:", (result["span_count"] > 0).sum())

print("\nOMISSION ANNOTATIONS:")
omissions = result[
    result["category"].str.contains(
        "Omission", case=False, na=False
    )
]

print(
    omissions[
        ["case", "rater", "category", "severity", "annotated_span"]
    ].to_string(index=False)
)

print("\nOUTPUT:")
print(OUTPUT)
