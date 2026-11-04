from pathlib import Path
import json
import pandas as pd

ROOT = Path(".")
BASE = ROOT / "results/week10/error_analysis_dev"

INPUT = BASE / "dev_top20_zero_vote_annotations.csv"
SEGMENT_OUT = BASE / "dev_top20_zero_vote_strict_segment_audit.csv"
RATER_OUT = BASE / "dev_top20_zero_vote_strict_rater_audit.csv"
SUMMARY_OUT = BASE / "dev_top20_zero_vote_strict_audit_summary.json"

KEYS = ["system", "doc", "doc_id", "seg_id"]

if not INPUT.is_file():
    raise FileNotFoundError(INPUT)

all_rows = pd.read_csv(INPUT, dtype=str, keep_default_na=False)

required = KEYS + [
    "rater", "category", "severity", "target_match"
]
missing = sorted(set(required) - set(all_rows.columns))
if missing:
    raise ValueError(f"Missing columns: {missing}")

matched = all_rows.loc[
    all_rows["target_match"].str.casefold().eq("true")
].copy()

unmatched = all_rows.loc[
    all_rows["target_match"].str.casefold().eq("false")
].copy()

matched["is_minor"] = matched["severity"].str.casefold().eq("minor")
matched["is_major"] = matched["severity"].str.casefold().eq("major")
matched["is_no_error"] = matched["category"].str.casefold().eq("no-error")

rater = (
    matched.groupby(KEYS + ["rater"], dropna=False)
    .agg(
        has_minor=("is_minor", "any"),
        has_major=("is_major", "any"),
        has_no_error=("is_no_error", "any"),
        annotation_rows=("category", "size"),
    )
    .reset_index()
)

rater["has_error"] = rater["has_minor"] | rater["has_major"]

segment = (
    rater.groupby(KEYS)
    .agg(
        n_raters=("rater", "nunique"),
        n_error_raters=("has_error", "sum"),
        n_no_error_raters=("has_no_error", "sum"),
        has_minor=("has_minor", "any"),
        has_major=("has_major", "any"),
    )
    .reset_index()
)

segment["disagreement"] = (
    (segment["n_error_raters"] > 0)
    & (segment["n_no_error_raters"] > 0)
)

segment["status"] = "No_MQM_Error_Recorded"
segment.loc[segment["has_minor"], "status"] = "Minor_Error"
segment.loc[
    segment["has_minor"] & segment["has_major"], "status"
] = "Minor_and_Major_Error"

# Fail-fast validation against the audited dataset.
assert len(all_rows) == 959
assert len(matched) == 893
assert len(unmatched) == 66
assert segment[KEYS].drop_duplicates().shape[0] == 180
assert len(segment) == 180

status_counts = segment["status"].value_counts().to_dict()
disagreement_count = int(segment["disagreement"].sum())
rater_counts = segment["n_raters"].value_counts().to_dict()

assert status_counts == {
    "Minor_Error": 149,
    "No_MQM_Error_Recorded": 30,
    "Minor_and_Major_Error": 1,
}
assert disagreement_count == 77
assert rater_counts == {3: 163, 2: 14, 1: 3}

segment.to_csv(SEGMENT_OUT, index=False, encoding="utf-8-sig")
rater.to_csv(RATER_OUT, index=False, encoding="utf-8-sig")

summary = {
    "input": str(INPUT),
    "candidate_annotation_rows": len(all_rows),
    "target_matched_annotation_rows": len(matched),
    "target_unmatched_annotation_rows": len(unmatched),
    "unique_segments": len(segment),
    "strict_status_distribution": status_counts,
    "annotator_disagreement_segments": disagreement_count,
    "annotator_disagreement_rate": disagreement_count / len(segment),
    "rater_count_distribution": {
        str(k): int(v) for k, v in rater_counts.items()
    },
    "disagreement_definition": (
        "A segment is marked as disagreement when at least one matched "
        "rater has a Minor/Major annotation and at least one matched "
        "rater has a No-error annotation."
    ),
    "outputs": [str(SEGMENT_OUT), str(RATER_OUT)],
}

SUMMARY_OUT.write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("STRICT TARGET-MATCHING AUDIT: PASS")
print(json.dumps(summary, indent=2, ensure_ascii=False))
