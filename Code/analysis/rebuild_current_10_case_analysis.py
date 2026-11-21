
from pathlib import Path
import csv
import re
import unicodedata
import hashlib

import pandas as pd


# ============================================================
# 1. PATHS AND CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

SELECTED_PATH = (
    ROOT / "results" / "week11" / "error_analysis_dev"
    / "dev_top20_error_analysis_10_cases.csv"
)

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = ROOT / "original_outputs"

OUT = (
    ROOT / "results" / "week11" / "error_analysis_dev"
    / "current_10_case_analysis"
)

KEYS = ["system", "doc", "doc_id", "seg_id"]

REQUIRED_SELECTED = KEYS + [
    "rank_LR_Base", "score_LR_Base",
    "source", "target", "y_primary", "serious_votes"
]

SYSTEM_FILES = {
    "eTranslation.737": "newstest2020.en-de.eTranslation.737.txt",
    "Huoshan_Translate.832": "newstest2020.en-de.Huoshan_Translate.832.txt",
    "Online-A.1574": "newstest2020.en-de.Online-A.1574.txt",
    "Online-B.1590": "newstest2020.en-de.Online-B.1590.txt",
    "OPPO.1535": "newstest2020.en-de.OPPO.1535.txt",
    "Tencent_Translation.1520": "newstest2020.en-de.Tencent_Translation.1520.txt",
    "Tohoku-AIP-NTT.890": "newstest2020.en-de.Tohoku-AIP-NTT.890.txt",
}


# ============================================================
# 2. NORMALIZATION
# ============================================================

def normalize_target(value):
    """Remove MQM markup and normalize text for target matching."""
    if pd.isna(value):
        return ""

    text = str(value)
    text = re.sub(r"</?v>", "", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_mqm():
    return pd.read_csv(
        MQM_PATH,
        sep="\t",
        dtype=str,
        keep_default_na=False,
        quoting=csv.QUOTE_NONE,
        encoding="utf-8"
    )


def load_mapping():
    mapping = pd.read_csv(
        MAPPING_PATH,
        sep="\t",
        header=None,
        dtype=str,
        keep_default_na=False
    )

    if mapping.shape[1] < 5:
        raise ValueError("Mapping file must contain at least 5 columns.")

    mapping = mapping.iloc[:, :5].copy()
    mapping.columns = [
        "line_id", "dataset", "language_pair",
        "doc", "doc_id"
    ]

    return mapping


def get_original_target(system, seg_id, output_cache):
    if system not in SYSTEM_FILES:
        raise ValueError(f"Unknown MT system: {system}")

    if system not in output_cache:
        path = OUTPUT_DIR / SYSTEM_FILES[system]

        if not path.exists():
            raise FileNotFoundError(path)

        output_cache[system] = path.read_text(
            encoding="utf-8",
            errors="strict"
        ).splitlines()

    lines = output_cache[system]
    line_no = int(seg_id)

    if line_no < 1 or line_no > len(lines):
        raise ValueError(
            f"Output line {line_no} out of range for {system}"
        )

    return lines[line_no - 1]


# ============================================================
# 3. LOAD AND VALIDATE INPUTS
# ============================================================

def main():
    for path in [SELECTED_PATH, MQM_PATH, MAPPING_PATH]:
        if not path.exists():
            raise FileNotFoundError(path)

    OUT.mkdir(parents=True, exist_ok=True)

    selected = pd.read_csv(
        SELECTED_PATH,
        dtype=str,
        keep_default_na=False
    )

    missing = [c for c in REQUIRED_SELECTED if c not in selected.columns]
    if missing:
        raise ValueError(f"Missing selected-case columns: {missing}")

    if len(selected) != 10:
        raise ValueError(f"Expected 10 selected cases, got {len(selected)}")

    if selected[KEYS].duplicated().any():
        raise ValueError("Duplicate selected case keys.")

    selected.insert(0, "case", range(1, 11))

    for col in ["doc_id", "seg_id", "rank_LR_Base"]:
        selected[col] = pd.to_numeric(
            selected[col], errors="raise"
        ).astype(int)

    for col in ["score_LR_Base"]:
        selected[col] = pd.to_numeric(
            selected[col], errors="raise"
        )

    selected["y_primary"] = pd.to_numeric(
        selected["y_primary"], errors="raise"
    ).astype(int)

    selected["serious_votes"] = pd.to_numeric(
        selected["serious_votes"], errors="raise"
    ).astype(int)

    if not selected["y_primary"].eq(0).all():
        raise ValueError("Selected cases must have y_primary = 0.")

    if not selected["serious_votes"].eq(0).all():
        raise ValueError("Selected cases must have serious_votes = 0.")

    selected.to_csv(
        OUT / "current_10_cases.csv",
        index=False,
        encoding="utf-8-sig"
    )

    mqm = read_mqm()
    mapping = load_mapping()

    required_mqm = KEYS + [
        "rater", "source", "target", "category", "severity"
    ]

    missing = [c for c in required_mqm if c not in mqm.columns]
    if missing:
        raise ValueError(f"Missing MQM columns: {missing}")

    for col in KEYS + ["rater", "category", "severity"]:
        mqm[col] = mqm[col].astype(str).str.strip()

    mqm["target_normalized"] = mqm["target"].map(normalize_target)
    selected["target_normalized"] = selected["target"].map(
        normalize_target
    )

    mapping["line_id"] = pd.to_numeric(
        mapping["line_id"], errors="raise"
    ).astype(int)

    mapping["doc_id"] = pd.to_numeric(
        mapping["doc_id"], errors="raise"
    ).astype(int)

    output_cache = {}


    # ========================================================
    # 4. EXTRACT ALL CANDIDATE MQM ANNOTATIONS
    # ========================================================

    candidate_parts = []

    for _, case in selected.iterrows():
        mask = pd.Series(True, index=mqm.index)

        for col in KEYS:
            mask &= mqm[col].eq(str(case[col]))

        subset = mqm.loc[mask].copy()

        if subset.empty:
            raise ValueError(
                f"No MQM annotations for case {case['case']}"
            )

        subset.insert(0, "case", int(case["case"]))
        subset["target_match"] = (
            subset["target_normalized"]
            == case["target_normalized"]
        )

        candidate_parts.append(subset)

    candidates = pd.concat(candidate_parts, ignore_index=True)

    matched = candidates[candidates["target_match"]].copy()
    unmatched = candidates[~candidates["target_match"]].copy()

    if matched.empty:
        raise ValueError("No target-matched MQM annotations.")

    # Every selected case must have at least one matched annotation.
    matched_counts = matched.groupby("case").size()

    if len(matched_counts) != 10 or not matched_counts.gt(0).all():
        raise ValueError(
            "At least one selected case has no target-matched annotations."
        )

    candidates.to_csv(
        OUT / "current_10_case_candidate_annotations.csv",
        index=False, encoding="utf-8-sig"
    )

    matched.to_csv(
        OUT / "current_10_case_matched_annotations.csv",
        index=False, encoding="utf-8-sig"
    )

    unmatched.to_csv(
        OUT / "current_10_case_unmatched_annotations.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 5. ANNOTATION SUMMARY AND SERIOUS VOTES
    # ========================================================

    matched["is_serious_error"] = (
        matched["severity"].eq("Major")
        & (
            matched["category"].str.startswith("Accuracy/")
            | matched["category"].eq("Non-translation!")
        )
    ).astype(int)

    rater_votes = (
        matched.groupby(["case"] + KEYS + ["rater"], as_index=False)
        .agg(rater_serious_vote=("is_serious_error", "max"))
    )

    vote_summary = (
        rater_votes.groupby("case", as_index=False)
        .agg(
            matched_raters=("rater", "nunique"),
            serious_votes_recomputed=("rater_serious_vote", "sum")
        )
    )

    vote_summary["y_primary_recomputed"] = (
        vote_summary["serious_votes_recomputed"] >= 2
    ).astype(int)

    summary_rows = []

    for _, case in selected.iterrows():
        case_id = int(case["case"])
        ann = matched[matched["case"] == case_id].copy()

        vote = vote_summary[vote_summary["case"] == case_id].iloc[0]

        categories = sorted(set(ann["category"]) - {""})
        severities = sorted(set(ann["severity"]) - {""})

        summary_rows.append({
            "case": case_id,
            **{k: case[k] for k in KEYS},
            "rank_LR_Base": case["rank_LR_Base"],
            "score_LR_Base": case["score_LR_Base"],
            "y_primary_original": case["y_primary"],
            "serious_votes_original": case["serious_votes"],
            "matched_annotation_rows": len(ann),
            "unmatched_annotation_rows": len(
                unmatched[unmatched["case"] == case_id]
            ),
            "matched_raters": int(vote["matched_raters"]),
            "major_annotation_rows": int(
                ann["severity"].eq("Major").sum()
            ),
            "serious_annotation_rows": int(
                ann["is_serious_error"].sum()
            ),
            "serious_votes_recomputed": int(
                vote["serious_votes_recomputed"]
            ),
            "y_primary_recomputed": int(
                vote["y_primary_recomputed"]
            ),
            "has_minor": bool(ann["severity"].eq("Minor").any()),
            "has_major": bool(ann["severity"].eq("Major").any()),
            "has_omission": bool(
                ann["category"].str.contains(
                    "Omission", case=False, na=False
                ).any()
            ),
            "has_no_error": bool(
                ann["category"].eq("No-error").any()
            ),
            "categories": " | ".join(categories),
            "severities": " | ".join(severities),
            "annotation_details": " || ".join(
                f"{r.rater}: {r.category} ({r.severity})"
                for r in ann.itertuples()
            )
        })

    summary = pd.DataFrame(summary_rows)

    # Recomputed labels must agree with the original operational labels.
    if not (
        summary["serious_votes_recomputed"]
        == summary["serious_votes_original"]
    ).all():
        raise ValueError("Recomputed serious votes disagree with Dev labels.")

    if not (
        summary["y_primary_recomputed"]
        == summary["y_primary_original"]
    ).all():
        raise ValueError("Recomputed y_primary disagrees with Dev labels.")

    summary.to_csv(
        OUT / "current_10_case_audit_summary.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 6. EXTRACT ANNOTATED SPANS FROM MATCHED ANNOTATIONS ONLY
    # ========================================================

    span_rows = []

    for row in matched.itertuples():
        spans = re.findall(
            r"<v>(.*?)</v>",
            str(row.target),
            flags=re.DOTALL
        )

        if not spans:
            span_rows.append({
                "case": row.case,
                "system": row.system,
                "doc": row.doc,
                "doc_id": row.doc_id,
                "seg_id": row.seg_id,
                "rater": row.rater,
                "category": row.category,
                "severity": row.severity,
                "annotated_span": "",
                "span_count": 0
            })
        else:
            for span in spans:
                span_rows.append({
                    "case": row.case,
                    "system": row.system,
                    "doc": row.doc,
                    "doc_id": row.doc_id,
                    "seg_id": row.seg_id,
                    "rater": row.rater,
                    "category": row.category,
                    "severity": row.severity,
                    "annotated_span": span,
                    "span_count": len(spans)
                })

    spans_df = pd.DataFrame(span_rows)

    spans_df.to_csv(
        OUT / "current_10_case_annotated_spans.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 7. VERIFY ORIGINAL MT OUTPUTS AND MAPPING
    # ========================================================

    original_rows = []

    for _, case in selected.iterrows():
        case_id = int(case["case"])
        global_id = int(case["seg_id"])
        local_id = int(case["doc_id"])

        map_rows = mapping[mapping["line_id"].eq(global_id)]

        if len(map_rows) != 1:
            raise ValueError(
                f"Case {case_id}: expected one mapping row, "
                f"found {len(map_rows)}"
            )

        map_row = map_rows.iloc[0]

        mapping_ok = (
            map_row["doc"] == case["doc"]
            and int(map_row["doc_id"]) == local_id
        )

        if not mapping_ok:
            raise ValueError(f"Case {case_id}: mapping mismatch.")

        original_target = get_original_target(
            case["system"], global_id, output_cache
        )

        original_rows.append({
            "case": case_id,
            **{k: case[k] for k in KEYS},
            "mapping_ok": mapping_ok,
            "source_dev": case["source"],
            "target_dev": case["target"],
            "target_original": original_target,
            "dev_target_matches_original": (
                normalize_target(case["target"])
                == normalize_target(original_target)
            ),
            "output_line": global_id
        })

    original_df = pd.DataFrame(original_rows)

    original_df.to_csv(
        OUT / "current_10_case_original_mt.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 8. NEIGHBORING SEGMENTS: PREVIOUS / CURRENT / NEXT
    # ========================================================

    neighbor_rows = []

    for _, case in selected.iterrows():
        case_id = int(case["case"])
        local_id = int(case["doc_id"])

        for neighbor_local in range(local_id - 1, local_id + 2):
            map_rows = mapping[
                (mapping["doc"] == case["doc"])
                & (mapping["doc_id"] == neighbor_local)
            ]

            if len(map_rows) != 1:
                neighbor_rows.append({
                    "case": case_id,
                    "system": case["system"],
                    "doc": case["doc"],
                    "position": (
                        "PREVIOUS" if neighbor_local < local_id
                        else "CURRENT" if neighbor_local == local_id
                        else "NEXT"
                    ),
                    "local_segment": neighbor_local,
                    "mapping_status": "NOT_UNIQUE_OR_NOT_FOUND",
                    "source": "",
                    "original_mt_target": ""
                })
                continue

            map_row = map_rows.iloc[0]
            global_id = int(map_row["line_id"])

            source_rows = mqm[
                (mqm["doc"] == case["doc"])
                & (mqm["doc_id"] == str(neighbor_local))
                & (mqm["seg_id"] == str(global_id))
            ]

            source = (
                source_rows["source"].iloc[0]
                if not source_rows.empty else ""
            )

            target = get_original_target(
                case["system"], global_id, output_cache
            )

            neighbor_rows.append({
                "case": case_id,
                "system": case["system"],
                "doc": case["doc"],
                "position": (
                    "PREVIOUS" if neighbor_local < local_id
                    else "CURRENT" if neighbor_local == local_id
                    else "NEXT"
                ),
                "local_segment": neighbor_local,
                "global_seg_id": global_id,
                "mapping_status": "PASS",
                "source": source,
                "original_mt_target": target
            })

    neighbors = pd.DataFrame(neighbor_rows)

    neighbors.to_csv(
        OUT / "current_10_case_neighbor_segments.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 9. OMISSION SPAN CONTEXT
    # ========================================================

    omissions = matched[
        matched["category"].str.contains(
            "Omission", case=False, na=False
        )
    ].copy()

    omission_rows = []

    for row in omissions.itertuples():
        marked = str(row.target)

        matches = list(re.finditer(
            r"<v>(.*?)</v>",
            marked,
            flags=re.DOTALL
        ))

        if not matches:
            omission_rows.append({
                "case": row.case,
                "rater": row.rater,
                "category": row.category,
                "severity": row.severity,
                "span": "",
                "context_before": "",
                "context_after": "",
                "note": "No explicit <v> span"
            })
            continue

        for match in matches:
            start, end = match.span()

            before = re.sub(r"</?v>", "", marked[:start])
            after = re.sub(r"</?v>", "", marked[end:])

            omission_rows.append({
                "case": row.case,
                "rater": row.rater,
                "category": row.category,
                "severity": row.severity,
                "span": match.group(1),
                "context_before": before[-50:],
                "context_after": after[:50],
                "note": ""
            })

    omission_df = pd.DataFrame(omission_rows)

    omission_df.to_csv(
        OUT / "current_10_case_omission_context.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 10. FINAL EVIDENCE TABLE
    # ========================================================

    evidence = (
        selected.merge(
            summary,
            on=["case"] + KEYS,
            suffixes=("_selected", ""),
            validate="one_to_one"
        )
        .merge(
            original_df[
                ["case", "target_original", "mapping_ok",
                 "dev_target_matches_original"]
            ],
            on="case",
            validate="one_to_one"
        )
    )

    evidence["manual_assessment"] = (
        "Pending manual review; do not infer from MQM labels alone."
    )

    evidence["interpretation"] = (
        "Describe only after reviewing matched annotations, "
        "original MT output and source text."
    )

    evidence.to_csv(
        OUT / "current_10_case_qualitative_evidence.csv",
        index=False, encoding="utf-8-sig"
    )


    # ========================================================
    # 11. AUDIT REPORT
    # ========================================================

    report = [
        "# Current 10-Case MQM Audit",
        "",
        "## Input provenance",
        f"- Selected cases: `{SELECTED_PATH.relative_to(ROOT)}`",
        f"- MQM file SHA-256: `{sha256(MQM_PATH)}`",
        f"- Selected CSV SHA-256: `{sha256(SELECTED_PATH)}`",
        "",
        "## Matching results",
        f"- Selected cases: {len(selected)}",
        f"- Cases with target-matched annotations: "
        f"{matched['case'].nunique()}",
        f"- Candidate annotation rows: {len(candidates)}",
        f"- Target-matched annotation rows: {len(matched)}",
        f"- Target-unmatched annotation rows: {len(unmatched)}",
        "",
        "## Operational label validation",
        f"- Serious annotation rows: "
        f"{int(matched['is_serious_error'].sum())}",
        f"- Recomputed serious votes: "
        f"{int(summary['serious_votes_recomputed'].sum())}",
        f"- Cases with recomputed y_primary = 1: "
        f"{int(summary['y_primary_recomputed'].sum())}",
        "",
        "## Original MT verification",
        f"- Mapping checks passed: "
        f"{int(original_df['mapping_ok'].sum())}/10",
        f"- Dev target matches original MT: "
        f"{int(original_df['dev_target_matches_original'].sum())}/10",
        "",
        "## Important interpretation limits",
        "- Target-unmatched annotations are retained separately.",
        "- Target-unmatched does not mean annotation is invalid.",
        "- Annotated spans are extracted from target-matched rows only.",
        "- MQM annotation is not equivalent to manual semantic judgment.",
        "- Manual assessment fields are intentionally left pending.",
        "- No model was retrained and no Test data was used.",
        "",
        "## Per-case summary",
        "",
        summary[
            [
                "case", "system", "doc", "doc_id", "seg_id",
                "matched_annotation_rows",
                "unmatched_annotation_rows",
                "matched_raters",
                "major_annotation_rows",
                "serious_votes_recomputed",
                "y_primary_recomputed"
            ]
        ].to_string(index=False),
        ""
    ]

    (OUT / "current_10_case_audit_report.md").write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("=" * 75)
    print("CURRENT 10-CASE ANALYSIS COMPLETED")
    print("=" * 75)
    print("Cases:", len(selected))
    print("Candidate annotations:", len(candidates))
    print("Target-matched annotations:", len(matched))
    print("Target-unmatched annotations:", len(unmatched))
    print("Original MT mapping:", int(original_df["mapping_ok"].sum()), "/ 10")
    print("Dev target = original MT:",
          int(original_df["dev_target_matches_original"].sum()), "/ 10")
    print("Output directory:", OUT)

    print("\nCASE SUMMARY:")
    print(        "```text",
        summary[
            [
                "case", "system", "doc", "doc_id", "seg_id",
                "matched_annotation_rows",
                "unmatched_annotation_rows",
                "matched_raters",
                "major_annotation_rows",
                "serious_votes_recomputed",
                "y_primary_recomputed"
            ]
        ].to_string(index=False),
        "```",)


if __name__ == "__main__":
    main()
