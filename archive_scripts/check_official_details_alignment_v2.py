import pandas as pd
from pathlib import Path

root = Path(r"D:\Translation Quality Estimation")
mqm_path = root / "mqm_newstest2020_ende.tsv"
details_path = Path.home() / "Downloads" / "newstest2020txt-v2 (1)" / "txt" / "details" / "en-de.txt"
outputs_dir = root / "original_outputs"

mqm = pd.read_csv(mqm_path, sep="\t", dtype=str, keep_default_na=False)
details = pd.read_csv(
    details_path, sep=r"\s+", header=None,
    names=["line", "testset", "lang_pair", "document_id", "segment_id"],
    dtype=str
)

mqm_keys = set(zip(mqm["doc"].str.strip(), mqm["doc_id"].str.strip()))
details_keys = set(zip(details["document_id"].str.strip(), details["segment_id"].str.strip()))

print("=== OFFICIAL MAPPING CHECK ===")
print("MQM unique (doc, doc_id):", len(mqm_keys))
print("Details unique (document_id, segment_id):", len(details_keys))
print("Matched keys:", len(mqm_keys & details_keys))
print("MQM-only keys:", len(mqm_keys - details_keys))
print("Details-only keys:", len(details_keys - mqm_keys))

# Check that each MQM key maps to exactly one global output line
mapping_counts = details.groupby(
    ["document_id", "segment_id"]
)["line"].nunique()

print("\nMapping keys with more than one line:",
      int((mapping_counts > 1).sum()))

# Check output files
print("\n=== SYSTEM OUTPUT FILES ===")
for path in sorted(outputs_dir.glob("*.txt")):
    with path.open("r", encoding="utf-8") as f:
        n_lines = sum(1 for _ in f)
    print(f"{path.name}: {n_lines} lines")

# Create a mapping report using the official details file
joined = mqm[["system", "doc", "doc_id", "seg_id"]].drop_duplicates().merge(
    details,
    left_on=["doc", "doc_id"],
    right_on=["document_id", "segment_id"],
    how="left",
    validate="many_to_one"
)

print("\nMQM system/document/segment rows:", len(joined))
print("Rows with no mapped output line:", int(joined["line"].isna().sum()))

out = root / "results" / "week10" / "data_quality"
out.mkdir(parents=True, exist_ok=True)
joined.to_csv(out / "mqm_official_line_mapping_check.csv", index=False)
print("Saved report:", out / "mqm_official_line_mapping_check.csv")
