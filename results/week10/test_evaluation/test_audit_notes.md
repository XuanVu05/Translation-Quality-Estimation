# Week 10 Test Evaluation Audit

## Existing artifacts

- test_predictions.csv
- test_point_metrics.csv
- test_metrics_with_ci.csv
- paired_difference_ci.csv
- error_analysis/test_predictions_with_mqm.csv

## Verified checks

- Test predictions were previously checked against the saved Test split.
- Point metrics were recomputed from the saved predictions and matched.
- Paired document-cluster bootstrap results were reproduced from saved predictions.

## Limitations

- Available logs do not establish the complete history of Test evaluations.
- File modification timestamps are not proof of the exact model execution history.
- It cannot be confirmed from the available evidence that Test was never used for model selection before the split was locked.

## Handling decision

- Preserve existing Test outputs.
- Do not rerun Test solely to recreate historical evidence.
- Report the limitation transparently.

## Random baseline convention

- Development set: Random metrics are averaged over 100 random rankings
  using seeds 42 through 141. Mean and sample standard deviation
  (ddof=1) are reported.
- Test set: Random metrics are based on one random ranking generated
  with seed 20261026.
- The Test evaluation additionally uses 1,000 paired document-cluster
  bootstrap replicates for uncertainty estimation.
- The Dev and Test Random estimates use different aggregation
  conventions and should not be interpreted as a like-for-like
  comparison.
- Existing Test outputs are preserved; Test was not rerun to
  standardize the Random baseline.
