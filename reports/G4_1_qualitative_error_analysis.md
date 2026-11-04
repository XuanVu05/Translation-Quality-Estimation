# G4.1 – Qualitative Error Analysis of High-Ranked Non-Critical Predictions

## 1. Objective

This analysis investigates ten high-ranked development-set examples selected from the Logistic Regression baseline (LR_Base). All ten examples were assigned the primary label `y_primary = 0`, meaning that none met the project's operational definition of a Critical Error.

The purpose is not to establish that these translations are incorrect. Instead, the analysis examines why the model assigns high priority to segments that are not labelled as critical, and whether these cases reveal minor translation problems, stylistic weaknesses, annotation disagreement, or limitations of the MQM-based target label.

The analysis uses three complementary sources of evidence:

1. Original English source and German MT output.
2. MQM annotations that match the normalized target translation.
3. Context from adjacent segments where available.

No model was retrained, and no Test-set observations were used.

## 2. Evidence matching and validation

The ten selected cases were matched against the original MQM annotation file and the official original MT outputs.

| Audit item                             | Result |
| -------------------------------------- | -----: |
| Selected system-segment cases          |     10 |
| Candidate MQM annotation rows          |     47 |
| Target-matched annotation rows         |     42 |
| Target-unmatched annotation rows       |      5 |
| Cases with target-matched annotations  |  10/10 |
| Original MT mapping checks passed      |  10/10 |
| Development target matches original MT |  10/10 |
| Recomputed serious annotation rows     |      0 |
| Recomputed serious votes               |      0 |
| Cases with recomputed `y_primary = 1`  |      0 |

The five target-unmatched annotation rows were retained in a separate audit file. They were not used to extract annotated spans or support the primary qualitative interpretation. A target-unmatched annotation is not necessarily invalid; it may refer to another target variant associated with the same system-segment key.

The serious-error rule was independently reapplied:

- Severity must be `Major`.
- Category must start with `Accuracy/` or equal `Non-translation!`.
- Serious votes are aggregated by distinct rater.
- The primary label is positive when at least two raters provide a serious vote.

All ten cases remained negative under this rule.

## 3. Case-level qualitative analysis

### Case 1 – Online-B.1590, abcnews.363994

**Source**

" Court documents say the surgeon was leaving a Walmart store when he was confronted by an armed man and shoved into a van. They say he was tortured for hours before being returned to his car while unconscious. Surveillance video supports the chain of events. Investigators say Nkorina's wife was a client of the surgeon."

**MT output**

"Gerichtsdokumente besagen, dass der Chirurg ein Walmart-Geschäft verließ, als er von einem bewaffneten Mann konfrontiert und in einen Van geschoben wurde. Man sagt, er wurde stundenlang gefoltert, bevor er bewusstlos zu seinem Auto zurückgebracht wurde. Das Überwachungsvideo unterstützt die Ereigniskette. Die Ermittler sagen, Nkorinas Frau sei eine Klientin des Chirurgen gewesen."

**MQM evidence**

- Six target-matched annotation rows from two raters.
- Five candidate annotation rows did not match the normalized target.
- Matched categories include `Accuracy/Mistranslation` and `Style/Awkward`.
- All matched annotations have Minor severity.
- No target-matched Major annotation was found.

**Qualitative assessment**

The expression "Man sagt" is a relatively general rendering of "They say" and may weaken the connection to the preceding reference to court documents. The expressions "Walmart-Geschäft", "konfrontiert", "unterstützt" and "Klientin" were also marked by annotators.

These observations suggest lexical and stylistic weaknesses rather than a demonstrated critical change in the event sequence. The Major annotation found among the five target-unmatched rows must not be attributed to the current target.

**Interpretation:** A high-ranked example containing several minor annotation issues, but no target-matched evidence of a Critical Error.

### Case 2 – eTranslation.737, standard.co.uk.14516

**Source**

"Mac Miller death: Third man charged with drug offences"

**MT output**

"Mac-Miller-Tod: Dritter Mann wegen Drogendelikten angeklagt"

**MQM evidence**

- Three target-matched annotation rows.
- Three raters.
- All annotations use category `Style/Awkward`.
- Two annotations are Minor and one is Major.

**Qualitative assessment**

The compound "Mac-Miller-Tod" may sound compressed or awkward as a German headline. However, the Major annotation belongs to `Style/Awkward`, not to the project's critical category set.

This case demonstrates that severity alone is insufficient to determine whether a segment is a Critical Error. The category and severity must be considered together.

**Interpretation:** A stylistic issue with one Major annotation, but no operational Critical Error.

### Cases 3–9 – Seven MT systems translating the same source segment

**Source**

"Allen's family pays nearly $12,000 per year for Amari to attend the school, which made headlines earlier this year after Karen Pence took an art teaching job at the famously anti-LGBTQ institution."

These seven cases correspond to the same source document and segment, `cbsnews.302129`, `doc_id=10`, `seg_id=763`, but have different MT systems and outputs.

| Case | MT system                | LR_Base rank | Matched MQM evidence                  |
| ---: | ------------------------ | -----------: | ------------------------------------- |
|    3 | Online-B.1590            |            3 | Minor Style, Minor Accuracy, No-error |
|    4 | OPPO.1535                |            6 | Minor Fluency, Accuracy and Style     |
|    5 | Online-B.1590            |            8 | Minor Fluency, Accuracy and Style     |
|    6 | Huoshan_Translate.832    |            9 | Minor Fluency, Accuracy and Style     |
|    7 | eTranslation.737         |           10 | Minor Fluency, Accuracy and Style     |
|    8 | Tencent_Translation.1520 |           11 | Minor Fluency, Accuracy and Style     |
|    9 | Online-A.1574            |           13 | Minor Fluency, Accuracy and Style     |

**Qualitative assessment**

Several systems use constructions similar to:

"für Amari, um die Schule zu besuchen"

This construction is understandable, but may be less idiomatic than a formulation such as:

"damit Amari die Schule besuchen kann"

Another possible formulation is:

"für Amaris Schulbesuch"

The Online-B output also uses a more nominalized construction:

"für den Besuch der Schule durch Amari"

This is understandable but comparatively cumbersome.

The annotations repeatedly identify spans around "um", "was" and "um die Schule zu besuchen". This indicates that annotators noticed recurring fluency or stylistic weaknesses across different system outputs.

The Online-A output uses "Kunstlehrjob", which was marked as an Accuracy/Mistranslation Minor issue. This lexical choice deserves attention, although the annotation does not establish a critical semantic error.

**Interpretation**

The seven outputs show how different MT systems can produce different realizations of the same source segment while exhibiting similar minor fluency and style issues.

This group is especially useful for system-level comparison. However, these are seven system-segment observations, not seven independent source segments. They must not be counted as seven independent examples when discussing generalization.

### Case 5 – Online-B.1590, cbsnews.302129

**Source**

"According to WUSA, one of the boys allegedly covered Amari's mouth while another held her hands behind her back and a third took a pair of scissors to her dreadlocks."

**MT output**

"Laut WUSA bedeckte einer der Jungen angeblich Amaris Mund, während ein anderer ihre Hände hinter dem Rücken hielt und ein dritter eine Schere zu ihren Dreadlocks nahm."

**MQM evidence**

- Five target-matched annotation rows.
- Three raters.
- Categories include `Fluency/Grammar`, `Accuracy/Mistranslation` and `Style/Awkward`.
- All annotations have Minor severity.

**Qualitative assessment**

The expression "eine Schere zu ihren Dreadlocks nahm" appears to follow the English idiom "took a pair of scissors to her dreadlocks" quite literally. The German output communicates the presence of scissors but does not express the cutting action as directly as the English source.

A more explicit German formulation could be:

"... und ein dritter schnitt ihr mit einer Schere die Dreadlocks ab."

This is a useful example of a potentially overly literal translation. The MQM annotations identify the relevant phrase, but do not classify it as a Critical Error.

**Interpretation:** A minor translation-quality issue involving idiomatic meaning and natural expression, not a confirmed Critical Error.

### Case 10 – Huoshan_Translate.832, seattle_times.7755

**Source**

"Brown has been accused of sexual misconduct by two women. He was released by the New England Patriots last week after playing only one game. He's been dumped by three teams in the last six months."

**MT output**

"Brown wurde von zwei Frauen des sexuellen Fehlverhaltens beschuldigt. Er wurde letzte Woche von den New England Patriots entlassen, nachdem er nur ein Spiel gespielt hatte. Er wurde in den letzten sechs Monaten von drei Teams entlassen."

**MQM evidence**

- Four target-matched annotation rows.
- Three raters.
- One `Style/Awkward` Minor annotation for "Teams".
- One `Style/Awkward` Neutral annotation for "gespielt".
- Two No-error annotations.

**Qualitative assessment**

The word "Teams" is an English loanword commonly encountered in German sports contexts. One annotator marked it as a minor stylistic issue, while other annotations include No-error. This is an example of annotation variation rather than clear evidence of a translation failure.

The phrase "von drei Teams entlassen" conveys the main idea that Brown was released by three teams during the stated period.

**Interpretation:** A low-severity stylistic observation with explicit No-error evidence from other raters. It should not be treated as a critical translation problem.

## 4. Cross-case findings

The ten cases reveal several recurring patterns.

### 4.1 Minor errors can contribute to high model rankings

The selected examples contain minor issues involving lexical choice, fluency, awkward phrasing and literal translation. These issues may contribute to model scores even when the corresponding segment does not meet the operational Critical Error threshold.

This is consistent with the role of the model as a prioritization mechanism rather than an automatic error adjudicator.

### 4.2 Severity and criticality are not interchangeable

Case 2 contains a Major annotation, but its category is `Style/Awkward`. Under the project's label definition, it does not qualify as a Critical Error.

This reinforces the need to define the target label using both category and severity.

### 4.3 Annotator disagreement affects interpretation

Cases 3 and 10 contain both error annotations and No-error annotations. Such disagreement indicates that not every perceived translation-quality issue is consistently assessed by all raters.

A binary label can therefore conceal differences in individual judgments and annotation granularity.

### 4.4 Target matching is necessary for reliable evidence attribution

Case 1 contains five candidate annotation rows that do not match the normalized target. Including those rows in the primary analysis would incorrectly attribute annotations from another target variant to the selected translation.

The analysis therefore uses target-matched annotations as the primary evidence and retains unmatched rows separately for transparency.

### 4.5 Repeated source segments require careful counting

Cases 3–9 represent seven MT system outputs for one source segment. This enables a useful comparison of system-specific translation behavior, but does not provide seven independent source-level observations.

The ten cases correspond to five unique source segments across four source documents: Case 1, Case 2, the segment shared by Cases 3, 4, 6, 7, 8 and 9, Case 5, and Case 10.

## 5. Implications for the Second Pair of Eyes system

The findings support three practical conclusions.

First, a high model score should be interpreted as a review-priority signal, not as proof of a critical translation error.

Second, the system's false positives may still contain useful information about minor translation-quality problems. A human reviewer can decide whether these issues deserve attention under the available review budget.

Third, the model and the MQM label definition serve different purposes. The model ranks segments based on learned patterns, while the operational label defines which errors count as critical. Their disagreement is therefore an important object of analysis rather than something that should be hidden.

## 6. Limitations

This analysis has several limitations.

1. The ten cases were selected from the highest-ranked LR_Base development predictions and are not a random sample.
2. All ten cases have `y_primary = 0`; therefore, this analysis does not characterize model behavior on true positive cases.
3. Seven cases share one source segment, limiting source-level diversity.
4. Five candidate annotation rows do not match the selected target and are excluded from the primary annotation interpretation.
5. MQM annotations represent human judgments and may contain disagreement.
6. The independent linguistic observations in this report are qualitative assessments by the project team, not a separate expert adjudication.
7. No conclusion about generalization to unseen languages, domains, or MT systems can be drawn from these ten cases.

## 7. Conclusion

The qualitative analysis shows that high-ranked non-critical predictions are not necessarily error-free translations. Several contain minor accuracy, fluency or stylistic issues, while others show annotator disagreement or no-error judgments.

The findings highlight an important distinction between identifying translation-quality weaknesses and detecting operationally defined Critical Errors. The Second Pair of Eyes system should therefore be positioned as a human-in-the-loop prioritization tool. Its purpose is to help reviewers decide which segments to inspect first, not to replace human judgment or automatically declare a translation incorrect.

The analysis is based on the current authoritative ten-case selection and uses only target-matched MQM annotations as primary annotation evidence. All unmatched annotations are retained separately for auditability.
