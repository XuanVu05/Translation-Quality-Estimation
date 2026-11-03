# G2 – Experimental Evaluation and Model Comparison

**Project:** Second Pair of Eyes – Reference-Free Critical Error Detection for English→German Machine Translation  
**Dataset:** WMT 2020 MQM English→German (`newstest2020`)  
**Evaluation phase:** Week 10  
**Status:** Completed with reporting caveats  
**Prepared from:** `dev_baseline_metrics.csv`, `dev_ablation_metrics.csv`, `test_point_metrics.csv`, `test_metrics_with_ci.csv`, `paired_difference_ci.csv`, and `test_predictions.csv`.

---

## 1. Purpose and scope of G2

G2 evaluates whether lightweight, CPU-feasible machine-learning models can rank machine-translated segments by their likelihood of containing a critical translation error, so that a human reviewer can inspect a limited subset first.

The experimental comparison includes:

1. Random ranking as a reference point.
2. A rule-based heuristic using source/target text characteristics.
3. Logistic Regression using TF-IDF and surface features.
4. Linear Support Vector Machine (Linear SVM) using the same base feature representation.
5. An ablation study examining the contribution of MT-system identity.

The operational evaluation emphasizes a fixed review budget of 20%. PR-AUC is also reported because it evaluates ranking quality across thresholds and is useful for an imbalanced binary classification problem. Precision@20%, Recall@20%, Lift@20%, and MCC@20% describe performance at the selected review budget.

This report records the supplied experimental outputs. It does not claim that the experiments establish generalization to unseen MT systems or that the model replaces human review.

## 2. Dataset, labels, and split used in evaluation

The model dataset contains 9,926 MT segment-level examples from seven MT systems and 130 documents. The primary label is `y_primary`, constructed from three distinct annotator votes: a segment is labelled Critical (`1`) when at least two annotators cast a serious-error vote; otherwise it is labelled Non-critical (`0`).

The document-level split used for Week 10 is:

| Partition | Rows | Documents | Positive samples |
|---|---:|---:|---:|
| Train | 6,797 | 90 | 803 |
| Dev | 1,554 | 20 | 218 |
| Test | 1,575 | 20 | 162 |
| **Total** | **9,926** | **130** | **1,183** |

Documents, rather than individual segments, are the grouping unit. The split audit found no document overlap between Train, Dev, and Test. The locked split hash recorded in the project audit is:

`780cd9f0b2b32042ad95f8e67318c03814fbe895e1f0ef8755da847e8d287ab`

The Test set contains 162 positive examples among 1,575 rows, giving a prevalence of approximately **10.29%**. Its 20% review budget is 315 segments (the integer cutoff used in the supplied predictions).

## 3. Models and feature configurations

### 3.1 Random ranking

Random assigns a random ranking to examples and provides a non-informative reference point. On Dev, the reported Random metrics are averaged over 100 rankings (seeds 42–141). The reported standard deviations describe variability across those Dev random runs.

On Test, the supplied evaluation uses one random ranking with seed `20261026`. Therefore, the Test Random point estimate and interval should not be interpreted as an average over repeated random rankings. This difference in protocol is a reporting limitation and should be stated explicitly.

### 3.2 Rule-based heuristic

The heuristic produces a ranking score from source/target text characteristics without fitting a supervised classifier. It is a necessary non-random baseline: the learned models must be compared not only with chance but also with a simple, transparent rule-based approach.

The precise heuristic formula should be described in the Methods section from the implementation in the repository. This results report does not infer additional rule details beyond the supplied evaluation outputs.

### 3.3 Logistic Regression and Linear SVM

The base feature representation comprises:

- Separate TF-IDF representations for source and target text.
- Word n-grams with `ngram_range=(1, 2)`.
- `max_features=30,000` for each vectorizer, `min_df=2`, and `sublinear_tf=True`.
- Twelve surface features derived from source and target text.

The twelve surface features recorded in the feature-provenance audit are:

1. Log-transformed source token count.
2. Log-transformed target token count.
3. Target/source token-count ratio.
4. Absolute token-count difference relative to source length.
5. Target/source character-length ratio.
6. Source digit count.
7. Target digit count.
8. Absolute digit-count difference.
9. Target uppercase ratio.
10. Target punctuation/symbol ratio.
11. Repeated-token count in target.
12. Empty-target indicator.

TF-IDF vectorizers and the feature scaler are fitted on the training data only during Dev evaluation, then applied to Dev using `transform`. The inspected baseline implementation does not use document identifiers, segment identifiers, MQM annotations, or labels as input features.

The baseline implementation uses class-weight balancing. The documented model settings are Logistic Regression with `C=1`, `max_iter=2000`, `random_state=42`, and Linear SVM with `C=1`, `max_iter=10000`. The model target is `y_primary`.

### 3.4 System-identity ablation

The ablation compares:

- `LR_Base`: TF-IDF source/target plus twelve surface features.
- `LR_Plus_System`: base features plus one-hot encoded MT-system identity.
- `System_Only`: system identity alone.

The encoder is fitted on Train and applied to Dev. The ablation is a diagnostic experiment: it measures whether system identity adds useful predictive information in this dataset. It does not demonstrate that a model will generalize to previously unseen MT systems.

## 4. Evaluation metrics

Let the top-ranked 20% of segments be the review queue.

- **PR-AUC:** area under the precision-recall curve; summarizes ranking performance over thresholds and is informative under class imbalance.
- **Precision@20%:** proportion of reviewed segments that are Critical.
- **Recall@20%:** proportion of all Critical segments captured within the review queue.
- **Lift@20%:** Precision@20% divided by the positive prevalence in the evaluated partition. A value above 1 indicates enrichment over selecting segments without ranking.
- **MCC@20%:** Matthews correlation coefficient after treating the top-20% queue as predicted positive and the remaining examples as predicted negative.
- **Positive samples in top 20%:** absolute number of Critical segments retrieved within the review budget.

For an operational interpretation, Precision@20% describes the concentration of critical errors in the queue, while Recall@20% describes how much of the total critical-error pool is captured by that queue. Neither metric alone describes all aspects of ranking quality.

## 5. Development-set baseline results

The Dev partition has 1,554 examples and a positive prevalence of **14.03%**. The following values are taken from `dev_baseline_metrics.csv`.

| Model | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% |
|---|---:|---:|---:|---:|---:|
| Random | 0.1435 | 0.1996 | 0.1399 | 1.00 | -0.0005 |
| HeuristicRules | 0.1777 | 0.3303 | **0.2315** | **1.65** | **0.1314** |
| LogisticRegression | **0.1961** | 0.2890 | 0.2026 | 1.44 | **0.0897** |
| LinearSVM | 0.1742 | 0.2752 | 0.1929 | 1.38 | 0.0758 |

Random results are means over 100 rankings; the corresponding standard deviations are in the source CSV. The heuristic and supervised model values are deterministic point estimates in the supplied file.

### 5.1 Interpretation

Logistic Regression achieves the highest Dev PR-AUC (0.1961), indicating the strongest overall precision-recall ranking among the listed methods on this partition. However, the heuristic has the highest Precision@20%, Recall@20%, and Lift@20%.

This distinction matters for the research objective. The objective is not simply to maximize a threshold-independent score; it is to prioritize segments under a fixed review budget. On Dev, the rule-based heuristic is more effective at the specific 20% cutoff, even though Logistic Regression has higher PR-AUC.

Linear SVM is below Logistic Regression on all five listed Dev metrics. These results support carrying Logistic Regression forward as the main learned model, while retaining the heuristic as a serious operational comparator.

## 6. Ablation study on Dev

The ablation outputs report 6,797 training rows and 1,554 Dev rows for each configuration. The base and system-augmented representations contain 58,150 and 58,157 features respectively.

| Configuration | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% | Critical in top 20% |
|---|---:|---:|---:|---:|---:|---:|
| LR_Base | 0.1961 | **0.2890** | **0.2026** | **1.4440** | **0.0897** | 63 |
| LR_Plus_System | **0.1991** | 0.2798 | 0.1961 | 1.3982 | 0.0805 | 61 |
| System_Only | 0.1568 | 0.2523 | 0.1768 | 1.2607 | 0.0527 | 55 |

### 6.1 Interpretation

Adding system identity produces a small PR-AUC increase, from 0.1961 to 0.1991. However, the system-augmented model performs worse on Recall@20%, Precision@20%, Lift@20%, and MCC@20%. It retrieves 61 Critical examples in the top 20%, compared with 63 for the base model.

The System_Only model is weaker than the text-based configurations, although it performs above the random reference on several measures. This indicates that system identity contains some dataset-specific signal, but it is not a substitute for source/target text features.

The ablation does not support retaining system identity as a default feature for the primary model when the operational target is top-20% review effectiveness. It also warns against claiming generalization to unseen MT systems: the system-identity feature explicitly relies on known system categories.

## 7. Final Test-set results

The Test partition contains 1,575 examples, including 162 Critical examples. The top-20% queue contains 315 segments. Values below are from `test_point_metrics.csv`; the corresponding confidence intervals are recorded in `test_metrics_with_ci.csv`.

| Model | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% |
|---|---:|---:|---:|---:|---:|
| Random | 0.1091 | 0.1975 | 0.1016 | 0.99 | -0.0021 |
| HeuristicRules | 0.1391 | 0.3086 | 0.1587 | 1.54 | 0.0920 |
| LogisticRegression | **0.1971** | **0.3148** | **0.1619** | **1.57** | **0.0972** |
| LinearSVM | 0.1676 | 0.2346 | 0.1206 | 1.17 | 0.0293 |

### 7.1 Operational interpretation at the 20% review budget

The Test prediction file contains 1,575 rows and four ranking-score columns (Random, HeuristicRules, LogisticRegression, and LinearSVM). Recomputing the top-315 selections from the prediction scores gives:

| Model | Critical examples in top 315 | Precision@20% |
|---|---:|---:|
| Random | 32 | 10.16% |
| HeuristicRules | 50 | 15.87% |
| LogisticRegression | **51** | **16.19%** |
| LinearSVM | 38 | 12.06% |

Logistic Regression retrieves 51 of the 162 Critical examples, compared with 50 for the heuristic. Thus, the absolute operational gain is one additional Critical segment in a queue of 315 items. The relative improvement in PR-AUC is more substantial than the difference in the fixed-budget queue.

The result supports a nuanced conclusion: Logistic Regression has the best point estimates on the Test metrics shown, but its practical advantage over the heuristic at the 20% cutoff is modest.

## 8. Confidence intervals and paired document-cluster bootstrap

The Test evaluation includes 95% confidence intervals. The paired comparison file reports bootstrap confidence intervals for the difference between each learned model and the heuristic. The bootstrap uses documents as clusters, retaining the dependence among segments from the same document. The project record specifies 1,000 bootstrap replicates and seed `20261027`.

### 8.1 Test estimates and 95% confidence intervals

| Model | Metric | Estimate | 95% CI |
|---|---|---:|---:|
| Random | PR-AUC | 0.1091 | [0.0769, 0.1550] |
| HeuristicRules | PR-AUC | 0.1391 | [0.0749, 0.2125] |
| LogisticRegression | PR-AUC | 0.1971 | [0.1220, 0.2833] |
| LinearSVM | PR-AUC | 0.1676 | [0.1055, 0.2564] |
| Random | Recall@20% | 0.1975 | [0.1515, 0.2655] |
| HeuristicRules | Recall@20% | 0.3086 | [0.1619, 0.4077] |
| LogisticRegression | Recall@20% | 0.3148 | [0.2215, 0.4202] |
| LinearSVM | Recall@20% | 0.2346 | [0.1743, 0.3711] |
| Random | Precision@20% | 0.1016 | [0.0653, 0.1452] |
| HeuristicRules | Precision@20% | 0.1587 | [0.0602, 0.2573] |
| LogisticRegression | Precision@20% | 0.1619 | [0.0915, 0.2500] |
| LinearSVM | Precision@20% | 0.1206 | [0.0686, 0.2167] |
| Random | Lift@20% | 0.9877 | [0.7574, 1.3265] |
| HeuristicRules | Lift@20% | 1.5432 | [0.8097, 2.0345] |
| LogisticRegression | Lift@20% | 1.5741 | [1.1061, 2.0983] |
| LinearSVM | Lift@20% | 1.1728 | [0.8691, 1.8519] |
| Random | MCC@20% | -0.0021 | [-0.0443, 0.0499] |
| HeuristicRules | MCC@20% | 0.0920 | [-0.0284, 0.1860] |
| LogisticRegression | MCC@20% | 0.0972 | [0.0176, 0.1880] |
| LinearSVM | MCC@20% | 0.0293 | [-0.0235, 0.1430] |

The complete source file also contains Lift@20% and MCC@20% intervals. The table above selects PR-AUC and the two principal fixed-budget measures for readability; all metrics remain available in the CSV.

### 8.2 Paired differences: learned models versus heuristic

Difference is defined as **model minus HeuristicRules**. A confidence interval that excludes zero indicates evidence of a non-zero difference under the specified paired cluster-bootstrap procedure.

| Comparison | Metric | Difference | 95% CI | Interpretation |
|---|---|---:|---:|---|
| LogisticRegression − HeuristicRules | PR-AUC | +0.0580 | [0.0151, 0.1232] | CI excludes zero; positive difference |
| LogisticRegression − HeuristicRules | Recall@20% | +0.0062 | [-0.0880, 0.1818] | CI includes zero |
| LogisticRegression − HeuristicRules | Precision@20% | +0.0032 | [-0.0525, 0.0820] | CI includes zero |
| LogisticRegression − HeuristicRules | Lift@20% | +0.0309 | [-0.4393, 0.9075] | CI includes zero |
| LogisticRegression − HeuristicRules | MCC@20% | +0.0052 | [-0.0798, 0.1376] | CI includes zero |
| LinearSVM − HeuristicRules | PR-AUC | +0.0285 | [-0.0095, 0.0926] | CI includes zero |
| LinearSVM − HeuristicRules | Recall@20% | -0.0741 | [-0.1361, 0.1243] | CI includes zero |
| LinearSVM − HeuristicRules | Precision@20% | -0.0381 | [-0.0831, 0.0556] | CI includes zero |
| LinearSVM − HeuristicRules | Lift@20% | -0.3704 | [-0.6792, 0.6199] | CI includes zero |
| LinearSVM − HeuristicRules | MCC@20% | -0.0627 | [-0.1221, 0.0998] | CI includes zero |

### 8.3 Interpretation and limits

The paired bootstrap supports a positive difference in PR-AUC between Logistic Regression and the heuristic because the reported 95% interval is entirely above zero. For the fixed-budget measures (Recall@20%, Precision@20%, Lift@20%, and MCC@20%), the intervals include zero. The experiment therefore does **not** establish that Logistic Regression is superior to the heuristic in operational top-20% review performance.

For Linear SVM, all paired-difference intervals shown include zero. Its point estimates are generally lower than Logistic Regression and the heuristic, but the supplied bootstrap results do not establish a non-zero difference from the heuristic for these metrics.

These intervals should not be described as proof that the models are equivalent. An interval containing zero means that the current experiment does not provide sufficient evidence of a non-zero difference at the interval level; it does not demonstrate equivalence.

## 9. Prediction-file integrity checks

The supplied `test_predictions.csv` was checked independently.

| Check | Result |
|---|---:|
| Number of rows | 1,575 |
| Number of columns | 11 |
| Distinct documents | 20 |
| Distinct MT systems | 7 |
| Positive labels (`y_primary=1`) | 162 |
| Negative labels (`y_primary=0`) | 1,413 |
| Missing values | 0 |
| Duplicate segment keys (`system`, `doc`, `doc_id`, `seg_id`) | 0 |
| Top-20% queue size | 315 |

The top-315 results reconstructed from the prediction scores match the reported point metrics. This provides an internal consistency check between the prediction-level output and the aggregate Test metrics.

The prediction file contains identifiers, source/target text, the primary label, and model scores for traceability. Its presence in the evaluation output does not mean that identifiers or labels were used as model input features. The feature-provenance audit records that model features are derived from source/target text, with system identity used only in the dedicated ablation.

## 10. Threats to validity and reporting caveats

### 10.1 Different number of random rankings on Dev and Test

The Dev Random baseline averages 100 random rankings, whereas the Test Random baseline uses one random ranking (seed `20261026`). This does not invalidate the learned-model predictions, but it makes the random-baseline uncertainty treatment inconsistent across partitions. State this limitation explicitly. If computationally feasible, rerun the Test Random baseline over 100 fixed, documented seeds and report its mean and standard deviation. Do not replace the existing Test result silently; preserve both the original and supplementary result.

### 10.2 Limited operational difference between Logistic Regression and heuristic

Although Logistic Regression has the highest Test point estimates, it retrieves only one more Critical segment than the heuristic in the top 315. The paired bootstrap intervals for top-20% metrics include zero. Avoid claiming a demonstrated practical or statistically reliable top-20% advantage.

### 10.3 Generalization scope

The evaluation uses a document-disjoint split from the same WMT 2020 English→German dataset and the same seven MT systems. It supports claims about held-out documents within this dataset. It does not by itself establish transfer to other language pairs, years, domains, annotation schemes, or unseen MT systems.

### 10.4 Label uncertainty

The binary target is derived from three annotators and a two-vote threshold. This operationalizes the project's definition of Critical Error but does not eliminate disagreement or subjectivity in MQM annotation. The threshold sensitivity and qualitative error analysis should be discussed elsewhere in the report.

### 10.5 Confidence intervals

The bootstrap resamples documents as clusters, which is more appropriate than treating all segments as independent when segments within a document may be correlated. However, there are only 20 Test documents. The uncertainty estimates should therefore be interpreted with the limited number of independent document clusters in mind.

### 10.6 System-identity ablation

The system-identity ablation is informative about dataset-specific system effects. Since the evaluation split contains the same system categories across partitions, it is not an unseen-system generalization experiment.

## 11. Main findings

The experiments support the following findings:

1. The rule-based heuristic is a meaningful baseline and performs substantially better than the random ranking at the 20% review budget.
2. Logistic Regression achieves the strongest overall ranking performance among the tested methods, with the highest Dev and Test PR-AUC.
3. Linear SVM does not outperform Logistic Regression or the heuristic in the supplied point estimates.
4. Adding MT-system identity slightly increases PR-AUC on Dev but reduces all reported top-20% measures relative to the base Logistic Regression model.
5. On Test, Logistic Regression retrieves 51 Critical examples in the top 315, compared with 50 for the heuristic. The operational gain at this cutoff is therefore small.
6. Paired document-cluster bootstrap supports a positive PR-AUC difference between Logistic Regression and the heuristic, but does not establish a difference in the fixed-budget top-20% metrics.
7. The results justify a decision-support ranking system for prioritizing human review, not an autonomous translation-quality judge.

## 12. Recommended conclusion for the research report

> The experimental results show that a lightweight Logistic Regression model based on source/target TF-IDF representations and surface-level linguistic features can achieve stronger overall ranking performance than a rule-based heuristic on the held-out WMT 2020 English→German test documents, as reflected by PR-AUC. However, under the operational constraint of reviewing only the top 20% of segments, the improvement is marginal: Logistic Regression identifies 51 critical segments compared with 50 for the heuristic among 315 reviewed segments. Paired document-cluster bootstrap intervals support a positive PR-AUC difference but do not establish a reliable advantage in Recall@20%, Precision@20%, Lift@20%, or MCC@20%. The system should therefore be presented as a lightweight decision-support mechanism that helps prioritize human inspection, rather than as a replacement for human evaluation or as evidence of generalization to unseen MT systems.

## 13. G2 completion checklist

| Requirement | Status | Evidence / note |
|---|---|---|
| Random baseline | Completed with caveat | 100 rankings on Dev; one ranking on Test |
| Rule-based baseline | Completed | Dev and Test results available |
| Logistic Regression | Completed | Dev and Test results available |
| Linear SVM | Completed | Dev and Test results available |
| Ablation study | Completed | Base, Plus System, System Only |
| Held-out Test evaluation | Completed | 1,575 predictions |
| Confidence intervals | Completed | Test metric CI file |
| Paired cluster bootstrap | Completed | Model-versus-heuristic differences |
| Prediction/metric consistency | Checked | Top-315 counts reproduce point metrics |
| Reporting caveats | Documented | See Section 10 |

**Overall G2 status: Completed with reporting caveats.**

Before final submission, preserve the six original CSV outputs and the exact scripts/configuration that generated them. If the supplementary 100-run Test Random baseline is performed, save it as a separate output and document the additional experiment without overwriting the original result.

---

## Appendix A. Source output files

This report was prepared from the following files:

- `dev_baseline_metrics.csv`
- `dev_ablation_metrics.csv`
- `test_point_metrics.csv`
- `test_metrics_with_ci.csv`
- `paired_difference_ci.csv`
- `test_predictions.csv`

The report should be stored in the project at:

`reports/G2_experimental_evaluation_report.md`
