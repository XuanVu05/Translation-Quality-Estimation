# Data README — Second Pair of Eyes

**Dataset:** WMT 2020 MQM English–German (`newstest2020`)  
**Language direction:** English → German  
**Primary annotation file:** `mqm_newstest2020_ende.tsv`

## 1. Data Directory Structure

```text
Data/
├── raw/
│   └── mqm_newstest2020_ende.tsv
├── details/
│   └── en-de.txt
├── official_wmt2020/
│   └── sgm/
│       └── newstest2020-ende-src.en.sgm
└── original_outputs/
    ├── newstest2020.en-de.eTranslation.737.txt
    ├── ...
    └── newstest2020.en-de.Tohoku-AIP-NTT.890.txt
```

The `original_outputs/` directory contains seven MT output files used by the project. Preserve their original filenames and the system-to-file mapping used by the alignment code.

## 2. Data Sources and Use Conditions

### 2.1 MQM Annotation TSV

- **File:** `Data/raw/mqm_newstest2020_ende.tsv`
- **Repository:** Google, [wmt-mqm-human-evaluation](https://github.com/google/wmt-mqm-human-evaluation)
- **Dataset:** MQM labels for English-to-German submissions of WMT `newstest2020`. The repository describes annotations containing error spans, categories, and severity, with three raters evaluating each segment.
- **Associated publication:** Freitag, M., Foster, G., Grangier, D., Ratnakar, V., Tan, Q., & Macherey, W. (2021). _Experts, Errors, and Context: A Large-Scale Study of Human Evaluation for Machine Translation_. arXiv:2104.14478. https://arxiv.org/abs/2104.14478
- **Use condition:** Cite the associated publication when using the annotation data. Public availability does not itself establish unrestricted redistribution rights. Retain attribution and follow the repository's applicable licence and terms.

### 2.2 WMT 2020 Source Text and System Outputs

- **Files:** `Data/official_wmt2020/` and `Data/original_outputs/`
- **Official WMT20 translation-task page:** https://www.statmt.org/wmt20/translation-task.html
- **Official WMT20 metrics-task page:** https://www.statmt.org/wmt20/metrics-task.html
- **Use condition:** WMT's task pages state that data released for the WMT20 news translation task may be used for research, subject to citation requirements and additional conditions attached to individual datasets. This is not unrestricted commercial or general-purpose redistribution permission. Respect the terms of the original data owners.

### 2.3 Document and Line Mapping File

- **File:** `Data/details/en-de.txt`
- **Role:** Mapping information used by the project to align document and line identifiers.
- **Provenance:** The supplied repository inventory identifies this file and its role, but does not establish an independent publisher or separate licence. Preserve it with the source context from which it was obtained. Do not redistribute it separately unless its source terms permit that use.

## 3. Dataset Description

The reported consolidated project dataset contains:

| Property                        |  Value |
| ------------------------------- | -----: |
| MT systems in project dataset   |      7 |
| Documents                       |    130 |
| Segments                        |  9,926 |
| Positive serious-error segments |  1,183 |
| Negative segments               |  8,743 |
| Positive prevalence             | 11.92% |

The broader MQM release description and the project's seven-system consolidated dataset refer to different scopes. Use the project-specific count of seven systems when describing these experiments.

## 4. Serious-Error Label Definition

The project's operational definition marks an annotation serious when:

1. Severity is `Major` and category begins with `Accuracy/`; or
2. Category is exactly `Non-translation!`.

A segment is positive when at least two of the three raters cast a serious vote. Otherwise, it is negative.

This is the project's operational definition, not the only possible definition of severe MQM errors.

## 5. Annotation Agreement

The project audit reports:

- Fleiss' Kappa: 0.290029
- Segments with disagreement among raters: 2,779 of 9,926
- Independent reconstruction of the primary labels matched all 9,926 segment labels

The agreement result indicates that rater disagreement is a material property of the labels. Model errors should therefore be interpreted in the context of annotation uncertainty.

## 6. Data Preparation and Alignment

The annotation TSV, mapping file, official source-side SGM data, and original MT outputs are aligned to construct the model-ready segment-level dataset.

Relevant code locations:

- `Code/config.py`: central project path configuration.
- `Code/src/`: data construction, document-level splitting, baselines, ablation, and evaluation.
- `Code/analysis/`: mapping, alignment, label, and qualitative error-analysis audits.
- `Code/experiments/`: exploratory and extended experiments.

Use the final commands and script entry points present in the submitted source tree. Archived scripts should not be treated as canonical execution entry points unless the final report explicitly identifies them as such.

## 7. Document-Level Data Split

| Partition | Documents |
| --------- | --------: |
| Train     |        90 |
| Dev       |        20 |
| Test      |        20 |
| **Total** |   **130** |

No document is shared between the three partitions. The reported Test partition contains 1,575 segments, including 162 positive segments (10.29% prevalence).

The split assignments should be taken from the submitted manifest files under the relevant `Results/week10/` directories, rather than reconstructed from aggregate counts.

## 8. Data Inventory

| Component           | Repository path                                          | Source and use condition                                                                     |
| ------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| MQM annotation TSV  | `Data/raw/mqm_newstest2020_ende.tsv`                     | Google WMT MQM repository; cite Freitag et al. (2021) and follow current repository terms.   |
| Mapping file        | `Data/details/en-de.txt`                                 | Provenance is not independently identified in the supplied inventory; retain source context. |
| Official source SGM | `Data/official_wmt2020/sgm/newstest2020-ende-src.en.sgm` | WMT20 task data; research use subject to citations and additional owner terms.               |
| Seven MT outputs    | `Data/original_outputs/`                                 | Follow WMT and individual data-owner conditions and citation requirements.                   |

## 9. Licensing, Copyright and Redistribution

The project uses data from multiple sources. Each component is subject to its own licensing terms, copyright conditions, and attribution requirements. No single licence is assumed to cover the entire `Data/` directory.

**WMT 2020 source data and translation-task resources.** According to the official WMT20 Translation Task terms, data released for the WMT20 news translation task may be used for research purposes. Users are required to cite the WMT20 shared-task overview paper and comply with any additional citation requirements imposed by individual dataset owners. Other uses require consultation with the original data owners.

**MQM annotation data.** The file `mqm_newstest2020_ende.tsv` is obtained from Google's `wmt-mqm-human-evaluation` repository. Users must cite Freitag et al. (2021), _Experts, Errors, and Context: A Large-Scale Study of Human Evaluation for Machine Translation_. The repository's software licence should not automatically be interpreted as a separate licence granting unrestricted redistribution rights for every underlying dataset.

**Machine-translation outputs.** The seven system-output files are associated with individual WMT20 submissions. Their use and redistribution must respect the relevant WMT conditions and any applicable restrictions imposed by the original system or data owners. The project does not assign a common open-source licence to all output files.

**Document and line mapping file.** The file `en-de.txt` is used for document and segment alignment. Its independent source and licence are not established by the available project documentation. It is therefore not assigned an invented licence.

**Redistribution policy.** The project is intended for academic research and educational demonstration. Raw data files should only be redistributed when their applicable terms permit it. Where redistribution is not permitted or cannot be established, the submission should retain the data source, filename, citation, and acquisition instructions without including the restricted raw file.

## 10. References

1. Freitag, M., Foster, G., Grangier, D., Ratnakar, V., Tan, Q., & Macherey, W. (2021). _Experts, Errors, and Context: A Large-Scale Study of Human Evaluation for Machine Translation_. arXiv:2104.14478. https://arxiv.org/abs/2104.14478
2. WMT20. _Translation Task_. https://www.statmt.org/wmt20/translation-task.html
3. WMT20. _Metrics Task_. https://www.statmt.org/wmt20/metrics-task.html
4. Google. _wmt-mqm-human-evaluation repository_. https://github.com/google/wmt-mqm-human-evaluation

**Prepared for:** Group 02 — CLC02  
**Project:** Second Pair of Eyes
