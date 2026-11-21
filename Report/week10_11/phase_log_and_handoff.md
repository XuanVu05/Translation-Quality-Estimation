# MLA Project -- Phase Log and Session Handoff

**Project:** Second Pair of Eyes -- Reference-Free Critical Error
Detection\
**Project root:** `D:\Translation-Quality-Estimation`\
**Python environment:** `.venv_mla` (Python 3.13)

Use this file to preserve progress between sessions. At the end of each
session, update the status, evidence, decisions, unresolved issues, and
exact next action.

## G1.1 -- Dataset provenance and license audit

**Status: Completed.**

-   Source repository identified: `google/wmt-mqm-human-evaluation`.
-   Local MQM TSV compared with repository version; SHA-256:
    `22ACB4D5CC4DC0D8F2683E9251C179C917AE8589D71B1945D755C46D88D345E3`.
-   Official WMT20 Metrics Task archive downloaded and checked.
-   Mapping file and seven original MT output files: 8/8 exact matches.
-   `reports/source_file_manifest.csv` generated.
-   `reports/dataset_license_audit.md` generated.

**License qualification:** Repository-level Apache 2.0 evidence does not
conclusively establish unrestricted redistribution rights for every
third-party component or the separate WMT archive. Preserve this caveat.

Archive SHA-256:
`98131534F0962CC2A050C7CDFA6CAC63EA94349248C912E0F4EA77F6650C547D`.

## G1.2 -- Data structure and quality audit

**Status: Completed for structural, source, rater-coverage,
target-normalization, and original-output alignment checks.**

Scripts created/run: - `analysis/audit_data_quality.py` -
`analysis/audit_annotation_structure.py` -
`analysis/audit_target_normalization.py` -
`analysis/inspect_remaining_variants.py` -
`analysis/audit_variants_by_system.py` -
`analysis/compare_mqm_with_original_mt.py` -
`analysis/inspect_mqm_original_mismatches.py`

Key findings: - MQM: 79,020 rows × 9 columns. - Mapping: 1,418 rows; 130
documents. - Missing values: 0. - Exact duplicate rows: 0. - Systems: 7
MT + 3 Human. - Rater identifiers: 6. - Unique system-segment groups:
14,180. - Source-inconsistent segments: 0. - One two-rater exception:
`Online-A.1574`, `sky.com.20669`, global `seg_id=1161`; observed
annotations are Minor punctuation. - Correct mapping: `MQM.doc` →
`mapping.document_id`; `MQM.seg_id` → `mapping.line_id`. - Mapping
coverage: 79,020/79,020; unmatched: 0. - MT system-segments: 9,926. -
Annotated target comparison: 7,838 All match; 2,072 Some match; 16 None
match. - Original MT output files are the recommended authoritative
target source for feature extraction. - MQM category/severity
annotations remain the source for label construction.

Important outputs under `analysis/data_quality_results/`: -
`data_quality_summary.json` - `target_normalization_summary.json` -
`target_variants_by_type.csv` - `target_variants_by_system.csv` -
`mqm_vs_original_summary.csv` - `mqm_vs_original_all_segments.csv` -
`inspect_none_match_segments.csv` - `inspect_some_match_sample.csv`

See `reports/data_quality_audit.md` for the detailed report.

## G1.3 -- Critical Error label audit

**Status: Next task; not yet completed.**

Questions: 1. What is the approved operational definition of Critical
Error? 2. Which categories qualify? 3. Which severity levels qualify? 4.
How are multiple annotation rows from the same rater aggregated? 5. Is
each rater counted at most once per system-segment? 6. What vote
threshold defines a positive segment? 7. How is the one two-rater
segment handled? 8. Are Human systems excluded from the MT prediction
dataset? 9. Does each MT system-segment receive exactly one final label?
10. Can labels be regenerated reproducibly from one script?

**Candidate rule previously discussed, not yet re-certified:**

``` python
serious_annotation = (
    (severity == "Major" and category.startswith("Accuracy/"))
    or category == "Non-translation!"
)
```

Candidate segment label:

``` python
y = 1 if number_of_distinct_raters_with_serious_error >= 2 else 0
```

Do not treat this as final until checked against the lecturer-approved
definition and current label-generation code.

Required aggregation: 1. Classify raw annotation rows using the approved
serious-error rule. 2. Group by `(system, doc, doc_id, seg_id, rater)`.
3. Give each rater one binary vote per segment: 1 if at least one
qualifying serious annotation exists; otherwise 0 if that rater has
annotation coverage. 4. Count distinct serious-voting raters per
system-segment. 5. Apply the approved vote threshold. 6. Preserve
observed rater count and serious-vote count. 7. Handle the two-rater
exception explicitly.

Expected outputs: - `analysis/audit_label_logic.py` -
`analysis/label_audit_results/label_rule_summary.json` -
`analysis/label_audit_results/serious_votes_by_rater.csv` -
`analysis/label_audit_results/segment_label_distribution.csv` -
`analysis/label_audit_results/label_edge_cases.csv` -
`analysis/label_audit_results/label_trace_sample.csv` -
`reports/label_definition_audit.md`

Exit criteria: - Approved rule written in Boolean form. - Multiple
annotations from one rater count as at most one vote. - Vote threshold
justified. - Two-rater exception explicitly handled. - One label per
included MT system-segment. - Positive/negative distribution and
prevalence reported. - Edge cases traceable to raw MQM rows. - Label
generation reproducible with one command.

## G1.4 -- Feature and leakage audit

**Status: Pending G1.3.**

Verify: - Features use original MT outputs, not MQM annotated targets. -
Source and target join using verified global line mapping. - No features
are derived from labels, category, severity, or annotator identity. -
System identity inclusion/ablation is documented. - Vectorizers are
fitted on training data only. - IDs are not accidentally predictive
features. - Preprocessing is reproducible.

Expected report: `reports/feature_and_leakage_audit.md`.

## G1.5 -- Split and reproducibility audit

**Status: Pending.**

Previously recorded candidate split: - Train: 6,797 segments, 90
documents, 803 positives. - Dev: 1,554 segments, 20 documents, 218
positives. - Test: 1,575 segments, 20 documents, 162 positives. - No
document overlap. - Split hash:
`780cd9f0b2b32042ad95f8e67318c03814fbe895e1f0ef8755da847e8d287ab`. -
Earlier manifest status: `candidate_locked`; verifier printed checks but
did not raise exceptions.

Re-verify these values from current split files before calling them
final.

## G2 -- Experiments and comparisons

**Status: Historical results exist; re-verify against saved predictions
before final reporting.**

Previously recorded Dev ablation: - LR Base: PR-AUC 0.1961; Precision@20
0.2026; Recall@20 0.2890; Lift 1.4440; MCC 0.0897. - LR + System: PR-AUC
0.1991; Precision@20 0.1961; Recall@20 0.2798; Lift 1.3982; MCC
0.0805. - System Only: PR-AUC 0.1568; Precision@20 0.1768; Recall@20
0.2523; Lift 1.2607; MCC 0.0527.

Previously recorded Test: - Random: PR-AUC 0.1091; Precision@20 0.1016;
Recall@20 0.1975; Lift 0.9877; MCC -0.0021. - Heuristic: PR-AUC 0.1391;
Precision@20 0.1587; Recall@20 0.3086; Lift 1.5432; MCC 0.0920. - LR:
PR-AUC 0.1971; Precision@20 0.1619; Recall@20 0.3148; Lift 1.5741; MCC
0.0972. - SVM: PR-AUC 0.1676; Precision@20 0.1206; Recall@20 0.2346;
Lift 1.1728; MCC 0.0293.

Previously recorded paired document-cluster bootstrap (1,000 reps, seed
20261027), LR versus heuristic: - PR-AUC delta +0.0580, CI \[0.0151,
0.1232\]. - Recall@20 delta +0.0062, CI \[-0.0880, 0.1818\]. -
Precision@20 delta +0.0032, CI \[-0.0525, 0.0820\]. - Lift delta
+0.0309, CI \[-0.4393, 0.9075\].

These are historical notes, not yet re-certified.

## Session handoff template

### Session: \[date\]

**Stage:**\
**Objective:**\
**Scripts run:**\
**Commands:**\
**Outputs created/updated:**\
**Verified findings:**\
**Decisions made:**\
**Open issues:**\
**Next exact action:**\
**Git status / commit:**

## Project operating rules

-   Run commands from `D:\Translation-Quality-Estimation`.
-   Use `.venv_mla\python.exe`; do not use the broken `.venv`.
-   Preserve raw dataset files and original MT outputs.
-   Do not silently overwrite experiment outputs.
-   Keep data audit, label audit, feature audit, split audit, and model
    evaluation separate.
-   Each stage should end with a Markdown report and machine-readable
    CSV/JSON evidence.
-   Clearly distinguish verified findings from assumptions and
    historical notes.
