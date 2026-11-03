# G1.2 -- Data Structure and Quality Audit

**Project:** Second Pair of Eyes -- Reference-Free Critical Error
Detection\
**Dataset:** WMT 2020 MQM English→German (`newstest2020`)\
**Status:** Completed for structural, source, rater-coverage,
target-normalization, and MT-output alignment checks.

## 1. Purpose

This audit checks the MQM dataset structure, completeness, annotation
multiplicity, source consistency, target normalization, and alignment
between MQM annotations and the seven original MT outputs.

## 2. Dataset structure

The MQM TSV contains **79,020 rows and 9 columns**: `system`, `doc`,
`doc_id`, `seg_id`, `rater`, `source`, `target`, `category`, and
`severity`.

The mapping file `data/details/en-de.txt` contains 1,418 segments across
130 documents.

There are 10 systems: - 7 MT: `eTranslation.737`,
`Huoshan_Translate.832`, `Online-A.1574`, `Online-B.1590`, `OPPO.1535`,
`Tencent_Translation.1520`, `Tohoku-AIP-NTT.890`. - 3 Human:
`Human-A.0`, `Human-B.0`, `Human-P.0`.

There are 6 distinct rater identifiers.

## 3. Completeness and duplicates

  Check                            Result
  ------------------------------ --------
  MQM rows                         79,020
  Missing values                        0
  Exact duplicate rows                  0
  Mapping rows                      1,418
  Mapping duplicate rows                0
  Mapping duplicate line IDs            0
  Documents                           130
  Unique system-segment groups     14,180

The initial audit found 36,481 repeated annotation keys. These are not
exact duplicate rows. They represent multiple annotation records for the
same system-document-segment-rater key. Do not drop these rows as
duplicates.

## 4. Annotation structure and rater coverage

  Measure                                                      Result
  ---------------------------------------------------------- --------
  Annotation groups `(system, doc, doc_id, seg_id, rater)`     42,539
  Groups with more than one annotation row                     17,708
  Maximum rows in one rater-segment group                           9
  Groups with multiple categories                              13,870
  Groups with multiple severities                               5,281
  Source-inconsistent segments                                      0

A rater may record multiple errors for one segment. Label generation
must aggregate rows within each rater-segment before counting rater
votes.

One segment has only two raters: - System: `Online-A.1574` - Document:
`sky.com.20669` - Global `seg_id`: 1161 - Raters: `rater2`, `rater6` -
Recorded annotations: `Fluency/Punctuation`, `Minor`.

The other 14,179 system-segment groups have three raters. The two-rater
case must be handled explicitly.

## 5. Source consistency

There are **zero source-inconsistent segments** across systems for the
same document and segment.

## 6. Target normalization

Removing MQM `<v>` and `</v>` tags and normalizing whitespace gives:

  Status                    All systems    Share
  ----------------------- ------------- --------
  Markup-only variation           9,654   68.08%
  Content variation               2,733   19.27%
  No variation                    1,793   12.64%

By system type:

  Type      System-segments   Multiple normalized targets     Rate
  ------- ----------------- ----------------------------- --------
  Human               4,254                           650   15.28%
  MT                  9,926                         2,083   20.99%

A within-rater check found 1,061 system-segments where at least one
rater had multiple normalized target strings. These string differences
cannot automatically be interpreted as distinct original translations.

## 7. MQM-to-original-MT mapping

The correct mapping is: - `MQM.doc` → `mapping.document_id` -
`MQM.seg_id` → `mapping.line_id`

`mapping.segment_id` is a document-local segment index (1--26), not the
global segment identifier in MQM.

The corrected mapping achieved: - MQM annotation rows: 79,020 - Matched
rows: 79,020 - Unmatched rows: 0 - MT systems checked: 7 - MT
system-segments: 9,926

## 8. Annotated target versus original MT output

Comparison removed `<v>` tags and normalized whitespace, then compared
unique MQM target strings against the corresponding original MT output.

  Status                                     System-segments      Share
  ---------------------------------------- ----------------- ----------
  All annotation targets match original                7,838     78.93%
  Some annotation targets match original               2,072     20.87%
  No annotation target matches original                   16      0.16%
  **Total**                                        **9,926**   **100%**

  MT system                    All match   Some match   None match   All-match rate
  -------------------------- ----------- ------------ ------------ ----------------
  eTranslation.737                 1,134          284            0           79.97%
  Huoshan_Translate.832            1,118          299            1           78.84%
  Online-A.1574                    1,064          351            3           75.04%
  Online-B.1590                    1,067          348            3           75.25%
  OPPO.1535                        1,173          241            4           82.72%
  Tencent_Translation.1520         1,149          267            2           81.03%
  Tohoku-AIP-NTT.890               1,133          282            3           79.90%

The `any_match_rate` ranges from 99.72% to 100%. Thus, almost every
system-segment has at least one MQM target matching the original output.

The 16 `None match` cases comprise 11 segments with multiple normalized
targets and 5 with one normalized target. Examples include repeated
words, spacing differences, and punctuation changes. Removing span tags
alone does not always restore the original target.

Cross-tabulation:

  -----------------------------------------------------------------------
  Comparison status       One normalized target       Multiple normalized
                                                                  targets
  ------------------- ------------------------- -------------------------
  All match                               7,838                         0

  Some match                                  0                     2,072

  None match                                  5                        11
  -----------------------------------------------------------------------

## 9. Decisions for the CED pipeline

1.  Use the **original MT output files** as the authoritative target
    text for feature extraction.
2.  Do not use MQM annotated `target` strings as the feature-extraction
    source; annotation markup and text variations may contaminate
    lexical and surface features.
3.  Retain MQM `category` and `severity` for label construction.
4.  Aggregate multiple annotation rows within each rater and
    system-segment before counting votes.
5.  Do not remove repeated annotation keys as duplicates; exact
    duplicate rows were zero.
6.  Handle the one two-rater segment explicitly.
7.  Do not drop the 16 mismatching segments solely because annotated
    target strings differ; original MT outputs are available.
8.  Use the verified mapping `doc + seg_id` → `document_id + line_id`.

## 10. Limitations

-   The comparison is exact string matching after removing `<v>` tags
    and normalizing whitespace; it is not a semantic equivalence test.
-   The 16 `None match` cases have not all been manually adjudicated.
-   The two-rater exception has not yet been evaluated under the final
    Critical Error label rule.
-   This audit does not validate the final label definition, vote
    aggregation, class distribution, or train/dev/test leakage controls.
-   The audit identifies string differences but does not prove their
    cause.

## 11. Conclusion

The dataset is structurally complete for the audited fields: no missing
values or exact duplicate rows were found, source text is consistent
across systems, and all MQM rows map to the official segment mapping
using the verified global line identifier.

The main risks are annotation multiplicity and annotated-target
variation. The CED pipeline should use original MT outputs for target
features and aggregate MQM annotations carefully at the rater-segment
level before constructing labels.

**G1.2 status: completed for the checks listed above. Proceed to G1.3 --
Critical Error label audit.**
