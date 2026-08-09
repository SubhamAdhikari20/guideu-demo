"""Evaluation metrics for the GuideU models.

Grouped by task: classification (anti-scam), ranking (recommender, guide
ranking), regression (guide match quality) and forecasting (arrivals). Every
model is reported against at least one baseline computed with the same harness,
so the numbers in the thesis are comparable rather than free-floating.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

# --------------------------------------------------------------------------- #
# classification
# --------------------------------------------------------------------------- #


def classification_metrics(y_true, y_prob, threshold: float = 0.5) -> dict[str, float]:
    """Standard binary-classification metrics for the scam model.

    ``brier`` is included deliberately: the app shows a probability to the user,
    so calibration matters as much as ranking quality.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= threshold).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }
    # AUC metrics require both classes present.
    if len(np.unique(y_true)) > 1:
        metrics["roc_auc"] = roc_auc_score(y_true, y_prob)
        metrics["pr_auc"] = average_precision_score(y_true, y_prob)
        metrics["brier"] = brier_score_loss(y_true, y_prob)
    return metrics


def best_f1_threshold(y_true, y_prob, grid: Sequence[float] | None = None) -> tuple[float, float]:
    """Pick the decision threshold that maximises F1 on the given split.

    Returns ``(threshold, f1)``. Call this on a *validation* split only — using
    the test split would tune on the data you then report.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    grid = grid if grid is not None else np.round(np.arange(0.05, 0.96, 0.05), 2)
    scored = [(float(t), float(f1_score(y_true, (y_prob >= t).astype(int), zero_division=0))) for t in grid]
    return max(scored, key=lambda pair: pair[1])


def roc_auc_or_none(y_true, y_prob) -> float | None:
    """ROC-AUC, or None when only one class is present in the slice."""
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return None
    return round(float(roc_auc_score(y_true, np.asarray(y_prob))), 4)


# --------------------------------------------------------------------------- #
# ranking
# --------------------------------------------------------------------------- #


def precision_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    top = recommended_ids[:k]
    return sum(1 for item in top if item in relevant_ids) / k


def recall_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    top = recommended_ids[:k]
    return sum(1 for item in top if item in relevant_ids) / len(relevant_ids)


def hit_rate_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    """1.0 when at least one relevant item appears in the top-k."""
    return 1.0 if set(recommended_ids[:k]) & relevant_ids else 0.0


def reciprocal_rank(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    for position, item in enumerate(recommended_ids[:k], start=1):
        if item in relevant_ids:
            return 1.0 / position
    return 0.0


def ndcg_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    top = recommended_ids[:k]
    dcg = sum(1.0 / np.log2(i + 2) for i, item in enumerate(top) if item in relevant_ids)
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return float(dcg / idcg) if idcg else 0.0


def average_precision_at_k(recommended_ids: Sequence[str], relevant_ids: set[str], k: int) -> float:
    """AP@k — rewards putting relevant items early, not just including them."""
    if not relevant_ids:
        return 0.0
    hits = 0
    total = 0.0
    for position, item in enumerate(recommended_ids[:k], start=1):
        if item in relevant_ids:
            hits += 1
            total += hits / position
    return total / min(len(relevant_ids), k)


def ranking_metrics(recommended_ids: Sequence[str], relevant_ids: set[str], k: int = 10) -> dict[str, float]:
    """All ranking metrics for a single user's recommendation list."""
    return {
        "precision_at_5": precision_at_k(recommended_ids, relevant_ids, 5),
        f"precision_at_{k}": precision_at_k(recommended_ids, relevant_ids, k),
        f"recall_at_{k}": recall_at_k(recommended_ids, relevant_ids, k),
        f"hit_rate_at_{k}": hit_rate_at_k(recommended_ids, relevant_ids, k),
        f"ndcg_at_{k}": ndcg_at_k(recommended_ids, relevant_ids, k),
        f"map_at_{k}": average_precision_at_k(recommended_ids, relevant_ids, k),
        f"mrr_at_{k}": reciprocal_rank(recommended_ids, relevant_ids, k),
    }


def mean_metrics(rows: Iterable[dict[str, float]]) -> dict[str, float]:
    """Average a sequence of per-user metric dicts."""
    rows = list(rows)
    if not rows:
        return {}
    keys = rows[0].keys()
    return {key: float(np.mean([row[key] for row in rows])) for key in keys}


# --------------------------------------------------------------------------- #
# regression & forecasting
# --------------------------------------------------------------------------- #


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def forecast_metrics(y_true, y_pred) -> dict[str, float]:
    """MAE / RMSE / MAPE. MAPE is the headline for arrivals — the scale changes
    by an order of magnitude across the series, so absolute error alone misleads.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    safe = np.where(y_true == 0, np.nan, y_true)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mape": float(np.nanmean(np.abs((y_true - y_pred) / safe)) * 100),
    }
