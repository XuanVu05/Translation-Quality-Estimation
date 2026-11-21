from pathlib import Path
import csv, hashlib, subprocess, sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MQM = ROOT / 'Data' / 'raw' / 'mqm_newstest2020_ende.tsv'
MAPPING = ROOT / 'Data' / 'details' / 'en-de.txt'
MODEL_DATA = ROOT / 'Results' / 'week10' / 'model_data' / 'mt_segment_level_original_outputs.csv'
OUT = ROOT / 'Report' / 'phase1_data_label_audit'
OUT.mkdir(parents=True, exist_ok=True)

KEYS = ['system', 'doc', 'doc_id', 'seg_id']
MT_SYSTEMS = {
    'eTranslation.737', 'Huoshan_Translate.832', 'Online-A.1574',
    'Online-B.1590', 'OPPO.1535', 'Tencent_Translation.1520',
    'Tohoku-AIP-NTT.890'
}

def sha256(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def git_lines(args):
    try:
        r = subprocess.run(['git', *args], cwd=ROOT, text=True,
                           capture_output=True, encoding='utf-8', errors='replace')
        return r.stdout.strip() or r.stderr.strip() or '(no output)'
    except Exception as e:
        return f'Git command unavailable: {e}'

for p in [MQM, MAPPING, MODEL_DATA]:
    if not p.is_file():
        raise FileNotFoundError(f'Missing required project file: {p}')

mqm = pd.read_csv(MQM, sep='\t', dtype=str, keep_default_na=False,
                  quoting=csv.QUOTE_NONE, encoding='utf-8')
required = set(KEYS + ['rater', 'source', 'target', 'category', 'severity'])
missing = required - set(mqm.columns)
if missing:
    raise ValueError(f'MQM columns missing: {sorted(missing)}')
for c in KEYS + ['rater', 'category', 'severity']:
    mqm[c] = mqm[c].astype(str).str.strip()
mqm = mqm[mqm['system'].isin(MT_SYSTEMS)].copy()
mqm['serious_error_row'] = (
    mqm['severity'].eq('Major') &
    (mqm['category'].str.startswith('Accuracy/', na=False) |
     mqm['category'].eq('Non-translation!'))
).astype(int)

# Deterministically choose a 2-of-3 majority case to show how majority is formed.
rater_votes = (mqm.groupby(KEYS + ['rater'], as_index=False)
                 .agg(serious_vote=('serious_error_row', 'max')))
segment_votes = (rater_votes.groupby(KEYS, as_index=False)
                 .agg(n_raters=('rater', 'nunique'), serious_votes=('serious_vote', 'sum')))
chosen = segment_votes[(segment_votes.n_raters == 3) & (segment_votes.serious_votes == 2)]
if chosen.empty:
    chosen = segment_votes[(segment_votes.n_raters == 3) & (segment_votes.serious_votes == 3)]
if chosen.empty:
    raise RuntimeError('No segment with 3 raters and a positive majority was found.')
chosen = chosen.sort_values(KEYS).iloc[0]
key = {k: str(chosen[k]) for k in KEYS}
ann = mqm
for k, v in key.items():
    ann = ann[ann[k].eq(v)]
ann = ann.copy()
rv = (ann.groupby('rater', as_index=False)
      .agg(serious_vote=('serious_error_row', 'max')))
y = int((int(rv.serious_vote.sum()) >= 2))
ann = ann.merge(rv, on='rater', how='left')

# Map MQM doc/doc_id to official WMT line and fetch original MT target.
mapping = pd.read_csv(MAPPING, sep=r'\s+', header=None,
    names=['line', 'testset', 'lang_pair', 'document_id', 'segment_id'],
    dtype=str, keep_default_na=False, encoding='utf-8')
mr = mapping[(mapping.document_id == key['doc']) & (mapping.segment_id == key['doc_id'])]
if len(mr) != 1:
    raise RuntimeError(f'Expected one mapping row for {key}, found {len(mr)}')
line_no = int(mr.iloc[0]['line'])
mt_file = ROOT / 'Data' / 'original_outputs' / f"newstest2020.en-de.{key['system']}.txt"
with mt_file.open('r', encoding='utf-8-sig') as f:
    mt_lines = [x.rstrip('\r\n') for x in f]
if line_no < 1 or line_no > len(mt_lines):
    raise RuntimeError(f'Mapped line {line_no} outside {mt_file.name} ({len(mt_lines)} lines)')
original_target = mt_lines[line_no - 1]

model = pd.read_csv(MODEL_DATA, dtype=str, keep_default_na=False, encoding='utf-8-sig')
model_match = model
for k, v in key.items():
    model_match = model_match[model_match[k].astype(str).eq(v)]
if len(model_match) != 1:
    model_target = None
    model_target_status = f'Expected one model-data row, found {len(model_match)}'
else:
    model_target = str(model_match.iloc[0]['target'])
    model_target_status = 'EXACT_MATCH' if model_target == original_target else 'MISMATCH'

# Source audit: within-segment consistency plus independent source corpus presence.
source_variants = ann['source'].nunique(dropna=False)
source_texts = sorted(set(ann['source'].astype(str).tolist()))
source_candidates = [
    ROOT / 'data' / 'sources' / 'newstest2020.en',
    ROOT / 'data' / 'newstest2020.en',
    ROOT / 'newstest2020.en',
    ROOT / 'original_sources' / 'newstest2020.en',
]
source_file = next((p for p in source_candidates if p.is_file()), None)

# Search only data/source-like folders for a plausible English source text file.
if source_file is None:
    for base in [ROOT / 'data', ROOT / 'original_sources']:
        if base.exists():
            candidates = list(base.rglob('*.en')) + list(base.rglob('*newstest2020*source*'))
            source_file = next((p for p in candidates if p.is_file()), None)
            if source_file:
                break
source_independent_status = 'NOT_FOUND_IN_PROJECT' if source_file is None else f'FOUND:{source_file.relative_to(ROOT)}'

# Marker audit. Raw MQM target intentionally contains reviewer span tags; model target should not.
marker_pattern = r'<\s*/?\s*v\s*>'
raw_target_marker_rows = int(mqm['target'].astype(str).str.contains(marker_pattern, regex=True, case=False).sum())
model_source_marker_rows = int(model['source'].astype(str).str.contains(marker_pattern, regex=True, case=False).sum())
model_target_marker_rows = int(model['target'].astype(str).str.contains(marker_pattern, regex=True, case=False).sum())
original_marker_lines = sum(bool(pd.Series([x]).str.contains(marker_pattern, regex=True, case=False).iloc[0]) for x in mt_lines)

# Write detailed outputs.
ann.to_csv(OUT / 'selected_case_raw_annotations.csv', index=False, encoding='utf-8-sig')
rv.to_csv(OUT / 'selected_case_rater_votes.csv', index=False, encoding='utf-8-sig')

lines = [
    'PHASE 1 – DATA AND LABEL AUDIT', '='*72,
    f"Selected segment key: {key}",
    f"MQM annotation rows for selected segment: {len(ann)}",
    f"Distinct raters: {rv.rater.nunique()}",
    f"Serious votes: {int(rv.serious_vote.sum())}/3",
    f"Recomputed y_primary: {y}",
    '', 'RATER-LEVEL VOTES', '-'*72,
]
for _, r in rv.sort_values('rater').iterrows():
    lines.append(f"{r['rater']}: serious_vote={int(r['serious_vote'])}")
lines += ['', 'RAW MQM ANNOTATIONS', '-'*72]
for _, r in ann.iterrows():
    lines.append(f"{r['rater']} | {r['category']} | {r['severity']} | serious_row={int(r['serious_error_row'])} | vote={int(r['serious_vote'])}")
    lines.append(f"  MQM target: {r['target']}")
lines += ['', 'SOURCE / MAPPING / ORIGINAL TARGET', '-'*72,
    f"MQM source variants within selected segment: {source_variants}",
    f"MQM source text: {source_texts[0] if source_texts else '(missing)'}",
    f"Independent WMT source text file: {source_independent_status}",
    f"Official mapping line: {line_no}",
    f"Original MT output file: {mt_file.relative_to(ROOT)}",
    f"Original MT target: {original_target}",
    f"Model-data target vs original MT target: {model_target_status}",
    '', 'REVIEWER MARKUP AUDIT', '-'*72,
    f"Raw MQM target rows containing <v>...</v> markers: {raw_target_marker_rows}/{len(mqm)}",
    f"Original MT output lines containing <v>...</v> markers: {original_marker_lines}/{len(mt_lines)}",
    f"Model input source rows containing markers: {model_source_marker_rows}/{len(model)}",
    f"Model input target rows containing markers: {model_target_marker_rows}/{len(model)}",
    'Interpretation: MQM target span tags are annotation markup. Model input target is sourced from original_outputs; confirm by exact target match above.',
    '', 'SOURCE FILE PROVENANCE', '-'*72,
    f"Mapping SHA-256: {sha256(MAPPING)}",
    f"Original MT output SHA-256: {sha256(mt_file)}",
    'Existing reports/source_file_manifest.csv records exact official-archive SHA-256 matches for the mapping and seven MT outputs; it does not list an independent English source-text file.',
    '', 'GIT HISTORY (read-only)', '-'*72,
    'Data/label/source history:',
    git_lines(['log', '--date=iso', '--format=%h | %ad | %s', '--', 'src/build_model_dataset.py', 'mqm_newstest2020_ende.tsv', 'data/details/en-de.txt', 'original_outputs']),
    '', 'Split/Test/error-analysis history:',
    git_lines(['log', '--date=iso', '--format=%h | %ad | %s', '--', 'src/split_by_document.py', 'src/evaluate_test_week10.py', 'results/week10/test_evaluation', 'results/week10/error_analysis']),
    '', 'GIT STATUS SUMMARY (read-only)', '-'*72,
    git_lines(['status', '--short']).splitlines()[0:30].__str__(),
    '', 'LIMITATIONS', '-'*72,
    '- This script does not modify source data, model data, splits, predictions, or model files.',
    '- Source consistency across MQM raters is not the same as independent verification against the official WMT English source corpus.',
    '- If independent source text is absent, obtain the official newstest2020 English source file and rerun this audit after placing it in the project.',
]
(OUT / 'phase1_data_label_audit_report.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
print('\nOUTPUT DIRECTORY:', OUT)
print('FILES: phase1_data_label_audit_report.txt, selected_case_raw_annotations.csv, selected_case_rater_votes.csv')
