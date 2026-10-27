
from pathlib import Path
import math

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, matthews_corrcoef

ROOT = Path(r"D:\Translation Quality Estimation")
DATA_DIR = ROOT / "results" / "week10" / "model_data"
OUT_DIR = ROOT / "results" / "week10" / "sensitivity_analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
TOP_FRACTION = 0.20

train = pd.read_csv(DATA_DIR / "train_segments.csv").fillna("")
dev = pd.read_csv(DATA_DIR / "dev_segments.csv").fillna("")


def text_features(df):
    """The same 12 source/target surface features as run_baselines.py."""
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
            sum(c.isupper() for c in target) / max(len(target), 1),
            sum(
                not c.isalnum() and not c.isspace()
                for c in target
            ) / max(len(target), 1),
            len(t_tokens) - len(set(t.lower() for t in t_tokens)),
            int(not target.strip()),
        ])

    return np.asarray(rows, dtype=float)


def build_features(train_df, other_df):
    """Fit all feature transformations on train only."""
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
        src_vec.fit_transform(train_df["source"].astype(str)),
        tgt_vec.fit_transform(train_df["target"].astype(str)),
    ]).tocsr()

    X_other_text = hstack([
        src_vec.transform(other_df["source"].astype(str)),
        tgt_vec.transform(other_df["target"].astype(str)),
    ]).tocsr()

    scaler = StandardScaler()
    raw_train = scaler.fit_transform(text_features(train_df))
    raw_other = scaler.transform(text_features(other_df))

    X_train = hstack([
        X_train_text,
        csr_matrix(raw_train),
    ]).tocsr()

    X_other = hstack([
        X_other_text,
        csr_matrix(raw_other),
    ]).tocsr()

    return X_train, X_other


# Primary definition remains >= 2 votes.
# Alternative thresholds are evaluated on dev only.
thresholds = {
    "strict_votes_ge_3": 3,
    "primary_votes_ge_2": 2,
    "inclusive_votes_ge_1": 1,
}

X_train, X_dev = build_features(train, dev)
rows = []

for label_name, threshold in thresholds.items():
    y_train = (
        pd.to_numeric(train["serious_votes"]) >= threshold
    ).astype(int)

    y_dev = (
        pd.to_numeric(dev["serious_votes"]) >= threshold
    ).astype(int)

    model = LogisticRegression(
        class_weight="balanced",
        C=1.0,
        max_iter=2000,
        random_state=SEED,
    )
    model.fit(X_train, y_train)

    scores = model.predict_proba(X_dev)[:, 1]

    n_top = max(1, math.ceil(TOP_FRACTION * len(dev)))
    order = np.argsort(-scores, kind="stable")
    top_idx = order[:n_top]

    y_pred_top = np.zeros(len(dev), dtype=int)
    y_pred_top[top_idx] = 1

    prevalence = float(y_dev.mean())
    precision_top = float(y_dev.iloc[top_idx].mean())
    recall_top = (
        float(y_dev.iloc[top_idx].sum() / y_dev.sum())
        if y_dev.sum() > 0 else np.nan
    )
    lift_top = (
        precision_top / prevalence
        if prevalence > 0 else np.nan
    )

    rows.append({
        "label_definition": label_name,
        "threshold": f"serious_votes >= {threshold}",
        "n_positive": int(y_dev.sum()),
        "n_negative": int((y_dev == 0).sum()),
        "prevalence": prevalence,
        "PR_AUC": float(average_precision_score(y_dev, scores)),
        "Precision_at_20pct": precision_top,
        "Recall_at_20pct": recall_top,
        "Lift_at_20pct": lift_top,
        "MCC_at_20pct": float(
            matthews_corrcoef(y_dev, y_pred_top)
        ),
        "n_reviewed_at_20pct": int(n_top),
    })

results = pd.DataFrame(rows)
output_path = OUT_DIR / "dev_label_sensitivity.csv"
results.to_csv(output_path, index=False)

print("\n=== DEV LABEL SENSITIVITY ANALYSIS ===")
print(results.round(4).to_string(index=False))
print(f"\nSaved to: {output_path}")
print("\nNote: all vectorizers and the scaler were fitted on train only.")
print("The test set was not loaded or evaluated.")
