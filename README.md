# Translation Quality Estimation

## 1. Project Overview

This project investigates a reference-free Critical Error Detection (CED) approach for machine translation (MT) quality estimation using the WMT 2020 English-to-German MQM dataset.

The proposed system, **Second Pair of Eyes**, is intended to help translation reviewers prioritize potentially critical MT errors under a limited human-review budget. It is a decision-support tool, not a replacement for human evaluation.

The project evaluates classical machine-learning models and a rule-based heuristic against a random-ranking baseline. The main operational setting considers the top 20% of translations ranked by predicted error risk.

## 2. Dataset and Label Definition

- **Dataset:** WMT 2020 MQM English-to-German (`newstest2020`).
- **Source file:** `mqm_newstest2020_ende.tsv`.
- **Annotation fields:** `system`, `doc`, `doc_id`, `seg_id`, `rater`, `source`, `target`, `category`, and `severity`.
- **Aggregated evaluation examples:** 9,926 system-document-segment examples.
- **Documents:** 130.
- **MT systems:** 7 in the aggregated segment-level evaluation data.

### Operational critical-error label

The project defines a positive label (`y_primary = 1`) when at least two annotators identify a serious error that satisfies the project's operational definition:

- Severity is `Major`, and the category starts with `Accuracy/`; or
- The category is exactly `Non-translation!`.

This definition is specific to this project. It should not be interpreted as a universal definition of critical translation errors or as proof that every negative example is error-free.

The aggregated dataset contains 1,183 positive examples, corresponding to approximately 11.92% of the 9,926 examples.

### Dataset licensing

The exact license and redistribution conditions must be confirmed against the authoritative release or repository documentation for the dataset and its component files. Do not assume that the data are unrestricted or that the license of the annotation data automatically covers all original translation outputs.

## 3. Project Structure

- `mqm_newstest2020_ende.tsv`: Source MQM annotation data.
- `data/`: Official segment and document alignment mapping, including `details/en-de.txt`.
- `original_outputs/`: Raw MT system translation outputs.
- `src/`: Dataset processing, splitting, baseline training, evaluation, and validation scripts.
- `analysis/`: Data-quality and MQM error-analysis scripts.
- `experiments/`: Sensitivity analysis and system-identity experiments.
- `results/week10/`: Week 10 experimental outputs and audit artifacts.
- `results/week11/`: Week 11 MQM error-analysis scripts, 10-case qualitative audits, and neighbor-segment inspection outputs.

Important result directories include:

- `results/week10/locked_split/`: Split snapshot, document assignments, manifest, and QA report.
- `results/week10/baseline_results/`: Development-set baseline results.
- `results/week10/ablation_dev/`: Development-set feature ablation results.
- `results/week10/test_evaluation/`: Test predictions, metrics, confidence intervals, and audit notes.
- `results/week10/error_analysis_dev/`: Development-set error-analysis outputs.
- `results/week10/model_data/`: Prepared train, development, and test data.
- `results/week10/logs/`: Existing audit and data-quality logs.
- `results/week11/error_analysis_dev/`: Week 11 Dev top-20% MQM audit, status summary, and 10-case deep-dive analyses.

## 4. Data Splitting and Reproducibility

The current Week 10 split snapshot contains:

| Split     | Documents | Segment examples |
| --------- | --------: | ---------------: |
| Train     |        90 |            6,797 |
| Dev       |        20 |            1,554 |
| Test      |        20 |            1,575 |
| **Total** |   **130** |        **9,926** |

The split is document-based: examples from the same document must not occur in multiple splits. The current QA checks report no document overlap, no duplicate `system`/`doc`/`seg_id` keys, and no missing required values in the validated segment data.

The locked-split artifacts are stored in `results/week10/locked_split/`. The recorded SHA-256 hash for the split source and snapshot is:

`780cd9f0b2b32042ad95f98e67318c03814fbe895e1f0ef8755da847e8d287ab`

The snapshot has been validated against the current split source. Its recorded status is `candidate_locked`; this establishes consistency between the stored artifacts, but does not independently prove that the split was regenerated from the original raw data or that Test was never examined during earlier development.

### Reproducibility principles

- Keep the original dataset unchanged.
- Run scripts from the project root unless otherwise specified.
- Preserve the split snapshot, predictions, metrics, manifests, and audit notes.
- Fit learned preprocessing components on Train only; evaluate model choices on Dev.
- Use Test for final evaluation and avoid further model selection based on Test results.
- Record seeds, input files, configurations, and output paths for new experiments.

## 5. Models and Baselines

The current Week 10 comparison includes:

1. **Random ranking:** Ranks examples randomly.
2. **Heuristic Rules:** Assigns higher risk scores to selected surface anomalies, including empty targets, extreme source-target length ratios, digit discrepancies, and repeated target words.
3. **Logistic Regression:** Uses TF-IDF representations of source and target text together with 12 surface features.
4. **Linear SVM:** Uses the same general feature representation as Logistic Regression.

The classical machine-learning models use balanced class weights. TF-IDF vectorizers and feature scaling are fitted using Train data, while Dev is used for development-set comparisons.

### Random-baseline conventions

The development-set Random baseline averages 100 random rankings, using seeds 42–141, and reports the sample standard deviation.

The Test Random baseline uses one random ranking with seed `20261026`. Test uncertainty is also estimated using paired document-cluster bootstrap resampling, but this does not turn the single random ranking into an average of 100 rankings.

These different conventions must be reported explicitly. The Dev and Test Random results are not directly comparable as if they used identical random-baseline procedures.

## 6. Development-Set Feature Ablation

Three Logistic Regression configurations were evaluated on Dev:

| Configuration  | PR-AUC | Precision@20% | Recall@20% | Lift@20% | MCC@20% |
| -------------- | -----: | ------------: | ---------: | -------: | ------: |
| LR_Base        | 0.1961 |        0.2026 |     0.2890 |   1.4440 |  0.0897 |
| LR_Plus_System | 0.1991 |        0.1961 |     0.2798 |   1.3982 |  0.0805 |
| System_Only    | 0.1568 |        0.1768 |     0.2523 |   1.2607 |  0.0527 |

The evaluation budget is 311 examples, corresponding to approximately 20% of the 1,554 Dev examples.

Adding MT-system identity slightly increases PR-AUC but reduces precision, recall, lift, and MCC at the fixed review budget. The system-only configuration performs worse than the base model across these reported metrics.

Based on the current Dev point estimates and the project's prioritization objective, **LR_Base is retained as the main configuration**. These comparisons are descriptive; no confidence intervals or statistical significance claims are established for this ablation.

## 7. Test-Set Evaluation

The locked Test set contains 1,575 examples from 20 documents, including 162 positive examples. The positive prevalence is approximately 10.29%. At a 20% review budget, 315 examples are selected.

| Model               | PR-AUC | Precision@20% | Recall@20% | Lift@20% | MCC@20% |
| ------------------- | -----: | ------------: | ---------: | -------: | ------: |
| Random              | 0.1091 |        0.1016 |     0.1975 |   0.9877 | -0.0021 |
| Heuristic Rules     | 0.1391 |        0.1587 |     0.3086 |   1.5432 |  0.0920 |
| Logistic Regression | 0.1971 |        0.1619 |     0.3148 |   1.5741 |  0.0972 |
| Linear SVM          | 0.1676 |        0.1206 |     0.2346 |   1.1728 |  0.0293 |

### Interpretation

Logistic Regression achieves the highest PR-AUC among the reported Test configurations. Its PR-AUC difference from Heuristic Rules is approximately `+0.0580`, with a paired document-cluster bootstrap 95% confidence interval of `[0.0151, 0.1232]`, which excludes zero.

However, the operational differences at the fixed 20% review budget are much smaller:

- Logistic Regression identifies 51 positive examples in the top 315.
- Heuristic Rules identifies 50 positive examples in the top 315.
- The paired confidence intervals for the reported fixed-budget differences include zero.

Therefore, the results support a higher PR-AUC for Logistic Regression relative to the heuristic on this Test evaluation, but **do not establish clear operational superiority at the fixed 20% review budget**.

## 8. Uncertainty Estimation

Test uncertainty is estimated using 1,000 paired document-cluster bootstrap replicates, with seed `20261027`.

Documents are resampled as clusters so that examples from a sampled document remain together. Paired model comparisons use the same sampled document clusters for both models.

The bootstrap intervals describe uncertainty under this resampling procedure. They do not eliminate limitations arising from the finite number of Test documents, the operational label definition, annotation disagreement, or possible prior exposure to Test during project development.

## 9. Development-Set Error Analysis

The Dev error analysis examines examples ranked in the top 20% by `LR_Base` that received zero votes meeting the operational serious-error criteria.

- Top-ranked Dev examples: 311.
- Examples with zero serious votes: 180.
- Selected segment keys with matching MQM annotations after target normalization: 180.
- Matched annotation rows: 893.
- Candidate annotation rows not matched after normalization: 66.

Normalization removes `<v>` markup, applies Unicode NFKC normalization, and collapses whitespace.

The matched annotation rows include Minor, No-error, Neutral, and one Major annotation. The Major annotation is `Style/Awkward`, which falls outside the project's positive-label definition.

These results demonstrate that a segment can receive zero votes meeting the operational critical-error criteria while still having other MQM annotations. Therefore, zero serious votes must not be interpreted as proof that a translation is error-free. Annotation-row counts must also not be treated as independent segment counts.

The analysis outputs are stored in `results/week10/error_analysis_dev/`.

## 10. Week 11 Qualitative Error Analysis and MQM Audit

Week 11 extends the Dev error analysis through a strict target-matching audit and a focused qualitative examination of ten high-ranked non-critical predictions. The analysis uses the existing Dev predictions and does not involve model retraining or Test-set case selection.

### 10.1. Strict MQM Status Audit of 180 Zero-Vote Segments

The audit examined 180 Dev segments ranked in the top 20% by `LR_Base` that had zero operational serious votes (`serious_votes = 0`, `y_primary = 0`).

A total of 959 candidate annotation rows were retrieved. After target normalization and matching:

- Matched annotation rows: 893.
- Unmatched annotation rows: 66 (6.88% of candidate rows).
- Unmatched segment keys: 0.

The strict target-matched status distribution is:

| MQM Error Status      | Segment Count | Percentage  |
| :-------------------- | :-----------: | :---------: |
| Minor Error only      |      149      |   82.78%    |
| No MQM Error Recorded |      30       |   16.67%    |
| Minor and Major Error |       1       |    0.56%    |
| **Total**             |    **180**    | **100.00%** |

Thus, 150/180 segments (83.33%) had at least one matched non-critical MQM error annotation. This does not mean that all 150 segments contain critical errors under the project's operational label definition.

The audit identified annotator disagreement in 77/180 segments (42.78%). Rater coverage was not uniform: 163 segments had three raters, 14 had two raters, and 3 had one rater. Therefore, the 30 segments with no MQM error recorded must not be described as unanimous three-rater No-error cases.

For comparison, the earlier broad segment-key aggregation produced 149 Minor-only, 29 No-error, and 2 Minor-and-Major cases, with 78 segments showing disagreement. These broad counts are not the primary results because the strict target-matched audit provides a more conservative basis for interpreting the annotations.

The 66 unmatched annotation rows represent row-level target mismatches, not 66 unmatched segments. All 180 selected segment keys had at least one matched annotation.

### 10.2. Ten-Case Qualitative Audit

Ten high-ranked Dev examples were selected from `LR_Base` predictions. All ten had `y_primary = 0`; they are therefore described as high-ranked non-critical cases or zero-vote cases, rather than confirmed false positives.

The audit produced the following evidence:

- Ten selected cases.
- 47 candidate MQM annotation rows.
- 42 target-matched annotation rows.
- 5 target-unmatched annotation rows.
- All ten cases had at least one matched annotation.
- All ten cases had zero recomputed serious votes.
- The ten cases represent five unique source segments across four documents.

Six of the ten cases (Cases 3, 4, 6, 7, 8, and 9) correspond to different MT systems translating the same source segment. They must not be interpreted as six independent source-level examples.

Two cases illustrate why MQM category and target matching matter:

1. **Online-B, abcnews, document 5, segment 1317:** The case had 11 candidate annotation rows, of which 6 matched and 5 did not. A Major annotation occurred among the unmatched rows; the matched annotations were Minor. The unmatched Major annotation is therefore not used as evidence of a matched critical error for this case.
2. **eTranslation, standard.co.uk, document 1, segment 1386:** The three candidate annotation rows matched. The Major annotation was categorized as `Style/Awkward`, which is outside the project's operational critical-error categories.

The cases illustrate that high model rankings can occur in examples with non-critical MQM annotations, annotation mismatches, and repeated source content across MT systems. A Major severity label alone does not establish a positive operational label; category, target matching, and the multi-rater rule also matter.

This is a focused, non-random sample of zero-vote Dev cases. The qualitative interpretations were produced by the project team and are not expert adjudications. No positive-label cases were included in this ten-case sample. The findings therefore do not establish how the model behaves across all error types or all critical-error cases.

The current audit outputs are stored in `results/week11/error_analysis_dev/current_10_case_analysis/`.

### 10.3. Interpretation

The quantitative and qualitative audits support three cautious conclusions:

- Zero operational serious votes do not imply that a translation has no MQM annotations or no translation-quality issues.
- MQM severity must be interpreted together with category, target matching, and annotator agreement.
- A ranking model may assign high scores to examples with non-critical defects. This is relevant to the intended review-prioritization workflow, but the present analysis does not establish that every high-ranked case is a critical error or that the model is operationally superior at the fixed review budget.

The analysis is limited by the non-random selection of cases, the small number of unique source segments, repeated translations of the same source segment across systems, annotation mismatches, and the absence of positive cases in the ten-case qualitative sample.

## 11. Limitations

- **Operational label:** The positive label is derived from MQM categories, severity, and annotator agreement. It is an operational definition, not universal ground truth.
- **Annotation uncertainty:** Annotator disagreement and target-matching limitations affect the interpretation of MQM labels. Zero serious votes must not be interpreted as proof of error-free translation.
- **Class imbalance:** The positive class is a minority of the dataset. Ranking-oriented metrics such as PR-AUC, Recall@20%, Precision@20%, and Lift@20% are therefore reported alongside other metrics.
- **Test sample size:** The Test set contains 20 documents. Document-cluster bootstrap intervals may consequently be wide and should be interpreted cautiously.
- **Model comparison:** Logistic Regression achieves the highest Test PR-AUC among the evaluated approaches. However, the paired document-cluster bootstrap confidence intervals for the differences in the top-20% operational metrics include zero. The results do not establish clear operational superiority at the fixed review budget.
- **Ablation scope:** System-identity ablation results are Dev point estimates and do not establish statistical significance or generalization to unseen MT systems.
- **Random baseline protocol:** The Dev Random baseline is averaged over 100 seeds (42–141), whereas the Test Random baseline uses a single seed (20261026). Their values should not be interpreted as directly equivalent estimates.
- **Test exposure:** The Test set is recorded as `candidate_locked`. The available verification confirms consistency of stored split artifacts, hashes, and document assignments; it does not establish that Test results were never inspected during earlier project development.
- **Domain scope:** The experiments use WMT 2020 English-to-German data from seven MT systems. Generalization to other language pairs, datasets, domains, or unseen systems has not been established.
- **Qualitative analysis:** The ten-case analysis is non-random, contains only zero-vote cases, and includes repeated source content across systems. The interpretations are project-team assessments rather than expert adjudication.
- **Reproducibility scope:** The reproduction checks were performed in a separate sandbox on the same machine, not on an independently configured computer or operating system.
- **Ablation provenance:** The ablation outputs were rerun and their contents matched the supplied results, but the provenance of separately stored copies is not independently established.
- **Licensing:** The repository-level Apache 2.0 license must not be interpreted as automatically granting unrestricted redistribution rights for every third-party dataset component. Dataset-specific terms should be checked before redistribution.

## 12. Main Artifacts

Key files for reproducing and auditing the project results include:

### Week 10 Artifacts

- `results/week10/locked_split/manifest.json`
- `results/week10/locked_split/qa_report.txt`
- `results/week10/locked_split/document_assignments.csv`
- `results/week10/baseline_results/dev_baseline_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_predictions.csv`
- `results/week10/test_evaluation/test_predictions.csv`
- `results/week10/test_evaluation/test_point_metrics.csv`
- `results/week10/test_evaluation/test_metrics_with_ci.csv`
- `results/week10/test_evaluation/paired_difference_ci.csv`
- `results/week10/test_evaluation/test_audit_notes.md`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_segments.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_annotations.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_summary.csv`
- `results/week10/error_analysis_dev/dev_error_analysis_manifest.json`

### Week 11 Artifacts

**Quantitative Dev error analysis**

- `results/week11/error_analysis_dev/dev_top20_error_analysis.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_summary.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_status_summary.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_rater_detail.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_unmatched.csv`

**Current ten-case analysis**

- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_cases.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_report.md`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_summary.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_matched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_unmatched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_qualitative_evidence.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_evidence_manifest.csv`

**Research and verification reports**

- `reports/G4_1_qualitative_error_analysis.md`
- `reports/G4_2_error_analysis_synthesis.md`
- `reports/G3_6_bao_cao_tong_ket_tinh_tai_lap.md`
- `reports/strict_split_verification_20261104.txt`

The strict split verification log records 37 successful checks, including source and snapshot hash consistency, split-file integrity, document assignments, and the absence of document overlap across Train, Dev, and Test.

The current ten-case directory is the primary source for the Week 11 qualitative case analysis. Older directories such as `final_10_case_analysis/` and `mqm_10_cases_audit/` are retained as historical or supplementary audit artifacts and should not be treated as substitutes for the current analysis.

File availability may depend on the current working tree. The verification log establishes consistency of the checked artifacts, not a clean-machine reproduction or proof that the Test set was never inspected.
