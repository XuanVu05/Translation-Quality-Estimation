import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Translation Quality Estimation")
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
DETAILS_PATH = ROOT / "data" / "details" / "en-de.txt"
OUTPUT_DIR = ROOT / "original_outputs"
RESULT_DIR = ROOT / "results" / "week10" / "model_data"
AUDIT_DIR = ROOT / "results" / "week10" / "data_quality"

SYSTEMS = {
    "eTranslation.737",
    "Huoshan_Translate.832",
    "Online-A.1574",
    "Online-B.1590",
    "OPPO.1535",
    "Tencent_Translation.1520",
    "Tohoku-AIP-NTT.890",
}

RESULT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Read MQM annotations
mqm = pd.read_csv(
    MQM_PATH,
    sep="\t",
    dtype=str,
    keep_default_na=False,
    quoting=3,
)

required = {
    "system", "doc", "doc_id", "seg_id",
    "rater", "source", "category", "severity"
}
missing = required - set(mqm.columns)
if missing:
    raise ValueError(f"Missing MQM columns: {sorted(missing)}")

mqm["system"] = mqm["system"].str.strip()
mqm["doc"] = mqm["doc"].str.strip()
mqm["doc_id"] = mqm["doc_id"].str.strip()
mqm["seg_id"] = mqm["seg_id"].str.strip()
mqm["rater"] = mqm["rater"].str.strip()
mqm["category"] = mqm["category"].str.strip()
mqm["severity"] = mqm["severity"].str.strip()

mqm = mqm[mqm["system"].isin(SYSTEMS)].copy()

# 2. Apply the predefined serious-error rule at annotation-row level
is_serious_error = (
    mqm["severity"].eq("Major")
    & (
        mqm["category"].str.startswith("Accuracy/", na=False)
        | mqm["category"].eq("Non-translation!")
    )
)
mqm["serious_error_row"] = is_serious_error.astype(int)

# One vote per rater per system/segment: any qualifying error means vote=1
keys = ["system", "doc", "doc_id", "seg_id"]
rater_votes = (
    mqm.groupby(keys + ["rater"], as_index=False)
    .agg(serious_vote=("serious_error_row", "max"))
)

labels = (
    rater_votes.groupby(keys, as_index=False)
    .agg(
        distinct_raters=("rater", "nunique"),
        serious_votes=("serious_vote", "sum"),
    )
)
labels["y_primary"] = (labels["serious_votes"] >= 2).astype(int)

# 3. Obtain one source sentence per segment and audit source consistency
source_audit = (
    mqm.groupby(keys)["source"]
    .nunique()
    .rename("n_source_variants")
    .reset_index()
)
source_audit.to_csv(
    AUDIT_DIR / "source_variants_by_segment.csv", index=False
)

source_rows = (
    mqm.groupby(keys, as_index=False)
    .agg(source=("source", "first"))
)

# 4. Read official line mapping
details = pd.read_csv(
    DETAILS_PATH,
    sep=r"\s+",
    header=None,
    names=["line", "testset", "lang_pair", "document_id", "segment_id"],
    dtype=str,
)
details["line"] = details["line"].astype(int)
details["document_id"] = details["document_id"].str.strip()
details["segment_id"] = details["segment_id"].str.strip()

# 5. Load each system's original output, indexed by official line number
output_records = []
for path in sorted(OUTPUT_DIR.glob("newstest2020.en-de.*.txt")):
    system = path.name.removeprefix("newstest2020.en-de.").removesuffix(".txt")
    if system not in SYSTEMS:
        continue

    with path.open("r", encoding="utf-8-sig") as f:
        translations = [line.rstrip("\r\n") for line in f]

    if len(translations) != len(details):
        raise ValueError(
            f"{path.name}: {len(translations)} lines; "
            f"expected {len(details)}"
        )

    for _, row in details.iterrows():
        output_records.append({
            "system": system,
            "doc": row["document_id"],
            "doc_id": row["segment_id"],
            "line": row["line"],
            "target": translations[row["line"] - 1],
        })

outputs = pd.DataFrame(output_records)

# 6. Join labels, source and actual MT outputs
dataset = labels.merge(
    source_rows, on=keys, how="left", validate="one_to_one"
)
dataset = dataset.merge(
    outputs,
    on=["system", "doc", "doc_id"],
    how="left",
    validate="one_to_one",
)

# Verify that every labeled segment has a translation and source
if dataset["target"].isna().any():
    missing_rows = dataset[dataset["target"].isna()]
    missing_rows.to_csv(AUDIT_DIR / "missing_output_rows.csv", index=False)
    raise ValueError(
        f"{len(missing_rows)} labeled segments have no mapped MT output."
    )

if dataset["source"].isna().any():
    raise ValueError("Some segments have missing source text.")

# Keep the label rule fixed; report unexpected rater counts for review
if not dataset["distinct_raters"].eq(3).all():
    dataset.loc[
        ~dataset["distinct_raters"].eq(3)
    ].to_csv(AUDIT_DIR / "segments_not_three_raters.csv", index=False)

columns = [
    "system", "doc", "doc_id", "seg_id", "line",
    "source", "target", "distinct_raters", "serious_votes", "y_primary"
]
dataset = dataset[columns].sort_values(
    ["system", "line"]
).reset_index(drop=True)

out_path = RESULT_DIR / "mt_segment_level_original_outputs.csv"
dataset.to_csv(out_path, index=False, encoding="utf-8-sig")

print("=== DATASET CREATED ===")
print("Saved:", out_path)
print("Rows:", len(dataset))
print("Systems:", dataset["system"].nunique())
print("Unique documents:", dataset["doc"].nunique())
print("Distinct segment IDs per system:",
      dataset.groupby("system")["line"].nunique().to_dict())
print("Missing source:", int(dataset["source"].isna().sum()))
print("Missing target:", int(dataset["target"].isna().sum()))
print("Rows with source variants > 1:",
      int(source_audit["n_source_variants"].gt(1).sum()))

print("\n=== LABEL DISTRIBUTION ===")
print(dataset["y_primary"].value_counts().sort_index().to_string())
print("Positive rate:", round(dataset["y_primary"].mean(), 5))

print("\n=== SERIOUS VOTE DISTRIBUTION ===")
print(dataset["serious_votes"].value_counts().sort_index().to_string())

print("\n=== LABEL DISTRIBUTION BY SYSTEM ===")
print(pd.crosstab(dataset["system"], dataset["y_primary"]).to_string())

print("\n=== FIRST 5 ROWS ===")
print(dataset.head().to_string(index=False))
