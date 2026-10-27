"""
Week 10 follow-up checks: Priority 2 (system-identity baseline + vote-count ranking)
and Priority 3 (XLM-R diagnostics + CPU/RAM inference measurement).

Run from the project root:
    python week10_priority2_3.py

Expected project files:
    mqm_newstest2020_ende.tsv
    results/week10/model_data/segments_with_fixed_splits.csv

Optional:
    Set XLMR_MODEL_DIR below to the folder containing a saved Hugging Face
    XLM-R sequence-classification checkpoint. If unset/not found, the script
    still completes Priority 2 and clearly reports that XLM-R could not be checked.
"""
from pathlib import Path
import json
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, precision_score, recall_score, matthews_corrcoef

ROOT = Path(__file__).resolve().parent
MQM_PATH = ROOT / "mqm_newstest2020_ende.tsv"
SPLIT_PATH = ROOT / "results" / "week10" / "model_data" / "segments_with_fixed_splits.csv"
OUT = ROOT / "results" / "week10" / "priority2_3"
OUT.mkdir(parents=True, exist_ok=True)

# If your saved XLM-R checkpoint is in a known location, set it here, e.g.
# XLMR_MODEL_DIR = ROOT / "models" / "xlmr_ced"
XLMR_MODEL_DIR = None

KEYS = ["system", "doc", "doc_id", "seg_id"]
HUMAN_SYSTEMS = {"Human-A.0", "Human-B.0", "Human-P.0"}
TOP_FRACTION = 0.20
# Predefined empirical-Bayes smoothing strength for system rates.
# This shrinks system rates toward the training prevalence when counts are small.
SYSTEM_RATE_PRIOR_STRENGTH = 20.0


def find_col(df, candidates, required=True):
    low = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in low:
            return low[candidate.lower()]
    if required:
        raise ValueError(
            f"Could not find any of columns {candidates}. Available columns: {list(df.columns)}"
        )
    return None


def normalize_key_columns(df):
    df = df.copy()
    for c in ["system", "doc"]:
        if c in df:
            df[c] = df[c].astype(str).str.strip()
    if "doc_id" in df:
        df["doc_id"] = pd.to_numeric(df["doc_id"], errors="coerce").astype("Int64")
    if "seg_id" in df:
        df["seg_id"] = pd.to_numeric(df["seg_id"], errors="coerce").astype("Int64")
    return df


def make_mqm_votes(path):
    # Use the same default TSV parser as the current Week 10 pipeline.
    raw = pd.read_csv(path, sep="\t", encoding="utf-8")
    required = set(KEYS + ["rater", "category", "severity"])
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"MQM TSV is missing required columns: {sorted(missing)}")

    raw = raw[~raw["system"].isin(HUMAN_SYSTEMS)].copy()
    raw["is_serious_annotation"] = (
        raw["severity"].astype(str).str.strip().str.casefold().eq("major")
        & (
            raw["category"].astype(str).str.strip().str.startswith("Accuracy/", na=False)
            | raw["category"].astype(str).str.strip().eq("Non-translation!")
        )
    ).astype(int)

    # One vote per distinct rater and segment, even if that rater has multiple MQM rows.
    rater_vote = (
        raw.groupby(KEYS + ["rater"], dropna=False)["is_serious_annotation"]
        .max().reset_index(name="rater_serious_vote")
    )
    votes = (
        rater_vote.groupby(KEYS, dropna=False)
        .agg(
            serious_votes=("rater_serious_vote", "sum"),
            distinct_raters=("rater", "nunique")
        ).reset_index()
    )
    votes["y_primary_rebuilt"] = (votes["serious_votes"] >= 2).astype(int)
    return votes


def load_split_data():
    if not MQM_PATH.exists():
        raise FileNotFoundError(f"Missing MQM file: {MQM_PATH}")
    if not SPLIT_PATH.exists():
        raise FileNotFoundError(
            f"Missing split file: {SPLIT_PATH}\n"
            "Check the actual filename in results/week10/model_data."
        )

    split = pd.read_csv(SPLIT_PATH, encoding="utf-8")
    missing = set(KEYS) - set(split.columns)
    if missing:
        raise ValueError(f"Split file is missing key columns {sorted(missing)}; columns={list(split.columns)}")
    split = normalize_key_columns(split)

    split_col = find_col(split, ["split", "set", "partition", "dataset_split"])
    split[split_col] = split[split_col].astype(str).str.strip().str.lower()
    split[split_col] = split[split_col].replace({
        "validation": "dev", "valid": "dev", "val": "dev",
        "training": "train", "testing": "test"
    })
    if not {"train", "dev", "test"}.issubset(set(split[split_col].unique())):
        raise ValueError(
            f"Expected train/dev/test in column '{split_col}', found {sorted(split[split_col].unique())}"
        )
    split = split.rename(columns={split_col: "split"})

    if split.duplicated(KEYS).any():
        dup = int(split.duplicated(KEYS).sum())
        raise ValueError(f"Split file has {dup} duplicate segment keys. Stop and inspect before evaluation.")

    votes = normalize_key_columns(make_mqm_votes(MQM_PATH))
    # The split file may already contain stale/previous serious_votes or label columns.
    # Drop these before merging so the freshly rebuilt MQM vote counts keep canonical names.
    stale_cols = [
        c for c in ["serious_votes", "distinct_raters", "y_primary_rebuilt"]
        if c in split.columns
    ]
    if stale_cols:
        print(f"Removing pre-existing columns before rebuilding from MQM: {stale_cols}")
        split = split.drop(columns=stale_cols)

    data = split.merge(votes, on=KEYS, how="left", validate="one_to_one", indicator=True)
    unmatched = int((data["_merge"] != "both").sum())
    if unmatched:
        examples = data.loc[data["_merge"] != "both", KEYS].head(10).to_dict("records")
        raise ValueError(f"{unmatched} split rows did not match MQM votes. Examples: {examples}")
    data = data.drop(columns="_merge")

    ycol = find_col(data, ["y_primary", "label", "y", "critical_label"], required=False)
    if ycol:
        existing = pd.to_numeric(data[ycol], errors="coerce")
        disagreement = int((existing.notna() & (existing.astype("Int64") != data["y_primary_rebuilt"])).sum())
        data["y_primary"] = data["y_primary_rebuilt"]
        print(f"Existing label column '{ycol}' found; disagreements with rebuilt label: {disagreement}")
    else:
        data["y_primary"] = data["y_primary_rebuilt"]

    # Verify every sample has a meaningful 0-3 vote count. If raters vary, disclose coverage.
    if not data["serious_votes"].between(0, 3).all():
        raise ValueError("serious_votes contains values outside 0..3.")
    data.to_csv(OUT / "segments_with_rebuilt_votes.csv", index=False, encoding="utf-8-sig")
    return data


def ranking_metrics(y, scores, budget=TOP_FRACTION):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)
    n = len(y)
    k = max(1, int(np.ceil(n * budget)))
    order = np.argsort(-scores, kind="mergesort")
    selected = order[:k]
    positives = int(y.sum())
    tp = int(y[selected].sum())
    precision = tp / k
    recall = tp / positives if positives else np.nan
    prevalence = positives / n if n else np.nan
    return {
        "n": n, "positives": positives, "prevalence": prevalence, "top_k": k,
        "TP_at_top20": tp, "Precision_at_top20": precision,
        "Recall_at_top20": recall,
        "Lift_at_top20": precision / prevalence if prevalence else np.nan,
        "PR_AUC": average_precision_score(y, scores) if len(np.unique(y)) > 1 else np.nan,
    }


def run_system_identity_baseline(data):
    train = data[data["split"] == "train"].copy()
    results = []
    system_stats = train.groupby("system")["y_primary"].agg(["sum", "count"]).rename(
        columns={"sum": "train_positives", "count": "train_n"}
    )
    train_prevalence = float(train["y_primary"].mean())
    alpha = SYSTEM_RATE_PRIOR_STRENGTH
    system_stats["train_prevalence"] = train_prevalence
    system_stats["smoothed_critical_rate"] = (
        system_stats["train_positives"] + alpha * train_prevalence
    ) / (system_stats["train_n"] + alpha)
    system_stats = system_stats.reset_index().sort_values("smoothed_critical_rate", ascending=False)
    system_stats.to_csv(OUT / "system_identity_train_rates.csv", index=False, encoding="utf-8-sig")

    # The system score is estimated only from training labels. No dev/test labels enter the score.
    rate_map = dict(zip(system_stats["system"], system_stats["smoothed_critical_rate"]))
    data = data.copy()
    data["system_identity_score"] = data["system"].map(rate_map)
    if data["system_identity_score"].isna().any():
        unseen = sorted(data.loc[data["system_identity_score"].isna(), "system"].unique())
        raise ValueError(f"Systems in dev/test absent from train: {unseen}")

    for part in ["dev", "test"]:
        part_df = data[data["split"] == part].copy()
        row = {"split": part, "method": "System identity only (smoothed train rate)"}
        row.update(ranking_metrics(part_df["y_primary"], part_df["system_identity_score"]))
        results.append(row)

    metrics = pd.DataFrame(results)
    metrics.to_csv(OUT / "system_identity_baseline_metrics.csv", index=False, encoding="utf-8-sig")
    data.to_csv(OUT / "segments_with_system_identity_scores.csv", index=False, encoding="utf-8-sig")

    # Ordinal analysis: Does the system-only score increase with 0/1/2/3 serious votes?
    ordinal_rows = []
    for part in ["dev", "test"]:
        d = data[data["split"] == part]
        rho, pval = spearmanr(d["system_identity_score"], d["serious_votes"])
        ordinal_rows.append({
            "split": part,
            "n": len(d),
            "spearman_rho_system_score_vs_votes": rho,
            "spearman_p_value_descriptive_only": pval,
            "note": "Descriptive; repeated segments/systems mean rows are not independent."
        })
        group = d.groupby("serious_votes").agg(
            n=("serious_votes", "size"),
            mean_system_score=("system_identity_score", "mean"),
            median_system_score=("system_identity_score", "median"),
            mean_primary_label=("y_primary", "mean")
        ).reset_index()
        group.insert(0, "split", part)
        ordinal_rows.extend(group.to_dict("records"))
    pd.DataFrame(ordinal_rows).to_csv(OUT / "system_identity_ordinal_vote_analysis.csv", index=False, encoding="utf-8-sig")

    # Counts of exact vote levels, split-specific.
    vote_counts = (
        data.groupby(["split", "serious_votes"]).size()
        .rename("n_segments").reset_index()
    )
    vote_counts.to_csv(OUT / "serious_vote_counts_by_split.csv", index=False, encoding="utf-8-sig")

    print("\n=== SYSTEM-IDENTITY BASELINE: score estimated from TRAIN only ===")
    print(system_stats.to_string(index=False))
    print("\n=== Ranking metrics at top 20% ===")
    print(metrics.to_string(index=False))
    print("\n=== Serious-vote counts by split ===")
    print(vote_counts.to_string(index=False))
    print("\nOutputs:", OUT)
    return data


def run_xlmr_diagnostic(data):
    model_dir = Path(XLMR_MODEL_DIR) if XLMR_MODEL_DIR else None
    if model_dir is None:
        # Conservative search for saved HF checkpoints, avoiding a full recursive scan of huge caches.
        candidates = [
            ROOT / "models" / "xlmr_ced",
            ROOT / "models" / "xlm-roberta",
            ROOT / "results" / "week9" / "xlmr_model",
            ROOT / "results" / "week10" / "xlmr_model",
            ROOT / "xlmr_model",
        ]
        model_dir = next((p for p in candidates if p.exists() and (p / "config.json").exists()), None)

    if model_dir is None or not model_dir.exists():
        message = (
            "SKIPPED: No saved XLM-R Hugging Face checkpoint found in the standard locations. "
            "Set XLMR_MODEL_DIR near the top of week10_priority2_3.py to the actual checkpoint path. "
            "Do not claim a fresh XLM-R diagnostic was run."
        )
        (OUT / "xlmr_diagnostic_status.txt").write_text(message, encoding="utf-8")
        print("\nXLM-R diagnostic:", message)
        return

    try:
        import torch
        import psutil
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
    except Exception as e:
        message = f"SKIPPED: XLM-R checkpoint found at {model_dir}, but a required package could not import: {e}"
        (OUT / "xlmr_diagnostic_status.txt").write_text(message, encoding="utf-8")
        print("\nXLM-R diagnostic:", message)
        return

    source_col = find_col(data, ["source", "src", "source_text", "src_text"])
    target_col = find_col(data, ["target", "translation", "mt", "target_text", "mt_text"])
    dev = data[data["split"] == "dev"].copy()
    if len(dev) == 0:
        raise ValueError("No dev rows available for XLM-R diagnostic.")

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.to("cpu")
    model.eval()
    max_length = min(256, int(getattr(tokenizer, "model_max_length", 256)))
    # Avoid pathological tokenizer sentinel values.
    if max_length > 4096:
        max_length = 256

    sources = dev[source_col].fillna("").astype(str).tolist()
    targets = dev[target_col].fillna("").astype(str).tolist()
    proc = psutil.Process()
    rss_before = proc.memory_info().rss / (1024 ** 2)

    # Tokenization diagnostic: pair length and truncation under the actual max_length.
    pair_lengths = []
    truncation_flags = []
    for s, t in zip(sources, targets):
        full = tokenizer(s, t, truncation=False, add_special_tokens=True)
        truncated = tokenizer(s, t, truncation=True, max_length=max_length, add_special_tokens=True)
        pair_lengths.append(len(full["input_ids"]))
        truncation_flags.append(len(full["input_ids"]) > max_length)

    # Run deterministic CPU inference in small batches and measure elapsed time/RSS.
    batch_size = 16
    scores = []
    start = time.perf_counter()
    with torch.no_grad():
        for i in range(0, len(dev), batch_size):
            batch = tokenizer(
                sources[i:i+batch_size], targets[i:i+batch_size],
                truncation=True, max_length=max_length, padding=True,
                return_tensors="pt"
            )
            outputs = model(**batch)
            logits = outputs.logits
            if logits.shape[-1] == 1:
                batch_scores = torch.sigmoid(logits.squeeze(-1)).cpu().numpy()
            else:
                # For binary sequence classification, use probability of class 1.
                batch_scores = torch.softmax(logits, dim=-1)[:, 1].cpu().numpy()
            scores.extend(np.asarray(batch_scores).reshape(-1).tolist())
    elapsed = time.perf_counter() - start
    rss_after = proc.memory_info().rss / (1024 ** 2)

    dev["xlmr_diagnostic_score"] = scores
    dev.to_csv(OUT / "dev_xlmr_diagnostic_predictions.csv", index=False, encoding="utf-8-sig")
    score_arr = np.asarray(scores, dtype=float)
    unique_raw = int(pd.Series(score_arr).nunique())
    diagnostic = {
        "model_dir": str(model_dir),
        "device": "CPU",
        "n_dev": int(len(dev)),
        "max_length": int(max_length),
        "pair_length_min": int(np.min(pair_lengths)),
        "pair_length_median": float(np.median(pair_lengths)),
        "pair_length_p95": float(np.percentile(pair_lengths, 95)),
        "pair_length_max": int(np.max(pair_lengths)),
        "n_pairs_over_max_length": int(np.sum(truncation_flags)),
        "truncation_rate": float(np.mean(truncation_flags)),
        "score_min": float(np.min(score_arr)),
        "score_max": float(np.max(score_arr)),
        "score_std": float(np.std(score_arr)),
        "unique_scores_raw": unique_raw,
        "unique_scores_3dp": int(pd.Series(np.round(score_arr, 3)).nunique()),
        "unique_scores_6dp": int(pd.Series(np.round(score_arr, 6)).nunique()),
        "fraction_of_pairs_tied_at_3dp": float(1 - pd.Series(np.round(score_arr, 3)).nunique() / len(score_arr)),
        "cpu_inference_seconds": float(elapsed),
        "cpu_ms_per_pair": float(1000 * elapsed / len(dev)),
        "rss_before_inference_mb": float(rss_before),
        "rss_after_inference_mb": float(rss_after),
        "rss_delta_mb": float(rss_after - rss_before),
    }
    if dev["y_primary"].nunique() > 1:
        diagnostic["dev_pr_auc"] = float(average_precision_score(dev["y_primary"], score_arr))
    (OUT / "xlmr_diagnostic_summary.json").write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    pd.DataFrame([diagnostic]).to_csv(OUT / "xlmr_diagnostic_summary.csv", index=False, encoding="utf-8-sig")

    print("\n=== XLM-R DEV DIAGNOSTIC (CPU inference only; not retraining) ===")
    print(json.dumps(diagnostic, indent=2))
    print("Saved summary:", OUT / "xlmr_diagnostic_summary.json")


def main():
    print("Project root:", ROOT)
    print("MQM file:", MQM_PATH)
    print("Split file:", SPLIT_PATH)
    data = load_split_data()
    print("\n=== Split and label checks ===")
    print(data.groupby("split").agg(
        n=("y_primary", "size"),
        positives=("y_primary", "sum"),
        prevalence=("y_primary", "mean"),
        n_documents=("doc", "nunique")
    ).to_string())
    print("\nRebuilt serious_votes distribution:")
    print(data.groupby(["split", "serious_votes"]).size().unstack(fill_value=0).to_string())
    data = run_system_identity_baseline(data)
    run_xlmr_diagnostic(data)
    print("\nFinished. Review files in:", OUT)


if __name__ == "__main__":
    main()
