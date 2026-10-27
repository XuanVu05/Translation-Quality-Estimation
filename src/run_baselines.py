
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import average_precision_score, matthews_corrcoef
from sklearn.preprocessing import StandardScaler

ROOT = Path(r"D:\Translation Quality Estimation")
DATA_DIR = ROOT / "results" / "week10" / "model_data"
OUT_DIR = ROOT / "results" / "week10" / "baseline_results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

train = pd.read_csv(DATA_DIR / "train_segments.csv").fillna("")
dev = pd.read_csv(DATA_DIR / "dev_segments.csv").fillna("")

# The test set is intentionally not loaded during model development.
SEED = 42
TOP_FRACTION = 0.20


def text_features(df):
    """Simple reference-free source/target surface features."""
    rows = []
    for source, target in zip(df["source"].astype(str), df["target"].astype(str)):
        s_tokens = source.split()
        t_tokens = target.split()
        s_len, t_len = len(s_tokens), len(t_tokens)

        digit_s = sum(c.isdigit() for c in source)
        digit_t = sum(c.isdigit() for c in target)

        rows.append([
            np.log1p(s_len),
            np.log1p(t_len),
            t_len / max(s_len, 1),
            abs(t_len - s_len) / max(s_len, 1),
            len(target) / max(len(source), 1),
            digit_s,
            digit_t,
            abs(digit_s - digit_t),
            sum(c.isupper() for c in target) / max(len(target), 1),
            sum(not c.isalnum() and not c.isspace() for c in target)
                / max(len(target), 1),
            len(t_tokens) - len(set(t.lower() for t in t_tokens)),
            int(not target.strip()),
        ])

    return np.asarray(rows, dtype=float)


def build_features(train_df, other_df):
    # Fit text vectorizers on training text only.
    src_vec = TfidfVectorizer(
        max_features=30000, ngram_range=(1, 2), min_df=2,
        sublinear_tf=True
    )
    tgt_vec = TfidfVectorizer(
        max_features=30000, ngram_range=(1, 2), min_df=2,
        sublinear_tf=True
    )

    Xtr_text = hstack([
        src_vec.fit_transform(train_df["source"].astype(str)),
        tgt_vec.fit_transform(train_df["target"].astype(str)),
    ]).tocsr()

    Xother_text = hstack([
        src_vec.transform(other_df["source"].astype(str)),
        tgt_vec.transform(other_df["target"].astype(str)),
    ]).tocsr()

    raw_train = text_features(train_df)
    raw_other = text_features(other_df)

    scaler = StandardScaler()
    raw_train = scaler.fit_transform(raw_train)
    raw_other = scaler.transform(raw_other)

    Xtr = hstack([Xtr_text, csr_matrix(raw_train)]).tocsr()
    Xother = hstack([Xother_text, csr_matrix(raw_other)]).tocsr()
    return Xtr, Xother


def metrics(y, scores, fraction=TOP_FRACTION):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)

    n_top = max(1, int(np.ceil(len(y) * fraction)))
    order = np.argsort(-scores, kind="stable")
    selected = order[:n_top]

    pred = np.zeros(len(y), dtype=int)
    pred[selected] = 1

    prevalence = y.mean()
    precision = y[selected].mean()
    recall = y[selected].sum() / max(y.sum(), 1)

    return {
        "PR_AUC": float(average_precision_score(y, scores)),
        "Recall_at_20pct": float(recall),
        "Precision_at_20pct": float(precision),
        "Lift_at_20pct": float(precision / prevalence) if prevalence else 0.0,
        "MCC_at_20pct": float(matthews_corrcoef(y, pred)),
        "n_top": int(n_top),
        "prevalence": float(prevalence),
    }


def heuristic_scores(df):
    """A transparent anomaly score, not an MQM-label-derived rule."""
    scores = []
    for source, target in zip(df["source"].astype(str), df["target"].astype(str)):
        s = source.split()
        t = target.split()
        ratio = len(t) / max(len(s), 1)
        digit_gap = abs(
            sum(c.isdigit() for c in source)
            - sum(c.isdigit() for c in target)
        )
        repeated = len(t) - len(set(x.lower() for x in t))

        score = 0.0
        if not target.strip():
            score += 5.0
        if ratio < 0.35 or ratio > 2.5:
            score += 1.0
        if digit_gap > 0:
            score += min(digit_gap, 3) * 0.25
        if repeated > 0:
            score += min(repeated, 5) * 0.2

        scores.append(score)

    return np.asarray(scores)


def random_scores(n, seed):
    rng = np.random.default_rng(seed)
    return rng.random(n)


y_train = train["y_primary"].astype(int).to_numpy()
y_dev = dev["y_primary"].astype(int).to_numpy()

X_train, X_dev = build_features(train, dev)

models = {
    "LogisticRegression": LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        C=1.0,
        random_state=SEED,
    ),
    "LinearSVM": LinearSVC(
    class_weight="balanced",
    C=1.0,
    max_iter=10000,
    random_state=SEED,
),
}

results = []

# Random baseline: average results across 100 random rankings.
random_runs = []
for seed in range(100):
    score = random_scores(len(dev), SEED + seed)
    random_runs.append(metrics(y_dev, score))

for key in random_runs[0]:
    if key == "n_top":
        continue
    results.append({
        "model": "Random",
        "metric": key,
        "mean": float(np.mean([r[key] for r in random_runs])),
        "std": float(np.std([r[key] for r in random_runs], ddof=1)),
    })

# Heuristic ranking baseline.
heuristic = metrics(y_dev, heuristic_scores(dev))
for key, value in heuristic.items():
    results.append({
        "model": "HeuristicRules",
        "metric": key,
        "mean": value,
        "std": 0.0,
    })

# Train classical ML baselines on train; evaluate on dev.
model_scores = {}
for name, model in models.items():
    model.fit(X_train, y_train)

    if hasattr(model, "predict_proba"):
        score = model.predict_proba(X_dev)[:, 1]
    else:
        score = model.decision_function(X_dev)

    model_scores[name] = score
    measured = metrics(y_dev, score)

    for key, value in measured.items():
        results.append({
            "model": name,
            "metric": key,
            "mean": value,
            "std": 0.0,
        })

results_df = pd.DataFrame(results)
results_df.to_csv(OUT_DIR / "dev_baseline_metrics.csv", index=False)

summary = {}
for name in ["Random", "HeuristicRules", *models.keys()]:
    subset = results_df[results_df["model"] == name]
    summary[name] = {
        row["metric"]: {
            "mean": float(row["mean"]),
            "std": float(row["std"]),
        }
        for _, row in subset.iterrows()
    }

with open(OUT_DIR / "dev_baseline_metrics.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("=== DEV BASELINE RESULTS ===")
print(
    results_df.pivot(index="metric", columns="model", values="mean")
    .round(4).to_string()
)
print("\nSaved:", OUT_DIR / "dev_baseline_metrics.csv")
print("Saved:", OUT_DIR / "dev_baseline_metrics.json")
print("\nNote: these are development results, not final test results.")


# ============================================================
# Additional dev analysis: model ranking vs. 0-3 serious votes
# This block uses DEV only and does not change model training.
# ============================================================
from scipy.stats import spearmanr

VOTE_DIR = ROOT / "results" / "week10" / "priority2_3"
VOTE_DIR.mkdir(parents=True, exist_ok=True)

required_vote_cols = {"serious_votes", "y_primary"}
missing_vote_cols = required_vote_cols - set(dev.columns)

if missing_vote_cols:
    raise ValueError(
        f"DEV data missing required columns: {sorted(missing_vote_cols)}"
    )

# Save each development sample's scores.
id_cols = [
    c for c in [
        "system", "doc", "doc_id", "seg_id",
        "source", "target", "serious_votes", "y_primary"
    ]
    if c in dev.columns
]

dev_predictions = dev[id_cols].copy()

for model_name, score in model_scores.items():
    dev_predictions[f"score_{model_name}"] = score

# Stable top-20% selection, matching the existing evaluation protocol.
n_top = max(1, int(np.ceil(len(dev) * TOP_FRACTION)))

for model_name in model_scores:
    score_col = f"score_{model_name}"
    order = np.argsort(-dev_predictions[score_col].to_numpy(), kind="stable")
    selected = np.zeros(len(dev_predictions), dtype=int)
    selected[order[:n_top]] = 1
    dev_predictions[f"top20_{model_name}"] = selected

pred_path = VOTE_DIR / "dev_model_predictions_with_votes.csv"
dev_predictions.to_csv(pred_path, index=False, encoding="utf-8-sig")

# Summarize score and top-20% selection by vote count.
group_rows = []
correlation_rows = []

for model_name in model_scores:
    score_col = f"score_{model_name}"
    top_col = f"top20_{model_name}"

    rho, p_value = spearmanr(
        dev_predictions["serious_votes"],
        dev_predictions[score_col]
    )

    correlation_rows.append({
        "model": model_name,
        "n_dev": len(dev_predictions),
        "spearman_rho_score_vs_votes": float(rho),
        "spearman_p_value_descriptive_only": float(p_value),
        "note": (
            "Descriptive only; rows may be dependent within documents "
            "and MT systems."
        ),
    })

    for votes, group in dev_predictions.groupby("serious_votes", dropna=False):
        group_rows.append({
            "model": model_name,
            "serious_votes": int(votes),
            "n_samples": len(group),
            "positive_rate_primary_label": float(group["y_primary"].mean()),
            "mean_score": float(group[score_col].mean()),
            "median_score": float(group[score_col].median()),
            "n_selected_top20": int(group[top_col].sum()),
            "fraction_of_vote_group_selected": float(group[top_col].mean()),
            "share_of_top20_from_vote_group": float(
                group[top_col].sum() / n_top
            ),
        })

group_df = pd.DataFrame(group_rows)
corr_df = pd.DataFrame(correlation_rows)

group_path = VOTE_DIR / "dev_model_ranking_by_serious_votes.csv"
corr_path = VOTE_DIR / "dev_model_vote_correlations.csv"

group_df.to_csv(group_path, index=False, encoding="utf-8-sig")
corr_df.to_csv(corr_path, index=False, encoding="utf-8-sig")

print("\n=== DEV MODEL SCORE CORRELATION WITH SERIOUS VOTES ===")
print(corr_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n=== DEV RANKING BY SERIOUS VOTE COUNT ===")
print(group_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\nSaved:", pred_path)
print("Saved:", group_path)
print("Saved:", corr_path)

