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

Important result directories include:

- `results/week10/locked_split/`: Split snapshot, document assignments, manifest, and QA report.
- `results/week10/baseline_results/`: Development-set baseline results.
- `results/week10/ablation_dev/`: Development-set feature ablation results.
- `results/week10/test_evaluation/`: Test predictions, metrics, confidence intervals, and audit notes.
- `results/week10/error_analysis_dev/`: Development-set error-analysis outputs.
- `results/week10/model_data/`: Prepared train, development, and test data.
- `results/week10/logs/`: Existing audit and data-quality logs.

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

The matching annotation rows include Minor, No-error, Neutral, and one Major annotation. The Major annotation is `Style/Awkward`, which falls outside the project's positive-label definition and was not supported by two annotators at Major severity.

These results illustrate that a segment can receive no votes meeting the operational critical-error criteria while still having other MQM annotations. Consequently, zero serious votes must not be interpreted as proof that a translation is error-free. Annotation-row counts also must not be treated as independent segment counts.

The analysis outputs are stored in `results/week10/error_analysis_dev/`.

## 10. Limitations

- The positive label is an operational definition derived from MQM categories, severity, and annotator agreement; it is not universal ground truth.
- Class imbalance affects model evaluation and motivates the use of ranking-oriented metrics such as PR-AUC, Recall@20%, Precision@20%, and Lift@20%.
- The Test set contains only 20 documents, so document-cluster uncertainty estimates may be wide.
- The ablation results are Dev point estimates and do not establish statistical significance.
- Logistic Regression's higher Test PR-AUC does not establish a clear improvement in positive-error discovery at the fixed review budget.
- The Dev and Test Random baselines use different random-ranking conventions.
- Historical logs do not establish conclusively whether Test results were examined during every earlier stage of model development.
- Dataset licensing and redistribution permissions must be verified from the authoritative dataset documentation before redistribution.

## 11. Main Artifacts

Key files for reproducing and auditing the Week 10 results include:

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

File availability may depend on the current working tree. Generated artifacts should be checked before claiming that a particular experiment is fully reproducible from a clean checkout.
