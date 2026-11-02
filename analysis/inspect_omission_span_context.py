
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

OUTPUT = (
    ROOT / "results" / "week11"
    / "error_analysis_dev"
    / "final_10_case_analysis"
    / "omission_span_context.csv"
)

df = pd.read_csv(INPUT)

omissions = df[
    df["category"].astype(str).str.contains(
        "Omission", case=False, na=False
    )
].copy()

records = []

for _, row in omissions.iterrows():

    marked_text = str(row.get("target", ""))

    matches = list(
        re.finditer(
            r"<v>(.*?)</v>",
            marked_text,
            flags=re.DOTALL
        )
    )

    if not matches:
        records.append({
            "case": row["case"],
            "rater": row["rater"],
            "category": row["category"],
            "severity": row["severity"],
            "span": "",
            "context_before": "",
            "context_after": "",
            "full_marked_target": marked_text,
            "note": "No explicit span found"
        })
        continue

    for match in matches:

        start, end = match.span()
        span = match.group(1)

        clean_before = re.sub(
            r"</?v>", "", marked_text[:start]
        )
        clean_after = re.sub(
            r"</?v>", "", marked_text[end:]
        )

        records.append({
            "case": row["case"],
            "rater": row["rater"],
            "category": row["category"],
            "severity": row["severity"],
            "span": repr(span),
            "context_before": clean_before[-50:],
            "context_after": clean_after[:50],
            "full_marked_target": marked_text,
            "note": ""
        })

result = pd.DataFrame(records)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 80)
print("OMISSION SPAN CONTEXT")
print("=" * 80)

for _, row in result.iterrows():
    print(f"\nCASE {row['case']} | {row['rater']}")
    print("Category:", row["category"])
    print("Severity:", row["severity"])
    print("Span:", row["span"])
    print("Before:", row["context_before"])
    print("After:", row["context_after"])
    print("Full target:", row["full_marked_target"])

print("\nSaved:", OUTPUT)
