
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, matthews_corrcoef
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

ROOT = Path(r"D:\Translation Quality Estimation")
DATA_DIR = ROOT / "results" / "week10" / "model_data"
OUT_DIR = ROOT / "results" / "week10" / "test_evaluation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20261026
N_BOOT = 1000
TOP_FRACTION = 0.20

train = pd.read_csv(DATA_DIR / "train_segments.csv").fillna("")
dev = pd.read_csv(DATA_DIR / "dev_segments.csv").fillna("")
test = pd.read_csv(DATA_DIR / "test_segments.csv").fillna("")

# The model choice is already fixed from development results.
fit_df = pd.concat([train, dev], ignore_index=True)
y_fit = fit_df["y_primary"].astype(int).to_numpy()
y_test = test["y_primary"].astype(int).to_numpy()


def surface_features(df):
    rows = []
    for source, target in zip(df["source"].astype(str), df["target"].astype(str)):
        s_tokens, t_tokens = source.split(), target.split()
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


def make_features(fit_df, test_df):
    src_vec = TfidfVectorizer(
        max_features=30000, ngram_range=(1, 2),
        min_df=2, sublinear_tf=True
    )
    tgt_vec = TfidfVectorizer(
        max_features=30000, ngram_range=(1, 2),
        min_df=2, sublinear_tf=True
    )

    X_fit_text = hstack([
        src_vec.fit_transform(fit_df["source"].astype(str)),
        tgt_vec.fit_transform(fit_df["target"].astype(str)),
    ]).tocsr()

    X_test_text = hstack([
        src_vec.transform(test_df["source"].astype(str)),
        tgt_vec.transform(test_df["target"].astype(str)),
    ]).tocsr()

    raw_fit = surface_features(fit_df)
    raw_test = surface_features(test_df)

    scaler = StandardScaler()
    raw_fit = scaler.fit_transform(raw_fit)
    raw_test = scaler.transform(raw_test)

    X_fit = hstack([X_fit_text, csr_matrix(raw_fit)]).tocsr()
    X_test = hstack([X_test_text, csr_matrix(raw_test)]).tocsr()
    return X_fit, X_test


def heuristic_scores(df):
    scores = []
    for source, target in zip(df["source"].astype(str), df["target"].astype(str)):
        s, t = source.split(), target.split()
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
        score += min(digit_gap, 3) * 0.25
        score += min(repeated, 5) * 0.2
        scores.append(score)
    return np.asarray(scores, dtype=float)


def metric_values(y, score):
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    n_top = max(1, int(np.ceil(len(y) * TOP_FRACTION)))
    selected = np.argsort(-score, kind="stable")[:n_top]

    pred = np.zeros(len(y), dtype=int)
    pred[selected] = 1

    prevalence = float(y.mean())
    precision = float(y[selected].mean())
    recall = float(y[selected].sum() / max(int(y.sum()), 1))

    return {
        "PR_AUC": float(average_precision_score(y, score)),
        "Recall_at_20pct": recall,
        "Precision_at_20pct": precision,
        "Lift_at_20pct": precision / prevalence if prevalence else 0.0,
        "MCC_at_20pct": float(matthews_corrcoef(y, pred)),
    }


# Fit vectorizers and models using train + dev only.
X_fit, X_test = make_features(fit_df, test)

lr = LogisticRegression(
    class_weight="balanced", C=1.0,
    max_iter=2000, random_state=42
)
svm = LinearSVC(
    class_weight="balanced", C=1.0,
    max_iter=10000, random_state=42
)

lr.fit(X_fit, y_fit)
svm.fit(X_fit, y_fit)

scores = {
    "Random": np.random.default_rng(SEED).random(len(test)),
    "HeuristicRules": heuristic_scores(test),
    "LogisticRegression": lr.predict_proba(X_test)[:, 1],
    "LinearSVM": svm.decision_function(X_test),
}

# Save predictions for reproducibility and manual error analysis.
predictions = test[
    ["system", "doc", "doc_id", "seg_id", "source", "target", "y_primary"]
].copy()
for name, score in scores.items():
    predictions[f"score_{name}"] = score

predictions.to_csv(OUT_DIR / "test_predictions.csv", index=False)

# Point estimates on the fixed test set.
point_rows = []
for name, score in scores.items():
    values = metric_values(y_test, score)
    for metric, value in values.items():
        point_rows.append({
            "model": name,
            "metric": metric,
            "estimate": value,
        })

point_df = pd.DataFrame(point_rows)
point_df.to_csv(OUT_DIR / "test_point_metrics.csv", index=False)

# Paired cluster bootstrap: resample documents, keeping every row
# from each sampled document together. Repeated sampled documents
# are retained as repeated clusters in each bootstrap replicate.
docs = test["doc"].astype(str).to_numpy()
unique_docs = np.unique(docs)
rows_by_doc = {
    doc: np.flatnonzero(docs == doc)
    for doc in unique_docs
}

rng = np.random.default_rng(SEED + 1)
boot_metrics = {name: {m: [] for m in metric_values(y_test, score)}
                for name, score in scores.items()}

for b in range(N_BOOT):
    sampled_docs = rng.choice(unique_docs, size=len(unique_docs), replace=True)
    idx_parts = [rows_by_doc[d] for d in sampled_docs]
    idx = np.concatenate(idx_parts)

    y_b = y_test[idx]
    for name, score in scores.items():
        vals = metric_values(y_b, score[idx])
        for metric, value in vals.items():
            boot_metrics[name][metric].append(value)

# 95% percentile confidence intervals for each method.
ci_rows = []
for name, metric_dict in boot_metrics.items():
    for metric, values in metric_dict.items():
        ci_rows.append({
            "model": name,
            "metric": metric,
            "estimate": metric_values(y_test, scores[name])[metric],
            "ci95_low": float(np.quantile(values, 0.025)),
            "ci95_high": float(np.quantile(values, 0.975)),
        })

ci_df = pd.DataFrame(ci_rows)
ci_df.to_csv(OUT_DIR / "test_metrics_with_ci.csv", index=False)

# Paired CIs for differences versus the heuristic baseline.
# Positive differences favor the named model on that metric.
diff_rows = []
for name in ["LogisticRegression", "LinearSVM", "Random"]:
    for metric in boot_metrics[name]:
        diffs = (
            np.asarray(boot_metrics[name][metric])
            - np.asarray(boot_metrics["HeuristicRules"][metric])
        )
        diff_rows.append({
            "comparison": f"{name} - HeuristicRules",
            "metric": metric,
            "difference_point": (
                metric_values(y_test, scores[name])[metric]
                - metric_values(y_test, scores["HeuristicRules"])[metric]
            ),
            "ci95_low": float(np.quantile(diffs, 0.025)),
            "ci95_high": float(np.quantile(diffs, 0.975)),
        })

diff_df = pd.DataFrame(diff_rows)
diff_df.to_csv(OUT_DIR / "paired_difference_ci.csv", index=False)

print("=== TEST POINT ESTIMATES ===")
print(point_df.pivot(index="metric", columns="model", values="estimate")
      .round(4).to_string())

print("\n=== TEST METRICS WITH 95% CLUSTER-BOOTSTRAP CI ===")
print(ci_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\n=== PAIRED DIFFERENCES VS HEURISTIC RULES ===")
print(diff_df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

print("\nTest rows:", len(test))
print("Test documents:", test["doc"].nunique())
print("Test positive samples:", int(y_test.sum()))
print("Test prevalence:", round(float(y_test.mean()), 5))
print("Bootstrap replicates:", N_BOOT)
print("\nSaved results to:", OUT_DIR)
