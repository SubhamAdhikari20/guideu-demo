"""Train + evaluate the anti-scam classifier on ``scam_reports.csv``.

Two models are fitted through the same pipeline: a logistic regression, kept as
the readable baseline, and a gradient-boosted tree, which wins and is the one
registered. Beyond the ordinary temporal split the script runs two checks the
thesis leans on:

* a **cold-cell test** that holds out entire (service_type, region) combinations,
  because in production a tourist will type in a service/region pair the model
  never saw and the useful question is whether it still judges the quote;
* a **fairness audit** by continent, since the dataset deliberately simulates
  nationality-based price discrimination.

The decision threshold is chosen on a validation year (2023) rather than on the
2024 test year, so the reported operating point is not tuned on what it reports.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data.loader import load_scam_reports, load_tourists
from evaluation.fairness import fairness_report
from evaluation.metrics import best_f1_threshold, classification_metrics, roc_auc_or_none
from features.scam import CATEGORICAL_FEATURES, FEATURES, NUMERIC_FEATURES, build_scam_frame, season_from_month
from registry import save_model

logger = logging.getLogger("guideu.ml.train.scam")

SEED = 42
HOLDOUT_CELL_FRACTION = 0.2


def _pipeline(model) -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    return Pipeline(steps=[("features", pre), ("clf", model)])


def _candidates() -> dict[str, Pipeline]:
    return {
        "logistic_regression": _pipeline(LogisticRegression(max_iter=1000, class_weight="balanced")),
        "gradient_boosting": _pipeline(HistGradientBoostingClassifier(max_iter=300, random_state=SEED)),
    }


def _cold_cell_check(df: pd.DataFrame) -> dict:
    """Hold out whole (service, region) cells to test generalisation to unseen combinations."""
    cells = df[["service_type", "region"]].drop_duplicates()
    held = cells.sample(frac=HOLDOUT_CELL_FRACTION, random_state=SEED)
    held_keys = set(held["service_type"] + "|" + held["region"])
    keys = df["service_type"] + "|" + df["region"]

    train_df = df[~keys.isin(held_keys)]
    test_df = df[keys.isin(held_keys)]
    X_train, y_train = build_scam_frame(train_df)
    X_test, y_test = build_scam_frame(test_df)

    results = {}
    for name, pipeline in _candidates().items():
        pipeline.fit(X_train, y_train)
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        scored = classification_metrics(y_test, probabilities)
        results[name] = {k: round(float(v), 4) for k, v in scored.items()}
    results["n_held_out_cells"] = len(held_keys)
    results["n_test_rows"] = len(test_df)
    return results


def train() -> dict:
    df = load_scam_reports()
    # Join continent for the fairness audit only — NOT used as a feature.
    tourists = load_tourists()[["tourist_id", "continent"]]
    df = df.merge(tourists, on="tourist_id", how="left")
    reported = pd.to_datetime(df["reported_date"])
    df["year"] = reported.dt.year
    df["season"] = reported.dt.month.map(season_from_month)

    fit_df = df[df["year"] <= 2022]         # fit for threshold selection
    validation_df = df[df["year"] == 2023]  # choose the operating point here
    train_df = df[df["year"] <= 2023]       # final fit
    test_df = df[df["year"] == 2024]        # report here

    if test_df.empty or validation_df.empty:
        from sklearn.model_selection import train_test_split

        train_df, test_df = train_test_split(df, test_size=0.2, random_state=SEED, stratify=df["was_flagged_by_app"])
        fit_df, validation_df = train_test_split(
            train_df, test_size=0.25, random_state=SEED, stratify=train_df["was_flagged_by_app"]
        )

    X_train, y_train = build_scam_frame(train_df)
    X_test, y_test = build_scam_frame(test_df)

    # ---------------- model selection on the validation year ----------------
    X_fit, y_fit = build_scam_frame(fit_df)
    X_val, y_val = build_scam_frame(validation_df)
    validation_scores: dict[str, dict[str, float]] = {}
    thresholds: dict[str, float] = {}
    for name, pipeline in _candidates().items():
        pipeline.fit(X_fit, y_fit)
        probabilities = pipeline.predict_proba(X_val)[:, 1]
        threshold, _ = best_f1_threshold(y_val, probabilities)
        thresholds[name] = threshold
        validation_scores[name] = {
            k: round(float(v), 4) for k, v in classification_metrics(y_val, probabilities, threshold).items()
        }

    best_name = max(validation_scores, key=lambda n: validation_scores[n]["f1"])
    best_threshold = thresholds[best_name]

    # ---------------- refit the winner on all training data, report on test ----------------
    comparison: dict[str, dict[str, float]] = {}
    fitted: dict[str, Pipeline] = {}
    for name, pipeline in _candidates().items():
        pipeline.fit(X_train, y_train)
        fitted[name] = pipeline
        probabilities = pipeline.predict_proba(X_test)[:, 1]
        comparison[name] = {
            k: round(float(v), 4) for k, v in classification_metrics(y_test, probabilities, thresholds[name]).items()
        }
    # Majority-class baseline for context (predict "not flagged" for everything).
    comparison["majority_baseline"] = {
        k: round(float(v), 4) for k, v in classification_metrics(y_test, np.zeros(len(y_test))).items()
    }

    model = fitted[best_name]
    probabilities = model.predict_proba(X_test)[:, 1]
    metrics = classification_metrics(y_test, probabilities, best_threshold)
    metrics["decision_threshold"] = best_threshold

    fairness = fairness_report(test_df, y_test, probabilities, group_col="continent", threshold=best_threshold)
    metrics["fairness_flag_rate_disparity"] = fairness["flag_rate_disparity"]

    cold_cell = _cold_cell_check(df)
    metrics["cold_cell_roc_auc"] = cold_cell[best_name].get("roc_auc", 0.0)
    metrics["cold_cell_f1"] = cold_cell[best_name].get("f1", 0.0)

    notes = (
        f"{best_name} selected on the 2023 validation year (threshold {best_threshold}). "
        f"Temporal split: train<=2023 (n={len(train_df)}), test=2024 (n={len(test_df)}). "
        f"Cold-cell test over {cold_cell['n_held_out_cells']} unseen service x region combinations: "
        f"ROC-AUC {metrics['cold_cell_roc_auc']}, F1 {metrics['cold_cell_f1']}. "
        f"Fairness gate {'PASS' if fairness['passes'] else 'REVIEW'} "
        f"(continent flag-rate disparity={fairness['flag_rate_disparity']}). "
        "Protected attributes excluded from features; benchmark and overcharge ratio excluded to avoid label leakage."
    )
    card = save_model(
        name="scam_classifier",
        model=model,
        metrics=metrics,
        params={
            "algorithm": best_name,
            "decision_threshold": best_threshold,
            "features": FEATURES,
            "excluded_leaky": ["overcharge_ratio", "benchmark_price_npr", "scam_severity"],
            "excluded_protected": ["nationality", "continent"],
        },
        n_train=len(train_df),
        notes=notes,
    )
    logger.info("scam model trained (%s): %s", best_name, metrics)
    return {
        "card": card.version,
        "metrics": metrics,
        "comparison": comparison,
        "validation": validation_scores,
        "cold_cell": cold_cell,
        "fairness": fairness,
    }


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    import json

    result = train()
    print(json.dumps({k: v for k, v in result.items() if k != "card"}, indent=2, default=str))
