# AI Use Log

## Second Pair of Eyes — Group 02 (CLC02)

## 1. Declaration

ChatGPT (OpenAI) was used by the project representative, for supporting tasks during project development and preparation of the final submission.

The recorded assistance includes explanations of machine-learning concepts and evaluation, methodological discussion, code and analysis troubleshooting, interpretation of experimental results, and editing of technical documentation and LaTeX.

ChatGPT was used as an assistant, not as a substitute for the implemented predictive models. The reported predictions are attributed to the project's implemented methods: random ranking, the rule-based heuristic, Logistic Regression, Linear SVM, and XLM-R.

## 2. AI Tools

| Tool             | Recorded user/scope                             | Purpose                                                                                                                                                        | Verification                                                             |
| ---------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| ChatGPT (OpenAI) | Project representative's recorded conversations | Technical explanations, methodology discussion, code/analysis support, interpretation of results, report editing, LaTeX assistance, and documentation drafting | Student review of code, numerical results, references, and final wording |
|                  |                                                 |                                                                                                                                                                |                                                                          |

## 3. Dated Interaction Summary

The following dates are based on dated conversations in the project history. Descriptions are concise summaries, not verbatim prompts.

| Date       | Recorded project-related topic                                                                                                                     | Type of assistance                                              |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 2026-09-27 | Discussion of the research gap, baseline design, class imbalance, dataset handling, and likely assessment questions.                               | Methodological explanation and critical review.                 |
| 2026-10-09 | Review of the report against instructor requirements, including the rule-based baseline, data licence, and error-analysis plan.                    | Report review and requirements alignment.                       |
| 2026-10-26 | Guidance on the Week 10 report and analysis workflow.                                                                                              | Technical troubleshooting and analysis support.                 |
| 2026-11-05 | Repository cleanup, README review, and code-organisation discussion.                                                                               | Documentation and code-organisation support.                    |
| 2026-11-20 | LaTeX report revision, cover-page formatting, table of contents, figure paths, and incorporation of XLM-R comparison and paired-bootstrap results. | LaTeX troubleshooting, report editing, and result presentation. |
| 2026-11-21 | Preparation and revision of submission documentation, member-contribution wording, and reproducibility documentation.                              | Documentation drafting and consistency review.                  |

## 4. Areas of AI Assistance

The recorded assistance for the project representative covered:

- Explaining MQM annotation concepts, serious-error label construction, class imbalance, and inter-rater agreement.
- Discussing document-level splitting and the purpose of separating documents across Train, Dev, and Test.
- Explaining Average Precision, ROC-AUC, Precision\@20%, Recall\@20%, Lift\@20%, and MCC.
- Reviewing interpretations of baseline, ablation, XLM-R, and error-analysis results.
- Discussing paired document-cluster bootstrap interpretation and the limitations of confidence intervals based on a small number of document clusters.
- Supporting code troubleshooting and repository organisation.
- Editing report sections, tables, figures, references, and LaTeX formatting.
- Drafting and revising README and reproducibility documentation.

## 5. AI Use in the Experimental Pipeline

### 5.1 Predictive Methods

The reported predictive methods are random ranking, a rule-based heuristic, Logistic Regression, Linear SVM, and XLM-R.

ChatGPT was not used as a replacement prediction model for these methods.

### 5.2 Evaluation and Bootstrap

The paired XLM-R–Logistic Regression comparison used document-cluster resampling with 1,000 replicates and bootstrap seed 42. This is an analysis/resampling seed, not the XLM-R training seed.

The reported 95% percentile confidence intervals include zero for AP, ROC-AUC, Precision\@20%, and Recall\@20%. The comparison therefore does not establish a statistically distinguishable advantage for either model.

The current Test set was used for the reported final evaluation and comparison. It must not be used for further model adjustment. The bootstrap comparison is not an independent external Test evaluation.

## 6. Human Review and Verification

AI-generated suggestions were treated as assistance rather than authoritative experimental evidence. We remain responsible for the final code, data processing, model training, metrics, interpretations, references, and documents.

Complete each item only after the check has actually been performed:

- [ ] Code suggestions retained in the repository were inspected and tested.
- [ ] Metric values were checked against saved result outputs or evaluation code.
- [ ] Dataset source, version, licence, and redistribution conditions were checked against authoritative documentation.
- [ ] Label rules and label counts were checked against the data and audit outputs.
- [ ] Train/Dev/Test document separation was checked against the split manifest and validation outputs.
- [ ] Model configuration and training details were checked against the final notebook, logs, and checkpoint metadata.
- [ ] Report tables and figures were checked against the final generated outputs.
- [ ] Bibliographic details were checked against the cited publications.
- [ ] AI-assisted wording was reviewed and corrected where necessary.
- [ ] No credentials or unauthorised private data were provided to an AI service.

## 7. Group Declaration

We confirm that this log has been reviewed by the group and accurately represents the AI tools and assistance used in preparing the submitted project. We accept responsibility for the submitted code, data processing, experiments, results, interpretations, citations, and final report.
