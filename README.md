# Second Pair of Eyes

## Final Project Submission — Group 02 (CLC02)

**Course:** Machine Learning Applications
**Project:** Second Pair of Eyes: A Reference-Free Risk-Ranking System for Critical Machine Translation Errors
**Language pair:** English → German
**Dataset:** WMT 2020 MQM (`newstest2020`)

## 1. Project Overview

This project investigates a reference-free risk-ranking approach for identifying machine-translation segments that may contain critical errors. Its purpose is to help human reviewers prioritise segments under a limited review budget.

The system is designed as a decision-support tool. A high-risk prediction should not be interpreted as definitive evidence that a translation is incorrect.

The experiments use WMT 2020 MQM English–German annotations and outputs from seven machine-translation systems.

## 2. Group Members and Contributions

| Student      | Student ID | Responsibilities                                                                                                                                                                                             |
| ------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Vũ Thị Xuân  | 2301140104 | Project coordination; work on data-related and programming/model-related tasks; integration of experimental results and analysis; preparation and revision of the final report and submission documentation. |
| Lê Như Quỳnh | 2301140084 | Collaboration with Vũ Thị Xuân on data-related work, including data inspection, validation, preprocessing review, and data-related analysis.                                                                 |
| Trần Nam Sơn | 2301140089 | Collaboration with Vũ Thị Xuân on programming-related work, including code implementation/review and examination of model execution and code-generated results.                                              |

All members should review and confirm this allocation before submission.

## 3. Repository Structure

```text
Translation-Quality-Estimation/
├── Data/
│   ├── raw/
│   │   └── mqm_newstest2020_ende.tsv
│   ├── details/
│   │   └── en-de.txt
│   ├── official_wmt2020/
│   │   └── sgm/
│   │       └── newstest2020-ende-src.en.sgm
│   └── original_outputs/
│       └── Seven original MT output files
├── Code/
│   ├── config.py
│   ├── src/
│   ├── analysis/
│   │   └── archive/
│   └── experiments/
├── Results/
│   ├── week10/
│   ├── week11/
│   └── data_quality/
├── Report/
│   ├── phase1_data_label_audit/
│   ├── phase2_3/
│   ├── phase4/
│   ├── phase5/
│   └── Markdown milestone and audit reports
├── AI_Log/
│   └── AI_Use_Log.md
├── .gitignore
├── requirements.txt
└── README.md
```

The local environments `.venv_mla/` (Python 3.13) and `.venv_audit/` (Python 3.11) are development environments. They should not be copied to the USB. Recreate the required environment using the dependency specification and the Python version required by each script.

## 4. Data and Label Construction

| Repository path                                          | Description                            |
| -------------------------------------------------------- | -------------------------------------- |
| `Data/raw/mqm_newstest2020_ende.tsv`                     | MQM annotation data                    |
| `Data/details/en-de.txt`                                 | Document and line-ID mapping           |
| `Data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm` | Official WMT 2020 English source file  |
| `Data/original_outputs/`                                 | Original outputs from seven MT systems |

The reported consolidated segment-level dataset contains 9,926 segments from 130 documents and seven MT systems.

The serious-error rule is defined as follows:

- An annotation is serious when its severity is `Major` and its category begins with `Accuracy/`.
- An annotation is also serious when its category is exactly `Non-translation!`.
- A segment receives the primary positive label when at least two of the three raters cast a serious vote.

The reported label distribution is 1,183 positive and 8,743 negative segments, corresponding to a positive prevalence of approximately 11.92%.

The reported Fleiss' Kappa is 0.290029, with disagreement among raters on 2,779 segments. Refer to the final report and audit outputs for the detailed label definition and validation evidence.

## 5. Code Organisation

`Code/config.py` is the central path-configuration module. Project scripts should use repository-relative paths through this module rather than machine-specific absolute paths.

- `Code/src/`: document-level splitting, model-dataset construction, baseline evaluation, Dev ablation, and Test evaluation.
- `Code/analysis/`: data-integrity audits and qualitative error-analysis scripts.
- `Code/analysis/archive/`: retained one-off or historical scripts.
- `Code/experiments/`: exploratory and extended experiments.

### Principal Source Files

| Script                                              | Purpose                                       |
| --------------------------------------------------- | --------------------------------------------- |
| `Code/src/split_by_document.py`                     | Creates document-level partitions.            |
| `Code/src/build_model_dataset.py`                   | Builds the model-ready segment dataset.       |
| `Code/src/run_baselines.py`                         | Runs baseline experiments.                    |
| `Code/src/run_ablation_dev.py`                      | Runs Dev ablation experiments.                |
| `Code/src/evaluate_test_week10.py`                  | Runs the documented Test evaluation workflow. |
| `Code/src/analyze_dev_zero_vote.py`                 | Analyses Dev zero-vote cases.                 |
| `Code/src/freeze_week10_split.py`                   | Freezes the designated split.                 |
| `Code/src/validate_week10.py`                       | Validates the experimental setup.             |
| `Code/src/verify_locked_split.py`                   | Verifies the locked split.                    |
| `Code/analysis/rebuild_current_10_case_analysis.py` | Rebuilds the current ten-case analysis.       |
| `Code/analysis/audit_mapping_integrity.py`          | Audits mapping integrity.                     |
| `Code/analysis/audit_original_target_alignment.py`  | Checks alignment with original MT targets.    |
| `Code/analysis/analyze_dev_top20_error_analysis.py` | Supports Dev Top-20% error analysis.          |
| `Code/experiments/sensitivity_analysis_week10.py`   | Runs sensitivity analysis.                    |

Other scripts are retained in their corresponding directories. Consult each script's current arguments and implementation before execution.

## 6. Results and Evidence

Generated outputs are organised under `Results/`.

- `Results/week10/` contains model data, locked-split evidence, baseline results, Dev ablation, Test evaluation, and error-analysis outputs.
- `Results/week11/` contains further Dev qualitative analysis, including the current ten-case analysis.
- `Results/data_quality/` contains data-quality audit outputs.

Preserve the CSV, JSON, manifest, log, audit-report, prediction, and figure files that support the final report. Do not manually alter generated result files and present them as direct model outputs.

## 7. Experimental Design and Evaluation

The reported document-level split contains:

- Train: 90 documents
- Dev: 20 documents
- Test: 20 documents

There is no document overlap between the three partitions. The Test partition contains 1,575 segments, including 162 positive segments (10.29% prevalence).

The evaluated approaches include random ranking, a rule-based heuristic, Logistic Regression, Linear SVM, and XLM-R.

The reported metrics include Average Precision (AP), ROC-AUC, Precision\@20%, Recall\@20%, Lift\@20%, and Matthews Correlation Coefficient (MCC), where applicable.

AP refers to `sklearn.metrics.average_precision_score`, not trapezoidal PR-AUC.

The XLM-R checkpoint was selected using Dev Average Precision. The reported checkpoint was epoch 2 (Dev AP = 0.201489). The reported XLM-R evaluation uses one training seed.

The paired document-cluster bootstrap comparison between XLM-R and Logistic Regression used 1,000 document-level resamples and bootstrap seed 42. The reported 95% percentile confidence intervals include zero for AP, ROC-AUC, Precision\@20%, and Recall\@20%. Therefore, the comparison does not establish a statistically distinguishable advantage for either model.

The current Test set must not be used for further feature selection, threshold tuning, checkpoint selection, or model adjustment.

## 8. Environment Setup

The root `requirements.txt` specifies Python dependencies. Do not submit the local virtual environments.

### Windows PowerShell

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project inventory identifies `.venv_mla/` as Python 3.13 and `.venv_audit/` as Python 3.11. Verify which interpreter each script requires. If separate environments are necessary, document the exact Python version and installation procedure.

## 9. Recommended Execution Order

The following is the logical workflow. It is not a claim that every command has been tested on a clean computer.

1. Read `Data/DATA_README.md` and verify data provenance, licences, and redistribution conditions.
2. Review `Code/config.py` and confirm that configured paths resolve from the repository root.
3. Create or verify the document-level split using the relevant scripts in `Code/src/`.
4. Build the model-ready dataset using `Code/src/build_model_dataset.py`.
5. Run baselines using `Code/src/run_baselines.py`.
6. Run Dev ablation using `Code/src/run_ablation_dev.py`.
7. Run the documented Test evaluation using `Code/src/evaluate_test_week10.py`, respecting the locked-Test protocol.
8. Run required audit and error-analysis scripts in `Code/analysis/`.
9. Run only additional experiments needed to reproduce results cited in the report.
10. Compare generated outputs with saved evidence in `Results/`.

## 10. Reproducibility and Limitations

- Use repository-relative paths through `Code/config.py`.
- Preserve the document-level split manifest, document assignments, and validation evidence.
- Record the exact XLM-R model identifier, tokenizer, hyperparameters, training seed, and software versions from the final configuration and logs.
- Keep the model-training seed separate from the bootstrap resampling seed.
- Do not use the current Test set for model selection or adjustment.
- The XLM-R evaluation uses one training seed and does not establish multi-seed stability.
- The paired XLM-R–LR bootstrap uses the existing Test set and 20 document clusters; it is not an independent external evaluation.
- Redistribute only data components that the group is authorised to share.
- Remove credentials, private data, temporary files, and local virtual environments from the USB copy.
