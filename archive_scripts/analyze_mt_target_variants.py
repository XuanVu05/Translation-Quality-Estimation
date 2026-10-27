from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "mqm_newstest2020_ende.tsv"
OUT = ROOT / "results" / "week10" / "data_quality"
OUT.mkdir(parents=True, exist_ok=True)

if not DATA.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA}")

df = pd.read_csv(DATA, sep="\t", encoding="utf-8")

human_systems = {"Human-A.0", "Human-B.0", "Human-P.0"}
mt = df[~df["system"].isin(human_systems)].copy()

mt["target_clean"] = (
    mt["target"]
    .fillna("")
    .astype(str)
    .map(lambda x: re.sub(r"</?v>", "", x))
)

keys = ["system", "doc", "doc_id", "seg_id"]

stats = (
    mt.groupby(keys, dropna=False)
    .agg(
        annotation_rows=("target_clean", "size"),
        raters=("rater", "nunique"),
        target_variants=("target_clean", "nunique")
    )
    .reset_index()
)

problems = stats[stats["target_variants"] > 1].copy()

variant_counts = (
    mt.groupby(keys + ["target_clean"], dropna=False)
    .size()
    .reset_index(name="variant_count")
)

variant_counts = variant_counts.merge(
    stats[keys + ["target_variants", "raters"]],
    on=keys,
    how="left"
)

stats.to_csv(
    OUT / "mt_target_variant_statistics.csv",
    index=False,
    encoding="utf-8-sig"
)

problems.to_csv(
    OUT / "mt_target_variant_problems.csv",
    index=False,
    encoding="utf-8-sig"
)

variant_counts.to_csv(
    OUT / "mt_target_variant_counts.csv",
    index=False,
    encoding="utf-8-sig"
)

print("MT segments:", len(stats))
print("Segments with multiple targets:", len(problems))
print("Output directory:", OUT)
