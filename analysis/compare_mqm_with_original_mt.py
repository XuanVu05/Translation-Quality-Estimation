
from pathlib import Path
import re
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
MAPPING_PATH = ROOT / "data" / "details" / "en-de.txt"
ORIGINAL_DIR = ROOT / "original_outputs"
OUT = ROOT / "analysis" / "data_quality_results"
OUT.mkdir(parents=True, exist_ok=True)

SYSTEM_FILES = {
    "eTranslation.737": "newstest2020.en-de.eTranslation.737.txt",
    "Huoshan_Translate.832": "newstest2020.en-de.Huoshan_Translate.832.txt",
    "Online-A.1574": "newstest2020.en-de.Online-A.1574.txt",
    "Online-B.1590": "newstest2020.en-de.Online-B.1590.txt",
    "OPPO.1535": "newstest2020.en-de.OPPO.1535.txt",
    "Tencent_Translation.1520": "newstest2020.en-de.Tencent_Translation.1520.txt",
    "Tohoku-AIP-NTT.890": "newstest2020.en-de.Tohoku-AIP-NTT.890.txt",
}

def normalize(text):
    if pd.isna(text):
        return ""
    text = re.sub(r"</?v>", "", str(text))
    return re.sub(r"\s+", " ", text).strip()

# 1. Load MQM.
mqm = pd.read_csv(MQM_PATH, sep="\t")

mqm["doc"] = mqm["doc"].astype(str).str.strip()
mqm["seg_id"] = pd.to_numeric(
    mqm["seg_id"], errors="raise"
).astype(int)

mqm["target_normalized"] = mqm["target"].apply(normalize)

# 2. Load mapping.
mapping = pd.read_csv(
    MAPPING_PATH,
    sep="\t",
    header=None,
    names=[
        "line_id", "testset", "langpair",
        "document_id", "segment_id"
    ],
    dtype={"document_id": str}
)

mapping["document_id"] = mapping["document_id"].str.strip()
mapping["line_id"] = pd.to_numeric(
    mapping["line_id"], errors="raise"
).astype(int)
mapping["segment_id"] = pd.to_numeric(
    mapping["segment_id"], errors="raise"
).astype(int)

# 3. Validate mapping.
assert mapping["line_id"].is_unique, "Duplicate line_id"
assert not mapping.duplicated(
    ["document_id", "segment_id"]
).any(), "Duplicate document-segment key"

# 4. Join using verified keys.
merged = mqm.merge(
    mapping,
    left_on=["doc", "seg_id"],
    right_on=["document_id", "line_id"],
    how="left",
    validate="many_to_one",
    indicator=True
)

unmatched = merged[merged["_merge"] != "both"].copy()
matched = merged[merged["_merge"] == "both"].copy()

unmatched.to_csv(OUT / "mqm_mapping_unmatched.csv", index=False)

print("=" * 65)
print("MAPPING VALIDATION")
print("=" * 65)
print("MQM rows:", len(mqm))
print("Matched rows:", len(matched))
print("Unmatched rows:", len(unmatched))

if len(unmatched) > 0:
    raise ValueError(
        "Some MQM rows could not be mapped. "
        "Inspect mqm_mapping_unmatched.csv."
    )

# 5. Compare each MT system against original output.
all_details = []
system_summaries = []

for system, filename in SYSTEM_FILES.items():

    current = matched[matched["system"] == system].copy()

    if current.empty:
        raise ValueError(f"No MQM rows found for {system}")

    filepath = ORIGINAL_DIR / filename

    if not filepath.exists():
        raise FileNotFoundError(filepath)

    original_lines = filepath.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    original_lines = [normalize(x) for x in original_lines]

    if len(original_lines) != len(mapping):
        raise ValueError(
            f"{system}: {len(original_lines)} original lines "
            f"but {len(mapping)} mapping rows."
        )

    current["original_target"] = current["line_id"].map(
        lambda line_id: original_lines[int(line_id) - 1]
    )

    segment_key = ["system", "doc", "doc_id", "seg_id"]

    records = []

    for key, group in current.groupby(segment_key, sort=False):

        original_targets = group["original_target"].unique()

        if len(original_targets) != 1:
            raise ValueError(
                f"Multiple original targets for {key}"
            )

        original_target = original_targets[0]
        mqm_targets = set(group["target_normalized"])

        records.append({
            "system": system,
            "doc": key[1],
            "doc_id": key[2],
            "seg_id": key[3],
            "line_id": int(group["line_id"].iloc[0]),
            "n_mqm_targets": len(mqm_targets),
            "n_targets_matching_original": sum(
                target == original_target
                for target in mqm_targets
            ),
            "all_mqm_targets_match_original": all(
                target == original_target
                for target in mqm_targets
            ),
            "any_mqm_target_matches_original":
                original_target in mqm_targets,
            "original_target": original_target,
            "mqm_targets": " ||| ".join(sorted(mqm_targets))
        })

    result = pd.DataFrame(records)

    result["comparison_status"] = result.apply(
        lambda row:
            "All match"
            if row["all_mqm_targets_match_original"]
            else (
                "Some match"
                if row["any_mqm_target_matches_original"]
                else "None match"
            ),
        axis=1
    )

    result.to_csv(
        OUT / f"comparison_{system}.csv",
        index=False
    )

    all_details.append(result)

    system_summaries.append({
        "system": system,
        "original_lines": len(original_lines),
        "mqm_segments": len(result),
        "all_match_segments": int(
            (result["comparison_status"] == "All match").sum()
        ),
        "some_match_segments": int(
            (result["comparison_status"] == "Some match").sum()
        ),
        "none_match_segments": int(
            (result["comparison_status"] == "None match").sum()
        ),
        "all_match_rate": float(
            (result["comparison_status"] == "All match").mean()
        ),
        "any_match_rate": float(
            result["any_mqm_target_matches_original"].mean()
        )
    })

# 6. Combine results.
if not all_details:
    raise RuntimeError("No system comparison results were generated.")

combined = pd.concat(all_details, ignore_index=True)
summary = pd.DataFrame(system_summaries)

combined.to_csv(
    OUT / "mqm_vs_original_all_segments.csv",
    index=False
)
summary.to_csv(
    OUT / "mqm_vs_original_summary.csv",
    index=False
)

overall = {
    "mqm_rows": int(len(mqm)),
    "matched_mqm_rows": int(len(matched)),
    "unmatched_mqm_rows": int(len(unmatched)),
    "mt_systems_checked": len(SYSTEM_FILES),
    "total_mt_system_segments": int(len(combined)),
    "all_match_segments": int(
        (combined["comparison_status"] == "All match").sum()
    ),
    "some_match_segments": int(
        (combined["comparison_status"] == "Some match").sum()
    ),
    "none_match_segments": int(
        (combined["comparison_status"] == "None match").sum()
    )
}

with open(
    OUT / "mqm_vs_original_summary.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        {"overall": overall, "by_system": system_summaries},
        f, indent=4, ensure_ascii=False
    )

print("\n" + "=" * 65)
print("MQM TARGET VS ORIGINAL MT OUTPUT")
print("=" * 65)

print("\nOVERALL")
for key, value in overall.items():
    print(f"{key}: {value}")

print("\nBY SYSTEM")
print(
    summary.to_string(
        index=False,
        formatters={
            "all_match_rate": "{:.4%}".format,
            "any_match_rate": "{:.4%}".format
        }
    )
)

print("\nResults saved to:", OUT)
