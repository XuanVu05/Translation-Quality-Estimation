# G4.2 – Error Analysis Synthesis

## 1. Purpose and Scope

This report synthesizes the quantitative and qualitative error-analysis findings from the WMT 2020 MQM English–German dataset. It connects the experimental results from Week 10 with the qualitative analysis from Week 11 to examine the limitations of reference-free Critical Error Detection (CED).

The analysis focuses on five aspects:

1. False-positive taxonomy among high-priority Dev segments.
2. MQM annotation uncertainty and target-matching limitations.
3. Model limitations and ablation findings.
4. Operational implications under a fixed 20% review budget.
5. Threats to validity and directions for further evaluation.

The analysis does not treat every segment selected by the ranking models as an actual translation error. In particular, a segment containing a Minor MQM annotation is not necessarily a Critical Error under the project's label definition.

## 2. False-Positive Taxonomy

### 2.1. Analysis population

The Dev set contains 1,554 segments. The top 20% review budget corresponds to 311 segments. Among these, 180 segments received zero serious votes and were selected for further investigation.

All 180 selected segments were matched to MQM segment keys. At the segment-key level, each segment had annotations from three distinct raters, resulting in 540 segment-rater records.

After strict target matching, 893 of the 959 candidate annotation rows were retained, while 66 rows referring to alternative target variants were excluded from the primary analysis. The remaining rater coverage was: 163 segments with three raters, 14 segments with two raters, and 3 segments with one rater.

The primary analysis distinguishes between segment-key matching and strict target matching. These are not interchangeable: a segment key may match while some annotation rows refer to a different target variant.

### 2.2. Segment-level MQM status

The initial segment-key-based analysis produced the following distribution:

| MQM status            | Segments | Percentage |
| --------------------- | -------: | ---------: |
| Minor_Error           |      149 |     82.78% |
| No_MQM_Error_Recorded |       29 |     16.11% |
| Minor_and_Major_Error |        2 |      1.11% |
| **Total**             |  **180** |   **100%** |

After strict target matching, the distribution changed:

| MQM status            | Segments | Percentage |
| --------------------- | -------: | ---------: |
| Minor_Error           |      149 |     82.78% |
| No_MQM_Error_Recorded |       30 |     16.67% |
| Minor_and_Major_Error |        1 |      0.56% |
| **Total**             |  **180** |   **100%** |

The strict target-matched distribution is used as the primary interpretation in this report because it more closely associates annotations with the exact translation being evaluated. The segment-key-based distribution is retained as an audit comparison.

The main finding is that most high-priority zero-vote segments still contain Minor MQM annotations. Therefore, these cases should not automatically be interpreted as completely error-free translations. Rather, they indicate that the model often prioritizes segments containing annotated errors that do not satisfy the project's Critical Error definition.

The 30 segments with no MQM error recorded after strict target matching represent false positives with respect to the observed binary label. However, the absence of a recorded MQM error does not prove that a translation is objectively error-free.

### 2.3. Major but non-critical annotations

Two segments contained Major annotations in the segment-key-based analysis:

- Online-B.1590, abcnews.363994, document 5, segment 1317.
- eTranslation.737, standard.co.uk.14516, document 1, segment 1386.

Their annotation evidence differs.

For the Online-B segment, 11 candidate annotation rows were identified, but only 6 matched the evaluated target. The Major annotation was among the unmatched rows. After strict target matching, the segment retained Minor annotations but no matched Major annotation.

For the eTranslation segment, all 3 annotation rows matched the evaluated target. Its Major annotation belonged to Style/Awkward.

Under the project's label definition, Major severity alone is insufficient to establish a Critical Error. The category must also satisfy the specified critical-category rule, and at least two distinct annotators must provide a serious vote. Style/Awkward does not meet the project's critical-category requirement.

These cases demonstrate why severity, category, target matching, and annotator voting must be considered together rather than treating every Major annotation as a positive label.

### 2.4. Annotator disagreement

Under strict target matching, 77 of the 180 selected segments exhibited annotator disagreement, corresponding to 42.78%.

The segment-key-based analysis identified 78 segments with disagreement, or 43.33%.

The strict target-matched figure is used as the primary result. The difference reflects the effect of excluding annotation rows that do not match the evaluated target.

This disagreement rate indicates that a substantial subset of high-priority segments has non-uniform annotation evidence. It should not be interpreted as Cohen's Kappa, Krippendorff's Alpha, or another chance-corrected inter-annotator agreement coefficient. It is a segment-level disagreement indicator produced by the analysis procedure.

### 2.5. Annotation-row matching limitations

The broad segment-key-based analysis identified 959 candidate annotation rows for the 180 selected segments.

After strict target matching:

- Target-matched annotation rows: 893.
- Target-unmatched annotation rows: 66.
- Unmatched segment keys: 0.

Thus, all selected segment keys had corresponding MQM annotations, but not every candidate annotation row referred to the exact evaluated target.

The 66 unmatched rows represent 6.88% of the 959 candidate annotation rows. This is a row-level matching rate, not a segment-level unmatched rate.

This distinction is methodologically important. Joining annotations using only system and segment identifiers may associate annotations from alternative target variants with the evaluated translation. Strict target matching reduces this risk.

### 2.6. False-positive taxonomy summary

The findings support the following taxonomy:

| Category                   | Interpretation                                                                                                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Minor-only errors          | The segment contains MQM errors, but they do not satisfy the Critical Error label definition.                                                         |
| No-error recorded          | No MQM error is recorded for the evaluated target. This is a false positive relative to the observed label, not proof of perfect translation quality. |
| Annotator disagreement     | Annotators provide non-uniform judgments, introducing uncertainty into the observed label.                                                            |
| Major but non-critical     | A Major annotation exists, but its category or voting evidence does not satisfy the Critical Error rule.                                              |
| Target-matching limitation | Some candidate annotations refer to a different target variant and must not be attributed to the evaluated translation.                               |

These categories describe different sources of uncertainty and should not be added together as mutually exclusive counts.

## 3. Model Limitations

### 3.1. Logistic Regression

On the held-out Test set, Logistic Regression achieved the highest PR-AUC among the evaluated methods:

| Model              | PR-AUC | Recall@20% | Precision@20% | Lift@20% | MCC@20% |
| ------------------ | -----: | ---------: | ------------: | -------: | ------: |
| Random             | 0.1091 |     0.1975 |        0.1016 |   0.9877 | -0.0021 |
| HeuristicRules     | 0.1391 |     0.3086 |        0.1587 |   1.5432 |  0.0920 |
| LogisticRegression | 0.1971 |     0.3148 |        0.1619 |   1.5741 |  0.0972 |
| LinearSVM          | 0.1676 |     0.2346 |        0.1206 |   1.1728 |  0.0293 |

Logistic Regression provides the strongest overall ranking performance according to PR-AUC. However, its advantage over the heuristic baseline is much smaller when evaluated at the operational review budget.

At the top 20% threshold, Logistic Regression identified 51 Critical Errors, compared with 50 for the heuristic baseline. This is an increase of only one Critical Error among 315 reviewed segments.

The paired document-cluster bootstrap used 1,000 replicates and produced the following Logistic Regression minus Heuristic differences:

| Metric        | Difference | 95% Confidence Interval |
| ------------- | ---------: | ----------------------: |
| PR-AUC        |    +0.0580 |        [0.0151, 0.1232] |
| Recall@20%    |    +0.0062 |       [-0.0880, 0.1818] |
| Precision@20% |    +0.0032 |       [-0.0525, 0.0820] |
| Lift@20%      |    +0.0309 |       [-0.4393, 0.9075] |
| MCC@20%       |    +0.0052 |       [-0.0798, 0.1376] |

Only the PR-AUC confidence interval excludes zero. The intervals for all four top-20% operational metrics include zero.

Consequently, the results support an improvement in overall ranking performance, but do not establish a statistically distinguishable advantage in the operational metrics at the fixed 20% review budget.

### 3.2. Linear SVM

Linear SVM achieved a lower PR-AUC than Logistic Regression and the heuristic baseline. It identified 38 Critical Errors in the top 315 Test segments.

Under the current feature representation and experimental configuration, Linear SVM does not demonstrate a clear operational advantage for prioritizing critical translation errors.

This conclusion is limited to the evaluated dataset and configuration. It should not be generalized to all Linear SVM applications or alternative feature representations.

### 3.3. System identity ablation

The Dev ablation compared three configurations:

| Metric        | LR Base | LR + System | System Only |
| ------------- | ------: | ----------: | ----------: |
| PR-AUC        |  0.1961 |      0.1991 |      0.1568 |
| Recall@20%    |  0.2890 |      0.2798 |      0.2523 |
| Precision@20% |  0.2026 |      0.1961 |      0.1768 |
| Lift@20%      |  1.4440 |      1.3982 |      1.2607 |
| MCC@20%       |  0.0897 |      0.0805 |      0.0527 |

Adding system identity slightly increased PR-AUC, but reduced Recall@20%, Precision@20%, Lift@20%, and MCC@20%.

The System Only configuration performed below LR Base on all five metrics. This suggests that system identity alone is insufficient to provide a strong prioritization signal.

The ablation was conducted on Dev only. Both Train and Dev contained all seven MT systems. Therefore, the results do not establish generalization to previously unseen MT systems.

### 3.4. Class imbalance and label representation

The full model dataset contains 9,926 MT segments:

- Non-critical: 8,743.
- Critical: 1,183.
- Positive rate: 11.92%.

The Test set contains 1,575 segments, including 162 positive segments, corresponding to a prevalence of approximately 10.29%.

This class imbalance makes Accuracy insufficient as the primary evaluation measure. PR-AUC and review-budget metrics are more relevant to the project's ranking objective.

The qualitative analysis also shows that the binary Critical/Non-critical label does not represent the full range of MQM annotation information. Minor errors, Major errors outside the critical-category definition, and annotator disagreement are not fully represented by the binary target.

## 4. Operational Implications

The intended application is a decision-support system that ranks machine-translated segments for human review under a limited review budget.

On Test, the 20% review budget corresponds to 315 of 1,575 segments.

| Ranking method     | Critical Errors in top 315 |
| ------------------ | -------------------------: |
| Random             |                         32 |
| HeuristicRules     |                         50 |
| LogisticRegression |                         51 |
| LinearSVM          |                         38 |

Both Logistic Regression and the heuristic baseline improve over random ranking.

Logistic Regression identifies one additional Critical Error compared with the heuristic baseline. Although Logistic Regression has a higher PR-AUC, this small difference at the operational cutoff does not establish a substantial practical improvement.

The heuristic baseline therefore remains a useful, transparent, and computationally simple reference method. Logistic Regression remains a promising candidate because of its stronger overall PR-AUC, but its operational value requires further validation.

The proposed Second Pair of Eyes system should be used to:

1. Generate a priority queue of segments for human review.
2. Help reviewers allocate limited time toward segments with higher predicted critical-error risk.
3. Provide a decision-support signal rather than an automatic quality judgment.
4. Preserve human responsibility for final translation-quality assessment.

The system should not automatically reject translations or replace professional human evaluation.

## 5. Threats to Validity

### 5.1. Construct validity

The Critical Error label is operationally defined using MQM category, severity, and a minimum of two serious votes from distinct annotators.

This definition provides a reproducible target, but it does not capture every possible interpretation of translation quality. Results are conditional on the project's label definition.

### 5.2. Annotation validity

The strict target-matched analysis found disagreement in 77 of 180 selected zero-vote segments.

This indicates uncertainty in a substantial portion of the qualitative analysis population. The study does not report a chance-corrected inter-annotator agreement coefficient for this subset.

### 5.3. Data-linkage validity

The analysis identified 66 target-unmatched annotation rows among 959 candidate rows. Segment-key matching alone is therefore insufficient to guarantee that every annotation belongs to the exact target being evaluated.

Strict target matching is necessary when interpreting qualitative error evidence.

### 5.4. External validity

The experiments use WMT 2020 English–German data, seven MT systems, and 130 documents.

The results do not establish generalization to other language pairs, domains, datasets, or unseen MT systems.

### 5.5. Statistical validity

The Test set contains only 20 document clusters. Although document-cluster bootstrap is used to account for document-level dependence, the resulting confidence intervals remain broad for several top-20% metrics.

The findings should therefore be interpreted as evidence from a limited held-out evaluation rather than definitive proof of operational superiority.

### 5.6. Random baseline comparability

The Dev random baseline averages 100 rankings, whereas the Test random baseline uses one ranking with seed 20261026.

The random baseline therefore has different levels of Monte Carlo averaging across the two evaluation stages. This should be considered when comparing random-baseline values between Dev and Test.

## 6. Overall Synthesis

The experimental results indicate that classical machine-learning models can provide useful ranking signals for reference-free Critical Error Detection.

Logistic Regression achieved the highest PR-AUC on the held-out Test set, outperforming the heuristic baseline and Linear SVM. However, its operational advantage under a fixed 20% review budget was marginal: it identified only one additional Critical Error compared with the heuristic baseline.

The paired document-cluster bootstrap showed a statistically distinguishable improvement in PR-AUC, but did not establish an advantage in Recall@20%, Precision@20%, Lift@20%, or MCC@20%.

The qualitative analysis further showed that many high-priority segments without critical votes still contained Minor MQM annotations. A substantial proportion also exhibited annotator disagreement. These findings suggest that the binary Critical Error label does not fully represent the range and uncertainty of translation-quality annotations.

The analysis also demonstrated that strict target matching is important. Annotation rows associated with alternative target variants can affect the interpretation of segment-level error evidence if they are joined only by segment identifiers.

Overall, the Second Pair of Eyes system should be considered a decision-support mechanism for prioritizing human review rather than an autonomous translation-quality evaluator. Further validation on additional language pairs, domains, and unseen MT systems is required before making broader generalization claims.

## 7. Evidence and Reproducibility References

The following project artifacts support this synthesis:

**Experimental evaluation**

- `results/week10/test_evaluation/test_point_metrics.csv`
- `results/week10/test_evaluation/test_metrics_with_ci.csv`
- `results/week10/test_evaluation/paired_difference_ci.csv`
- `results/week10/test_evaluation/test_predictions.csv`
- `results/week10/ablation_dev/dev_ablation_metrics.csv`
- `results/week10/ablation_dev/dev_ablation_manifest.json`

**Week 11 error analysis**

- `results/week11/error_analysis_dev/dev_top20_error_analysis.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_summary.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_status_summary.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_rater_detail.csv`
- `results/week11/error_analysis_dev/dev_top20_error_analysis_unmatched.csv`

**Strict target-matching audit**

- `src/analyze_dev_zero_vote.py`
- `analysis/audit_dev_top20_strict_target_matching.py`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_annotations.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_strict_segment_audit.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_strict_rater_audit.csv`
- `results/week10/error_analysis_dev/dev_top20_zero_vote_strict_audit_summary.json`

**Current ten-case evidence**

- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_report.md`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_audit_summary.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_matched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_unmatched_annotations.csv`
- `results/week11/error_analysis_dev/current_10_case_analysis/current_10_case_qualitative_evidence.csv`

**Previous reports**

- `reports/G2_experimental_evaluation_report.md`
- `reports/G3_5_4_bao_cao_tai_lap_test_evaluation.md`
- `reports/G4_1_qualitative_error_analysis.md`

The current ten-case analysis is the authoritative qualitative case selection. Earlier Week 11 case-analysis artifacts are retained for historical reference and should not be mixed with the current ten-case evidence unless explicitly re-audited.
