
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, matthews_corrcoef
from sklearn.preprocessing import StandardScaler, OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "results" / "week10" / "model_data"
OUT_DIR = ROOT / "results" / "week10" / "ablation_dev"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
TOP_FRACTION = 0.20

train = pd.read_csv(DATA_DIR / "train_segments.csv").fillna("")
dev = pd.read_csv(DATA_DIR / "dev_segments.csv").fillna("")

y_train = train["y_primary"].astype(int).to_numpy()
y_dev = dev["y_primary"].astype(int).to_numpy()


def surface_features(df):
    rows = []

    for source, target in zip(
        df["source"].astype(str),
        df["target"].astype(str),
    ):
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
            sum(c.isupper() for c in target)
                / max(len(target), 1),
            sum(
                not c.isalnum() and not c.isspace()
                for c in target
            ) / max(len(target), 1),
            len(t_tokens) - len(set(t.lower() for t in t_tokens)),
            int(not target.strip()),
        ])

    return np.asarray(rows, dtype=float)


# ------------------------------------------------------------
# 1. Base features: TF-IDF(source, target) + surface features
#    All vectorizers/scalers are fitted on TRAIN only.
# ------------------------------------------------------------
src_vec = TfidfVectorizer(
    max_features=30000,
    ngram_range=(1, 2),
    min_df=2,
    sublinear_tf=True,
)
tgt_vec = TfidfVectorizer(
    max_features=30000,
    ngram_range=(1, 2),
    min_df=2,
    sublinear_tf=True,
)

X_train_text = hstack([
    src_vec.fit_transform(train["source"].astype(str)),
    tgt_vec.fit_transform(train["target"].astype(str)),
]).tocsr()

X_dev_text = hstack([
    src_vec.transform(dev["source"].astype(str)),
    tgt_vec.transform(dev["target"].astype(str)),
]).tocsr()

scaler = StandardScaler()
raw_train = scaler.fit_transform(surface_features(train))
raw_dev = scaler.transform(surface_features(dev))

X_train_base = hstack([
    X_train_text,
    csr_matrix(raw_train),
]).tocsr()

X_dev_base = hstack([
    X_dev_text,
    csr_matrix(raw_dev),
]).tocsr()


# ------------------------------------------------------------
# 2. One-hot system identity, fitted on TRAIN only.
# ------------------------------------------------------------
try:
    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=True,
    )
except TypeError:
    # Compatibility with older scikit-learn versions.
    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse=True,
    )

X_train_system = encoder.fit_transform(
    train[["system"]].astype(str)
)
X_dev_system = encoder.transform(
    dev[["system"]].astype(str)
)

X_train_plus_system = hstack([
    X_train_base,
    X_train_system,
]).tocsr()

X_dev_plus_system = hstack([
    X_dev_base,
    X_dev_system,
]).tocsr()


# ------------------------------------------------------------
# 3. Common evaluation metrics.
#    Higher score = higher review priority.
# ------------------------------------------------------------
def calculate_metrics(y, scores):
    y = np.asarray(y, dtype=int)
    scores = np.asarray(scores, dtype=float)

    n_top = max(1, int(np.ceil(len(y) * TOP_FRACTION)))
    selected = np.argsort(-scores, kind="stable")[:n_top]

    pred = np.zeros(len(y), dtype=int)
    pred[selected] = 1

    prevalence = float(y.mean())
    precision = float(y[selected].mean())
    recall = float(y[selected].sum() / max(int(y.sum()), 1))

    return {
        "PR_AUC": float(average_precision_score(y, scores)),
        "Recall_at_20pct": recall,
        "Precision_at_20pct": precision,
        "Lift_at_20pct": (
            precision / prevalence if prevalence > 0 else 0.0
        ),
        "MCC_at_20pct": float(matthews_corrcoef(y, pred)),
        "n_top": int(n_top),
        "prevalence": prevalence,
        "positive_samples_in_top20pct": int(y[selected].sum()),
    }


# ------------------------------------------------------------
# 4. Three ablation configurations.
# ------------------------------------------------------------
configs = [
    (
        "LR_Base",
        X_train_base,
        X_dev_base,
        "TF-IDF source/target + 12 surface features",
    ),
    (
        "LR_Plus_System",
        X_train_plus_system,
        X_dev_plus_system,
        "Base features + one-hot system identity",
    ),
    (
        "System_Only",
        X_train_system,
        X_dev_system,
        "One-hot system identity only",
    ),
]

metric_rows = []
prediction_df = dev[
    ["system", "doc", "doc_id", "seg_id", "y_primary"]
].copy()

for name, Xtr, Xdv, description in configs:
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        C=1.0,
        random_state=SEED,
    )

    model.fit(Xtr, y_train)
    scores = model.predict_proba(Xdv)[:, 1]

    values = calculate_metrics(y_dev, scores)

    prediction_df[f"score_{name}"] = scores

    for metric, value in values.items():
        metric_rows.append({
            "model": name,
            "description": description,
            "metric": metric,
            "value": value,
            "train_rows": len(train),
            "dev_rows": len(dev),
            "train_features": Xtr.shape[1],
            "dev_features": Xdv.shape[1],
        })

metrics_df = pd.DataFrame(metric_rows)

# Write only into the new ablation_dev directory.
metrics_path = OUT_DIR / "dev_ablation_metrics.csv"
predictions_path = OUT_DIR / "dev_ablation_predictions.csv"
manifest_path = OUT_DIR / "dev_ablation_manifest.json"

metrics_df.to_csv(metrics_path, index=False)
prediction_df.to_csv(predictions_path, index=False)

manifest = {
    "experiment": "Week 10 Dev ablation",
    "seed": SEED,
    "top_fraction": TOP_FRACTION,
    "train_rows": len(train),
    "dev_rows": len(dev),
    "train_documents": int(train["doc"].nunique()),
    "dev_documents": int(dev["doc"].nunique()),
    "train_positive": int(y_train.sum()),
    "dev_positive": int(y_dev.sum()),
    "train_systems": sorted(train["system"].astype(str).unique().tolist()),
    "dev_systems": sorted(dev["system"].astype(str).unique().tolist()),
    "configurations": [
        {
            "name": name,
            "description": description,
            "train_feature_count": int(Xtr.shape[1]),
            "dev_feature_count": int(Xdv.shape[1]),
        }
        for name, Xtr, Xdv, description in configs
    ],
    "test_set_loaded": False,
    "output_files": [
        str(metrics_path.relative_to(ROOT)),
        str(predictions_path.relative_to(ROOT)),
        str(manifest_path.relative_to(ROOT)),
    ],
}

with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print("=== WEEK 10 DEV ABLATION ===")
print("Train:", len(train), "rows;", train["doc"].nunique(), "documents")
print("Dev:", len(dev), "rows;", dev["doc"].nunique(), "documents")
print("Train positives:", int(y_train.sum()))
print("Dev positives:", int(y_dev.sum()))
print("Top-20% Dev budget:", int(np.ceil(len(dev) * TOP_FRACTION)))

print("\n=== METRICS ===")
print(
    metrics_df.pivot(
        index="metric",
        columns="model",
        values="value",
    ).round(6).to_string()
)

print("\nSaved:")
print(metrics_path)
print(predictions_path)
print(manifest_path)
print("\nTest set was not loaded or evaluated.")
