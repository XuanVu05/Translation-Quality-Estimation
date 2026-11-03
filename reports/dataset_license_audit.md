# Dataset Provenance and License Audit

## 1. MQM Annotation Dataset

- Dataset: WMT 2020 MQM English-German
- Local file: mqm_newstest2020_ende.tsv
- Source repository:
  https://github.com/google/wmt-mqm-human-evaluation
- Dataset path in source repository:
  newstest2020/ende/mqm_newstest2020_ende.tsv
- Repository license: Apache License 2.0
- Repository README identifies the MQM labels as annotations
  for 10 WMT 2020 English-German submissions.
- The repository states that its contents are not an official
  Google product.
- Local SHA-256:
  22ACB4D5CC4DC0D8F2683E9251C179C917AE8589D71B1945D755C46D88D345E3
- Local Git status: tracked from the initial project commit.
- Exact source-file hash comparison: PENDING.

## 2. WMT 2020 Mapping

- Local file: data/details/en-de.txt
- Source: WMT 2020 data release (reported by the project team).
- Purpose: document and segment alignment.
- Local SHA-256:
  5364B05190E9914A361DEE960FE8E376CA6762CCE08A5D577A3CEEE970146FA8
- Mapping integrity audit:
  1,418 rows; 130 documents; no duplicate line IDs;
  all 9,926 MT system-segment keys matched.
- Exact source archive and hash: PENDING.

## 3. Original MT Outputs

- Local directory: original_outputs/
- Source: WMT 2020 data release (reported by the project team).
- Number of MT systems: 7
- Lines per output file: 1,418
- Local SHA-256 fingerprints: recorded in the audit log.
- Exact source archive and hash comparison: PENDING.

## 4. Usage Conditions

The WMT 2020 News Translation Task states that released
task data may be freely used for research, provided that
the WMT20 shared task overview paper is cited and any
additional dataset-specific citation requirements are respected.

The MQM repository publishes an Apache License 2.0 file.
This repository-level license must not automatically be
assumed to override third-party rights in source texts,
test sets, or system outputs.

The project is currently used for academic research.

The project repository is private. Raw dataset files are
tracked in Git. Public redistribution is not planned until
the relevant permissions and attribution requirements
have been verified.

## 5. Required Citations

1. WMT 2020 Translation Task:
   https://www.statmt.org/wmt20/translation-task.html

2. Google WMT MQM Human Evaluation:
   https://github.com/google/wmt-mqm-human-evaluation

3. WMT 2020 Shared Task Overview:
   Findings of the 2020 Conference on Machine Translation.

4. MQM study:
   Freitag et al. (2021), Experts, Errors, and Context:
   A Large-Scale Study of Human Evaluation for Machine Translation.

## 6. Outstanding Checks

- [ ] Verify local MQM file against official GitHub file.
- [ ] Identify exact WMT archive used for mapping.
- [ ] Identify exact WMT archive used for original outputs.
- [ ] Compare local file hashes against official source files.
- [ ] Confirm dataset-specific attribution requirements.
- [ ] Preserve source and license notices where applicable.

## 7. Audit Status

Status: IN PROGRESS

Research use is supported by the cited WMT data policy.
Exact local-to-official file identity and component-level
redistribution conditions remain to be verified.

## WMT 2020 English-German Data Provenance Verification

### Official archive

- Archive: `newstest2020txt-v2.tar.gz`
- Source: WMT 2020 Metrics Task data archive
- Local audit copy: `D:\WMT20_OFFICIAL_AUDIT\newstest2020txt-v2.tar.gz`
- Archive SHA-256:
  `98131534F0962CC2A050C7CDFA6CAC63EA94349248C912E0F4EA77F6650C547D`

### File-level integrity verification

The local mapping file and all seven selected English-German MT system outputs
were compared against their corresponding files extracted from the WMT 2020
archive using SHA-256.

Result: 8 of 8 files matched exactly.

Verified components:

- `txt/details/en-de.txt`
- `eTranslation.737`
- `Huoshan_Translate.832`
- `Online-A.1574`
- `Online-B.1590`
- `OPPO.1535`
- `Tencent_Translation.1520`
- `Tohoku-AIP-NTT.890`

The complete local and archive SHA-256 values are recorded in
`source_file_manifest.csv`.

### Scope and limitations

This verification establishes byte-level identity between the eight local
files and their counterparts in the downloaded WMT 2020 archive.

It does not independently establish licensing permissions, redistribution
rights, or ownership of the system outputs. These matters require separate
review of the relevant dataset terms and notices.

## Dataset Provenance and License Audit

### 1. MQM Annotation Dataset

**Source repository:** `https://github.com/google/wmt-mqm-human-evaluation`

**Dataset file:** `newstest2020/ende/mqm_newstest2020_ende.tsv`

**Verification:**

- The local MQM TSV was compared against the corresponding file in the source repository using SHA-256.
- Result: `EXACT MATCH`.
- Repository HEAD at the time of audit: `29acd6999aaea3586378c9dcb58d8cc4820cede3`.

**License information:**

- The repository contains a root-level `LICENSE` file specifying Apache License 2.0.
- The root-level `README.md` was downloaded and retained as audit evidence.
- No root-level `NOTICE` or `COPYING` file was found.
- The license of individual third-party components, if any, has not been independently established.

**SHA-256:**

- LICENSE: `CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30`
- README: `7BE8CB98BAD32DA2437F2BC59310C0BFD517B02F13BE27185085B2FF0F8327C4`

**License assessment:**

The repository provides an Apache License 2.0 file. This is evidence of the repository's stated licensing terms. However, the audit does not independently establish that every annotation or third-party component is owned by the repository maintainers or covered without additional restrictions. Redistribution permissions for the MQM data should therefore be interpreted with this limitation.

### 2. WMT 2020 English-German Mapping and MT Outputs

**Source:** WMT 2020 Metrics Task data archive.

**Archive:** `newstest2020txt-v2.tar.gz`

**Archive SHA-256:**
`98131534F0962CC2A050C7CDFA6CAC63EA94349248C912E0F4EA77F6650C547D`

**Verification method:** SHA-256 comparison between local project files and corresponding files extracted from the archive.

**Result:** 8/8 files matched exactly:

- `txt/details/en-de.txt`
- `eTranslation.737`
- `Huoshan_Translate.832`
- `Online-A.1574`
- `Online-B.1590`
- `OPPO.1535`
- `Tencent_Translation.1520`
- `Tohoku-AIP-NTT.890`

Full file paths and SHA-256 values are recorded in `source_file_manifest.csv`.

**License limitation:** The archive-level integrity check does not establish redistribution permissions. Separate licensing or usage terms for WMT data and individual system outputs have not yet been conclusively verified.

### 3. Audit Limitations and Responsible Use

- Exact file matching establishes byte-level identity, not ownership or licensing rights.
- Repository-level licensing should not automatically be interpreted as proof that every third-party component is covered.
- WMT archive provenance and the MQM repository license are treated as separate matters.
- No claim of unrestricted redistribution is made.
- The project should retain source attribution, license references, and the verification manifest.
- Any public redistribution of the dataset or original MT outputs requires further review of the applicable terms.

### 4. Audit Evidence

Evidence retained under `D:\WMT20_OFFICIAL_AUDIT`:

- `newstest2020txt-v2.tar.gz`
- `MQM_LICENSE`
- `MQM_README.md`
- `MQM_REPO_ROOT.json`
- Extracted WMT 2020 archive files

Project evidence:

- `reports/source_file_manifest.csv`
- `reports/dataset_license_audit.md`
