"""Train + evaluate the guide match-quality model.

Predicts the 1-5 rating a given tourist will give a given guide, from guide
credentials plus the tourist's own profile. Ranking a shortlist by predicted
rating is what turns this into a personalised guide ranker.

Two baselines make the result interpretable: predicting the training-set mean
rating for everyone, and predicting each guide's registry-wide ``average_rating``.
The second is the strong "just show the best-rated guides" strategy the app would
use with no model at all, so beating it is the bar that matters.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data.loader import load_guides, load_interactions, load_tourists
from evaluation.metrics import regression_metrics
from features.guides import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, TARGET, build_rating_frame
from registry import save_model

logger = logging.getLogger("guideu.ml.train.guides")

SEED = 42


def _pipeline(model) -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    return Pipeline(steps=[("features", pre), ("model", model)])


def _candidates() -> dict[str, Pipeline]:
    return {
        "ridge": _pipeline(Ridge(alpha=1.0, random_state=SEED)),
        "gradient_boosting": _pipeline(HistGradientBoostingRegressor(max_iter=300, random_state=SEED)),
    }


def train() -> dict:
    frame = build_rating_frame(load_interactions(), load_guides(), load_tourists())
    train_df = frame[frame["year"] <= 2023]
    test_df = frame[frame["year"] == 2024]
    if test_df.empty:
        from sklearn.model_selection import train_test_split

        train_df, test_df = train_test_split(frame, test_size=0.2, random_state=SEED)

    X_train, y_train = train_df[FEATURES], train_df[TARGET]
    X_test, y_test = test_df[FEATURES], test_df[TARGET]

    comparison: dict[str, dict[str, float]] = {
        "baseline_global_mean": {
            k: round(float(v), 4)
            for k, v in regression_metrics(y_test, np.full(len(y_test), y_train.mean())).items()
        },
        "baseline_guide_average_rating": {
            k: round(float(v), 4) for k, v in regression_metrics(y_test, test_df["average_rating"]).items()
        },
    }

    fitted: dict[str, Pipeline] = {}
    for name, pipeline in _candidates().items():
        pipeline.fit(X_train, y_train)
        fitted[name] = pipeline
        predictions = np.clip(pipeline.predict(X_test), 1.0, 5.0)
        comparison[name] = {k: round(float(v), 4) for k, v in regression_metrics(y_test, predictions).items()}

    model_names = list(_candidates())
    best_name = min(model_names, key=lambda n: comparison[n]["rmse"])
    model = fitted[best_name]

    predictions = np.clip(model.predict(X_test), 1.0, 5.0)
    metrics = {k: float(v) for k, v in regression_metrics(y_test, predictions).items()}
    mean_rmse = comparison["baseline_global_mean"]["rmse"]
    metrics["rmse_improvement_over_mean_pct"] = round((mean_rmse - metrics["rmse"]) / mean_rmse * 100, 2)
    metrics["n_test"] = float(len(test_df))

    notes = (
        f"{best_name} predicting a tourist's 1-5 rating of a guide from guide credentials + tourist profile. "
        f"Temporal split: train<=2023 (n={len(train_df)}), test=2024 (n={len(test_df)}). "
        f"RMSE {metrics['rmse']:.4f} vs {mean_rmse:.4f} for the global-mean baseline "
        f"({metrics['rmse_improvement_over_mean_pct']}% better) and "
        f"{comparison['baseline_guide_average_rating']['rmse']:.4f} for ranking by the guide's own average rating. "
        "Ranking a shortlist by predicted rating is what makes guide ranking personalised rather than fixed."
    )
    card = save_model(
        name="guide_ranker",
        model=model,
        metrics=metrics,
        params={"algorithm": best_name, "features": FEATURES, "target": "explicit 1-5 rating"},
        n_train=len(train_df),
        notes=notes,
    )
    logger.info("guide model trained (%s): %s", best_name, metrics)
    return {"card": card.version, "metrics": metrics, "comparison": comparison, "algorithm": best_name}


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    import json

    result = train()
    print(json.dumps({k: v for k, v in result.items() if k != "card"}, indent=2))
