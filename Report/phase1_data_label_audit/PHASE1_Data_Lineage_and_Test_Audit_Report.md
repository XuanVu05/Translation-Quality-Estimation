# PHASE 1 --- DATA LINEAGE, LABEL RECONSTRUCTION, DATA SPLIT AND TEST-SET AUDIT

**Project:** Second Pair of Eyes --- Reference-Free Critical Error
Detection\
**Dataset:** WMT 2020 MQM English--German (`newstest2020`)\
**Phase:** 1 --- Data Lineage, Split and Test Evaluation Audit\
**Status:** Completed with documented limitations\
**Report purpose:** Preserve the evidence, checks, results, decisions,
and unresolved limitations from Phase 1 for inclusion in the final
project repository.

------------------------------------------------------------------------

## 1. Executive summary

Phase 1 audited the path from the raw WMT 2020 MQM annotations to the
segment-level labels and the train/development/test partitions used by
the project. It also reviewed the current evaluation implementation and
the evidence available about historical test-set use.

The audit establishes the following:

1.  The project's serious-error label can be reconstructed from the MQM
    annotation rows using the documented severity/category rule and
    one-vote-per-rater aggregation.
2.  An individual translation was traced from its raw annotations
    through three rater-level serious votes to its final majority label.
3.  The final model dataset contains 9,926 translation rows from seven
    MT systems, covering 130 documents and 1,418 source segments.
4.  Each translation has exactly three rater assessments. The label
    reconstruction previously performed independently matched the
    existing labels exactly: no missing keys and no label disagreements.
5.  The document-level split contains 90 train documents, 20 development
    documents, and 20 test documents. No document is shared across
    partitions.
6.  The current evaluation script fits the models on train plus
    development data and evaluates on the test partition. Saved test
    predictions match the saved test split.
7.  The available artifacts do **not** establish the complete historical
    sequence of test-set use. It is therefore not possible to prove that
    the test set was never consulted during earlier model-selection
    work.
8.  The uploaded raw MQM file contains 79,020 rows, whereas an earlier
    audit recorded 79,024 rows. The four-row discrepancy remains
    unresolved and must be retained as a data-version caveat.
9.  Source text aligns with the official WMT source after the documented
    normalization, but the comparison is not byte-exact: 464 of 1,418
    segments differ only in quote formatting under the normalization
    procedure.
10. Reviewer markup (`<v>...</v>`) occurs in raw MQM target strings. The
    final split dataset has no such tags in its source or target fields.
    The exact preprocessing stage responsible for removing them should
    be tied to the implementation in the dataset-building code.

The phase is complete for the checks supported by the available
evidence. The unresolved historical and versioning limitations are
explicitly recorded rather than inferred away.

------------------------------------------------------------------------

## 2. Project and dataset scope

### 2.1 Dataset

The project uses the WMT 2020 MQM English-to-German data associated with
`newstest2020`.

The raw annotation schema contains the following fields:

  -----------------------------------------------------------------------
  Field                               Meaning in the project
  ----------------------------------- -----------------------------------
  `system`                            MT system identifier

  `doc`                               Document identifier used by MQM

  `doc_id`                            Segment identifier in the MQM
                                      representation

  `seg_id`                            Segment/line identifier used for
                                      mapping

  `rater`                             Annotator identifier

  `source`                            English source segment

  `target`                            German translation text,
                                      potentially containing reviewer
                                      span markup

  `category`                          MQM error category

  `severity`                          MQM severity
  -----------------------------------------------------------------------

### 2.2 Systems retained for modeling

The model dataset retains seven MT systems:

-   `eTranslation.737`
-   `Huoshan_Translate.832`
-   `Online-A.1574`
-   `Online-B.1590`
-   `OPPO.1535`
-   `Tencent_Translation.1520`
-   `Tohoku-AIP-NTT.890`

The raw MQM file contains additional systems beyond the seven retained
for the model dataset. The uploaded raw file has 10 systems in total.

### 2.3 Dataset construction counts

The previously audited dataset construction produced:

  -----------------------------------------------------------------------
  Item                                                              Count
  ------------------------------ ----------------------------------------
  Raw MQM annotation rows in the                                   79,024
  earlier audited version        

  Annotation rows after                                            61,120
  filtering to the seven         
  retained MT systems            

  Documents                                                           130

  Source segments                                                   1,418

  MT systems retained                                                   7

  Segment/system translation                                        9,926
  rows                           

  Rater assessments per                                                 3
  translation                    

  Positive majority labels                                          1,183

  Negative majority labels                                          8,743

  Positive rate                                                    11.92%
  -----------------------------------------------------------------------

The uploaded raw MQM file examined for this report contains **79,020
rows**, not 79,024. This discrepancy is addressed in Section 8. Counts
from the earlier audit are retained as the recorded dataset-construction
results; the two raw-file versions are not treated as identical without
reconciliation.

------------------------------------------------------------------------

## 3. Serious-error definition and label construction

### 3.1 Serious annotation rule

The project defines a serious error as an annotation satisfying both
conditions:

-   `severity == Major`; and
-   `category` starts with `Accuracy/` **or** is exactly
    `Non-translation!`.

In logical form:

\[ `\text{serious\_annotation}`{=tex} =
(`\text{severity}`{=tex}=`\text{Major}`{=tex}) `\land`{=tex} `\left[
\text{category starts with Accuracy/}
\lor
\text{category}=\text{Non-translation!}
\right]`{=tex}\]

This is the operational definition used by `src/build_model_dataset.py`.

### 3.2 One vote per rater

For each translation, identified by its system/document/segment key,
annotation rows are aggregated at rater level. A rater contributes one
serious vote if at least one of that rater's annotation rows for the
translation satisfies the serious-error rule.

This prevents multiple serious annotation rows from the same rater from
being counted as multiple independent votes.

### 3.3 Majority-label rule

Each translation has three rater assessments. The primary binary label
is:

\[ y\_{`\text{primary}`{=tex}} =
```{=tex}
\begin{cases}
1 & \text{if serious\_votes}\geq 2\\
0 & \text{otherwise}
\end{cases}
```
\]

Thus, a translation is labeled positive when at least two of its three
raters identify a serious error.

### 3.4 Reconstructed label distribution

The audited label distribution is:

    Serious votes   Number of translations
  --------------- ------------------------
                0                    6,810
                1                    1,933
                2                      846
                3                      337
        **Total**                **9,926**

The final binary-label distribution is:

  Label               Number of translations
  ----------------- ------------------------
  `y_primary = 0`                      8,743
  `y_primary = 1`                      1,183
  **Total**                        **9,926**

Positive prevalence:

\[ `\frac{1,183}{9,926}`{=tex}`\approx 0.1192`{=tex} = 11.92% \]

The earlier independent reconstruction found that all translation keys
matched and that there were zero label disagreements with the existing
label dataset.

------------------------------------------------------------------------

## 4. Example-level trace: raw MQM annotations to majority label

A concrete translation was selected to demonstrate the full
label-generation procedure.

### 4.1 Translation key

  Field      Value
  ---------- ------------------------------
  System     `eTranslation.737`
  Document   `abcnews.363994`
  `doc_id`   `4`
  `seg_id`   `1316`
  Raters     `rater4`, `rater5`, `rater6`

### 4.2 Source sentence

> Boccio's attorney, Kenneth Lange, said his client was convinced to
> take part in the scheme by co-defendant, Serge Nkorina, who's being
> extradited from Tenerife, Spain.

### 4.3 Rater-level evidence

The raw MQM annotations for this translation show:

  -------------------------------------------------------------------------------
  Rater                 Annotation evidence                          Serious vote
  --------------------- ---------------------------- ----------------------------
  `rater4`              `Accuracy/Mistranslation`,                              1
                        `Major`; this rater also has 
                        a separate `Style/Awkward`,  
                        `Minor` annotation           

  `rater5`              `Accuracy/Mistranslation`,                              1
                        `Major`                      

  `rater6`              `Accuracy/Mistranslation`,                              1
                        `Major`                      
  -------------------------------------------------------------------------------

`rater4` has two annotation rows, but only one satisfies the
serious-error rule. More generally, even if one rater has multiple
serious annotation rows for a translation, that rater contributes at
most one serious vote.

### 4.4 Vote aggregation

\[ `\text{serious\_votes}`{=tex}=1+1+1=3 \]

Since three votes meet the threshold of at least two:

\[ y\_{`\text{primary}`{=tex}}=1 \]

**Reconstructed result:** this translation receives the positive
majority label (`y_primary = 1`).

This example verifies the complete transformation:

**Raw MQM rows → serious-error rule → one vote per rater → total serious
votes → majority label.**

------------------------------------------------------------------------

## 5. Reviewer markup and model-input integrity

### 5.1 Markup in raw MQM targets

Raw MQM target strings may contain `<v>` and `</v>` tags. These tags
mark spans associated with reviewer annotations; they are not part of
the underlying machine-translated sentence.

For the traced example, one annotation-specific target contains the
marked span:

`<v>sei überzeugt, sich an dem Plan des Mitangeklagten Serge Nkorina zu beteiligen</v>`

After removing the reviewer tags, the underlying German translation is:

> Der Anwalt von Boccio, Kenneth Lange, sagte, sein Mandant sei
> überzeugt, sich an dem Plan des Mitangeklagten Serge Nkorina zu
> beteiligen, der aus Teneriffa, Spanien, ausgeliefert wird.

The four raw annotation rows for the traced example yield the same
underlying translation after removal of the reviewer span tags.

### 5.2 Final model dataset

The previously inspected
`results/week10/model_data/segments_with_fixed_splits.csv` has no
HTML/XML tags or `<v>...</v>` reviewer markup in its `source` or
`target` fields.

This supports the conclusion that the final model dataset contains
unmarked source and translation text.

### 5.3 Evidence boundary

The final CSV establishes the state of the model-input fields after
dataset construction. It does not, by itself, identify the exact line or
preprocessing operation at which reviewer markup was removed.

The final report should therefore make two separate statements:

-   **Supported:** the final split dataset's source and target fields do
    not contain reviewer markup.
-   **Requires code-level attribution:** the exact preprocessing stage
    that strips the markup must be identified from the dataset-building
    implementation.

The model must not receive reviewer markup as part of its translation
input because that markup encodes annotation information unavailable in
ordinary MT output and could contaminate the input representation.

------------------------------------------------------------------------

## 6. Source alignment and identifier mapping

### 6.1 Mapping file

The mapping file `data/details/en-de.txt` is headerless and was
interpreted using the following column order:

1.  `line_id`
2.  `set_id`
3.  `language_pair`
4.  `document_id`
5.  `segment_id`

The audited key correspondence is:

  MQM field   Mapping field
  ----------- ---------------
  `doc`       `document_id`
  `seg_id`    `line_id`
  `doc_id`    `segment_id`

The audit found 1,418 unique source-segment keys, and all 1,418 matched
the mapping file. The MQM `doc_id` also matched the mapping file's
`segment_id` for all 1,418 source segments.

### 6.2 Official source file

The official WMT source file examined was:

`data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm`

A standard XML parse failed because the source file contains an invalid
XML character. A regex-based extraction was therefore used to recover
the document and segment structure.

The extraction recovered:

-   130 documents;
-   1,418 source segments;
-   the expected sequence order;
-   zero sequence mismatches.

### 6.3 Text comparison and normalization

The raw MQM source strings were not byte-for-byte identical to the
official SGM source strings.

After applying the documented normalization---Unicode NFC normalization,
whitespace collapsing, quote normalization, and collapsing repeated
quote characters---the comparison yielded:

  Comparison result                                     Segments
  --------------------------------------------------- ----------
  Exact matches after normalization                          954
  Quote-format-only differences under normalization          464
  Total                                                    1,418

All 1,418 source segments aligned under the implemented normalization
procedure.

**Important wording:** the source data should be described as matching
after normalization, not as byte-identical. The 464 quote-format-only
differences must not be omitted from the audit description.

------------------------------------------------------------------------

## 7. Rater coverage and agreement audit

This section records the rater-quality and assignment checks completed
before the current report.

### 7.1 Rater coverage

-   There are six rater identifiers: `rater1` through `rater6`.
-   Every translation has exactly three distinct raters.
-   The 9,926 translation keys have three ratings each.
-   The assignment audit found 20 unique combinations of three raters.

### 7.2 Agreement on serious-error decisions

  Agreement outcome                        Translations
  -------------------------------------- --------------
  Unanimous negative (0 serious votes)            6,810
  Unanimous positive (3 serious votes)              337
  Total unanimous                                 7,147
  Disagreement (1 or 2 serious votes)             2,779
  Total                                           9,926

-   Unanimity: approximately 72%.
-   Disagreement: approximately 28%.

Fleiss' Kappa was calculated using 9,926 segments with three ratings
each:

  Statistic                                        Value
  ------------------------------------------- ----------
  Observed agreement, (P\_{`\bar{}`{=tex}})     0.813352
  Expected agreement, (P_e)                     0.737105
  Fleiss' Kappa                                 0.290029

Under the commonly used Landis--Koch heuristic, this value falls in the
"fair" agreement range. This categorization is only a heuristic
description; it is not a definitive threshold for annotation quality.

### 7.3 Pooled rater-level serious-vote rates

  Rater      Segments rated   Serious votes   Serious-vote rate
  -------- ---------------- --------------- -------------------
  rater1              4,991             720              14.43%
  rater2              4,781             404               8.45%
  rater3              4,935           1,101              22.31%
  rater4              4,963             893              17.99%
  rater5              5,054             954              18.88%
  rater6              5,054             564              11.16%

These differences indicate variation in serious-vote rates across
raters. They may reflect annotation tendencies, assignment composition,
or other factors. The rates alone do not establish annotator bias.

### 7.4 Per-system positive rates and agreement

  System           Positive labels   Positive rate   Fleiss' Kappa
  -------------- ----------------- --------------- ---------------
  Huoshan              166 / 1,418          11.71%          0.2763
  OPPO                 144 / 1,418          10.16%          0.3054
  Online-A             242 / 1,418          17.07%          0.3220
  Online-B             187 / 1,418          13.19%          0.2810
  Tencent              149 / 1,418          10.51%          0.2454
  Tohoku               120 / 1,418           8.46%          0.2717
  eTranslation         175 / 1,418          12.34%          0.2952

### 7.5 Pairwise rater agreement

  Pair               Agreement
  ---------------- -----------
  rater1--rater2        82.02%
  rater1--rater3        76.19%
  rater1--rater4        88.52%
  rater1--rater5        83.59%
  rater1--rater6        86.33%
  rater2--rater3        82.05%
  rater2--rater4        79.89%
  rater2--rater5        79.54%
  rater2--rater6        87.24%
  rater3--rater4        79.48%
  rater3--rater5        76.84%
  rater3--rater6        79.53%
  rater4--rater5        78.38%
  rater4--rater6        78.54%
  rater5--rater6        81.19%

### 7.6 Assignment structure across systems and documents

The assignment audit established:

-   All 1,418 source segments occur in all seven retained MT systems.
-   Each source segment has the same combination of three raters across
    all seven systems.
-   There are zero source segments with a different rater combination
    across systems.
-   The distribution of rater combinations is identical across the seven
    systems.
-   Each document is associated with exactly one rater combination.
-   There are 130 documents and 910 document/system groups (130 × 7).
-   The maximum number of rater combinations within a document is one.
-   The maximum segment count for one rater combination within a
    document is 26.

Rater positive-rate variation across systems was also observed:

  -----------------------------------------------------------------------
  Rater       Minimum system Maximum system           Mean       Standard
                        rate           rate                     deviation
  ----------- -------------- -------------- -------------- --------------
  rater1              12.62%         20.06%         14.43%           2.58

  rater2               6.88%         10.54%          8.45%           1.19

  rater3              15.74%         29.65%         22.31%           4.43

  rater4              13.68%         23.27%         17.99%           3.03

  rater5              13.57%         24.24%         18.88%           3.17

  rater6               9.14%         14.96%         11.16%           2.15
  -----------------------------------------------------------------------

Because the same annotator composition is used for each source segment
across systems, paired system comparisons are not confounded by a change
in the rater combination at the source-segment level.

However, rater-level differences remain. In addition, each document has
a fixed rater combination, so document characteristics and rater
assignment are coupled in this dataset. The current assignment structure
does not allow those effects to be fully separated.

------------------------------------------------------------------------

## 8. Raw-file version discrepancy

The raw MQM file uploaded for this audit contains:

  Item         Uploaded file
  ---------- ---------------
  Raw rows            79,020
  Systems                 10

The earlier Phase 1 data audit recorded 79,024 raw rows. The difference
is four rows.

The current evidence does not identify which four rows are absent or
establish whether the difference results from a file revision,
filtering, or another export difference. Therefore:

-   Do not describe the two raw files as identical.
-   Do not silently replace the previously recorded count.
-   Preserve the discrepancy in the project audit trail.
-   Before final submission, if the exact raw-data provenance is
    required, compare the two file versions or record the authoritative
    source/version and checksum.

The seven-system modeling dataset and its previously audited counts are
documented separately from this unresolved raw-file discrepancy.

------------------------------------------------------------------------

## 9. Document-level train/development/test split

### 9.1 Split implementation

The split is implemented in `src/split_by_document.py` using
`GroupShuffleSplit`, with document (`doc`) as the grouping variable.

The recorded procedure is:

1.  First split: reserve 15% of documents for test, using
    `random_state=42`.
2.  Second split: reserve `0.15 / 0.85` of the remaining documents for
    development, using `random_state=43`.
3.  The remaining documents form the training partition.

This produces an intended 70% / 15% / 15% document-level split.

### 9.2 Partition sizes

  -------------------------------------------------------------------------------
  Partition        Documents       Source   Translation     Positive     Positive
                                 segments          rows       labels         rate
  ------------- ------------ ------------ ------------- ------------ ------------
  Train                   90          971         6,797          803       11.81%

  Development             20          222         1,554          218       14.03%

  Test                    20          225         1,575          162       10.29%

  **Total**          **130**    **1,418**     **9,926**    **1,183**   **11.92%**
  -------------------------------------------------------------------------------

Every translation row has exactly three rater assessments.

### 9.3 Why split by document?

Segments from the same document can share topic, named entities, style,
vocabulary, and contextual information. Randomly distributing individual
segments across train and test could therefore allow document-specific
information to appear in both partitions.

Grouping by document reduces this leakage risk and makes the test
evaluation more representative of performance on documents not seen
during model development.

This is the methodological rationale for the current design. The
available project artifacts do not document the historical reason for
changing from any earlier split configuration.

### 9.4 Split snapshot and verification

The split-freezing and verification scripts reviewed were:

-   `src/freeze_week10_split.py`
-   `src/verify_locked_split.py`

The freezing script validates the current split and records a snapshot,
assignments, manifest, and SHA256 information. It does not regenerate
the split. The manifest records:

-   split method: `GroupShuffleSplit by doc`;
-   random seeds: 42 and 43;
-   status: `candidate_locked`.

The verification script checks the source CSV, snapshot, manifest, split
files, and hash integrity.

The status `candidate_locked` documents the current snapshot state. It
is not proof that the split was locked before every historical
experiment or that the test set was never previously consulted.

### 9.5 Document overlap

The previously completed validation found no document overlap between
train, development, and test. The current partition counts sum to all
130 documents and all 9,926 translation rows.

------------------------------------------------------------------------

## 10. Test evaluation implementation and saved-artifact audit

### 10.1 Current evaluation procedure

The reviewed script `src/evaluate_test_week10.py`:

-   fits the vectorizer and scaler using training plus development data;
-   trains Logistic Regression and Linear SVM using training plus
    development data;
-   generates test predictions and computes test metrics;
-   includes a code comment indicating that model choice had already
    been fixed based on development results.

This describes the behavior of the current evaluation script. It should
not be interpreted as proof of the complete historical sequence of all
prior experiments.

### 10.2 Saved artifacts reviewed

The audit identified and reviewed the following relevant artifacts:

-   `results/week10/test_evaluation/test_predictions.csv`
-   `results/week10/test_evaluation/test_point_metrics.csv`
-   `results/week10/test_evaluation/test_metrics_with_ci.csv`
-   `results/week10/test_evaluation/paired_difference_ci.csv`
-   `results/week10/test_evaluation/test_audit_notes.md`
-   `results/week10/error_analysis/test_predictions_with_mqm.csv`
-   `results/week10/model_data/test_segments.csv`
-   `results/week10/model_data/segments_with_fixed_splits.csv`

Relevant scripts reviewed:

-   `src/evaluate_test_week10.py`
-   `src/freeze_week10_split.py`
-   `src/split_by_document.py`
-   `src/verify_locked_split.py`

### 10.3 Prediction-to-test-split consistency

The saved `test_predictions.csv` was compared with `test_segments.csv`
using the translation key:

`system, doc, doc_id, seg_id`

The audit found:

-   no missing test predictions;
-   no extra prediction keys;
-   no key mismatches;
-   no label mismatches.

The saved predictions therefore correspond to the saved test partition
on the audited keys and labels.

### 10.4 Historical test-use limitation

The test audit notes state that:

-   saved test predictions and point metrics can be recomputed from the
    saved prediction file;
-   paired document-cluster bootstrap results can be reproduced from
    saved predictions;
-   available logs do not establish the complete history of test
    evaluations;
-   file modification timestamps do not prove the exact model execution
    history;
-   the available evidence cannot confirm that the test set was never
    used for model selection before the split was locked.

This is a material limitation. The report must not claim that the test
set was untouched throughout the entire project history.

The defensible statement is:

> The current evaluation implementation trains on the combined training
> and development partitions and evaluates on the held-out test
> partition. The saved predictions match the saved test split. However,
> the available artifacts do not establish the complete historical
> sequence of test-set use, so the project cannot independently verify
> that the test set was never consulted during earlier model-selection
> activities.

### 10.5 Preserve existing test outputs

The audit recommendation is to preserve the existing test outputs and
not rerun the test evaluation merely to recreate historical evidence.
Rerunning the test set would not resolve the missing historical record.

### 10.6 Random-baseline convention

The development and test random baselines use different aggregation
conventions:

-   Development random metrics were averaged over 100 random rankings
    with seeds 42--141; the reported standard deviation is the sample
    standard deviation (`ddof=1`).
-   The test random baseline uses one random ranking with seed
    `20261026`.
-   Test evaluation also uses 1,000 paired document-cluster bootstrap
    replicates.

These random-baseline estimates are not strictly like-for-like because
their aggregation procedures differ. Existing test outputs were
preserved rather than rerunning test evaluation solely to standardize
the random baseline.

------------------------------------------------------------------------

## 11. Audit conclusions

### 11.1 What is supported by the evidence

The Phase 1 evidence supports the following conclusions:

1.  The serious-error rule is explicitly defined in the dataset-building
    implementation.
2.  The majority-label construction can be independently reconstructed
    from the raw MQM annotations.
3.  The selected example demonstrates the full annotation-to-label path
    and produces `y_primary = 1`.
4.  Each translation has three rater assessments.
5.  The independently reconstructed labels previously matched all
    existing translation keys and labels.
6.  The final model dataset contains 9,926 rows, seven MT systems, 130
    documents, and 1,418 source segments.
7.  The final split fields contain no reviewer span markup.
8.  Source alignment is complete after normalization, with 464
    quote-format-only differences.
9.  The current document-level split has 90/20/20 documents and no
    document overlap.
10. Saved test predictions match the saved test split.
11. The current evaluation script fits on train plus development data
    and evaluates on test.

### 11.2 What cannot be claimed

The evidence does not support the following claims:

-   That the two raw MQM file versions are identical.
-   That the source strings are byte-for-byte identical to the official
    SGM source.
-   That the exact reviewer-markup removal line or preprocessing stage
    has been established solely from the final CSV.
-   That the historical reason for changing the split configuration is
    documented.
-   That the test set was never consulted during any earlier
    model-selection activity.
-   That the manifest's `candidate_locked` status proves the split was
    locked before all historical experiments.

### 11.3 Final Phase 1 status

**Phase 1 is complete for the reproducible data, label,
source-alignment, split-integrity, and current evaluation-code checks
supported by the available artifacts.**

The following limitations remain explicitly open:

1.  Reconcile the 79,020-row uploaded raw file with the previously
    audited 79,024-row version.
2.  Attribute reviewer-markup removal to the exact preprocessing
    operation in the code, if the final report requires
    implementation-level detail.
3.  Historical reason for the split change is not recorded in the
    available artifacts.
4.  Complete historical test-set use cannot be independently verified.

These limitations should remain visible in the final project report.
They should not be concealed by stronger claims than the evidence
permits.

------------------------------------------------------------------------

## 12. Evidence and project paths

The following paths were used or identified during the Phase 1 audit:

### Data

-   `mqm_newstest2020_ende.tsv`
-   `data/details/en-de.txt`
-   `data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm`
-   `results/week10/model_data/mt_segment_level_original_outputs.csv`
-   `results/week10/model_data/segments_with_fixed_splits.csv`
-   `results/week10/model_data/train_segments.csv`
-   `results/week10/model_data/test_segments.csv`
-   `results/week10/priority2_3/serious_vote_counts_by_split.csv`
-   `results/week10/priority2_3/dev_model_predictions_with_votes.csv`

### Scripts

-   `src/build_model_dataset.py`
-   `src/split_by_document.py`
-   `src/freeze_week10_split.py`
-   `src/verify_locked_split.py`
-   `src/evaluate_test_week10.py`
-   `src/validate_week10.py`

### Test evaluation and audit outputs

-   `results/week10/test_evaluation/test_audit_notes.md`
-   `results/week10/test_evaluation/test_predictions.csv`
-   `results/week10/test_evaluation/test_point_metrics.csv`
-   `results/week10/test_evaluation/test_metrics_with_ci.csv`
-   `results/week10/test_evaluation/paired_difference_ci.csv`
-   `results/week10/error_analysis/test_predictions_with_mqm.csv`

### Additional files used for the example trace

-   Uploaded raw MQM annotation file
-   `independent_rater_votes.csv`

------------------------------------------------------------------------

**End of Phase 1 report.**
