import csv
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT_DIR = ROOT / "original_outputs"

df = pd.read_csv(
    DATA,
    sep="\t",
    encoding="utf-8",
    quoting=csv.QUOTE_NONE,
    dtype=str,
    keep_default_na=False,
)

human_systems = {"Human-A.0", "Human-B.0", "Human-P.0"}
df = df[~df["system"].isin(human_systems)].copy()

# Use unique segment keys; target variants are deliberately not collapsed here.
segments = (
    df[["system", "doc", "doc_id", "seg_id", "source", "target"]]
    .drop_duplicates(["system", "doc", "doc_id", "seg_id"])
)

system_to_file = {
    "eTranslation.737": "newstest2020.en-de.eTranslation.737.txt",
    "Huoshan_Translate.832": "newstest2020.en-de.Huoshan_Translate.832.txt",
    "Online-A.1574": "newstest2020.en-de.Online-A.1574.txt",
    "Online-B.1590": "newstest2020.en-de.Online-B.1590.txt",
    "OPPO.1535": "newstest2020.en-de.OPPO.1535.txt",
    "Tencent_Translation.1520": "newstest2020.en-de.Tencent_Translation.1520.txt",
    "Tohoku-AIP-NTT.890": "newstest2020.en-de.Tohoku-AIP-NTT.890.txt",
}

for system, filename in system_to_file.items():
    path = OUT_DIR / filename
    outputs = path.read_text(encoding="utf-8-sig").splitlines()
    sub = segments[segments["system"] == system]

    print("\n" + "=" * 90)
    print("SYSTEM:", system)
    print("Output lines:", len(outputs), "| MQM segment keys:", len(sub))

    for _, row in sub.head(3).iterrows():
        doc_id = row["doc_id"]
        seg_id = row["seg_id"]
        try:
            idx = int(seg_id) - 1
            output = outputs[idx]
        except (ValueError, IndexError):
            print("Cannot index:", doc_id, seg_id)
            continue

        print(f"\nDOC={row['doc']} DOC_ID={doc_id} SEG_ID={seg_id}")
        print("MQM target:", row["target"][:180])
        print("Output line:", output[:180])
