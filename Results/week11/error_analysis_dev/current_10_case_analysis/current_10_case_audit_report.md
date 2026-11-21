# Current 10-Case MQM Audit

## Input provenance
- Selected cases: `results\week11\error_analysis_dev\dev_top20_error_analysis_10_cases.csv`
- MQM file SHA-256: `22acb4d5cc4dc0d8f2683e9251c179c917ae8589d71b1945d755c46d88d345e3`
- Selected CSV SHA-256: `f743693afbeb09164ce15f5c88986b8269b5eccdbc8b1808d07928dd55b6b7d2`

## Matching results
- Selected cases: 10
- Cases with target-matched annotations: 10
- Candidate annotation rows: 47
- Target-matched annotation rows: 42
- Target-unmatched annotation rows: 5

## Operational label validation
- Serious annotation rows: 0
- Recomputed serious votes: 0
- Cases with recomputed y_primary = 1: 0

## Original MT verification
- Mapping checks passed: 10/10
- Dev target matches original MT: 10/10

## Important interpretation limits
- Target-unmatched annotations are retained separately.
- Target-unmatched does not mean annotation is invalid.
- Annotated spans are extracted from target-matched rows only.
- MQM annotation is not equivalent to manual semantic judgment.
- Manual assessment fields are intentionally left pending.
- No model was retrained and no Test data was used.

## Per-case summary

 case                   system                  doc  doc_id  seg_id  matched_annotation_rows  unmatched_annotation_rows  matched_raters  major_annotation_rows  serious_votes_recomputed  y_primary_recomputed
    1            Online-B.1590       abcnews.363994       5    1317                        6                          5               2                      0                         0                     0
    2         eTranslation.737 standard.co.uk.14516       1    1386                        3                          0               3                      1                         0                     0
    3            Online-B.1590       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
    4                OPPO.1535       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
    5            Online-B.1590       cbsnews.302129       5     758                        5                          0               3                      0                         0                     0
    6    Huoshan_Translate.832       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
    7         eTranslation.737       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
    8 Tencent_Translation.1520       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
    9            Online-A.1574       cbsnews.302129      10     763                        4                          0               3                      0                         0                     0
   10    Huoshan_Translate.832   seattle_times.7755       4      38                        4                          0               3                      0                         0                     0
