"""Train + evaluate the tourist-arrivals demand forecaster.

Model: ordinary least squares on ``log(arrivals) ~ time + month indicators``,
fitted on the trailing 24 months. Logs make the seasonality multiplicative,
which is what a recovering series needs — a month is a *percentage* of the
year's level, not a fixed number of visitors.

The script scores three naive baselines alongside it and reports the 2023
validation year as well as the 2024 test year, because with only three years of
post-COVID data the two years disagree about which method wins. Reporting both
is the honest thing to do: it shows the model selection is fragile rather than
implying a robust winner.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from data.loader import load_arrivals
from evaluation.metrics import forecast_metrics
from features.forecasting import (
    TREND_WINDOW_MONTHS,
    design_matrix,
    monthly_series,
    region_shares,
    seasonal_index,
    trailing_window,
)
from registry import save_model

logger = logging.getLogger("guideu.ml.train.forecast")


def _fit_log_trend(train: pd.DataFrame) -> LinearRegression:
    window = trailing_window(train)
    return LinearRegression().fit(design_matrix(window), np.log(window["arrival_count"].to_numpy(dtype=float)))


def _baselines(series: pd.DataFrame, train: pd.DataFrame, test: pd.DataFrame) -> dict[str, np.ndarray]:
    last_year = int(train["year"].max())
    same_month_last_year = train[train["year"] == last_year].set_index("month")["arrival_count"]
    naive = test["month"].map(same_month_last_year).to_numpy(dtype=float)

    previous = train[train["year"] == last_year - 1]["arrival_count"].sum()
    growth = train[train["year"] == last_year]["arrival_count"].sum() / previous if previous else 1.0

    return {
        "seasonal_naive": naive,
        "seasonal_naive_x_growth": naive * growth,
        "last_12_month_mean": np.full(len(test), train[train["year"] == last_year]["arrival_count"].mean()),
    }


def _score_split(series: pd.DataFrame, test_year: int) -> dict[str, dict[str, float]]:
    train = series[series["year"] < test_year]
    test = series[series["year"] == test_year].sort_values("month")
    if train.empty or test.empty:
        return {}

    actual = test["arrival_count"].to_numpy(dtype=float)
    scored = {
        name: {k: round(float(v), 4) for k, v in forecast_metrics(actual, prediction).items()}
        for name, prediction in _baselines(series, train, test).items()
    }
    model = _fit_log_trend(train)
    prediction = np.exp(model.predict(design_matrix(test)))
    scored["log_trend_seasonal"] = {k: round(float(v), 4) for k, v in forecast_metrics(actual, prediction).items()}
    return scored


def train() -> dict:
    arrivals = load_arrivals()
    series = monthly_series(arrivals)

    years = sorted(series["year"].unique())
    test_year = int(years[-1])
    validation_year = int(years[-2])

    validation = _score_split(series, validation_year)
    comparison = _score_split(series, test_year)

    train_df = series[series["year"] < test_year]
    test_df = series[series["year"] == test_year].sort_values("month")

    # Model used for the honest metrics below: it has never seen the test year.
    evaluation_model = _fit_log_trend(train_df)
    prediction = np.exp(evaluation_model.predict(design_matrix(test_df)))
    actual = test_df["arrival_count"].to_numpy(dtype=float)

    # Model that actually ships: refitted on every observation including the test
    # year. Registering the evaluation model instead would leave the served
    # forecaster a year behind its own `last_year`, so each request extrapolated
    # one extra year of compounding growth and overstated demand.
    serving_model = _fit_log_trend(series)

    metrics = {k: float(v) for k, v in forecast_metrics(actual, prediction).items()}
    best_baseline = min(
        (name for name in comparison if name != "log_trend_seasonal"),
        key=lambda n: comparison[n]["mape"],
    )
    metrics["best_baseline_mape"] = comparison[best_baseline]["mape"]
    metrics["mape_improvement_over_seasonal_naive_pct"] = round(
        (comparison["seasonal_naive"]["mape"] - metrics["mape"]) / comparison["seasonal_naive"]["mape"] * 100, 2
    )

    artifact = {
        "model": serving_model,
        "last_t": float(series["t"].max()),
        "last_year": int(series["year"].max()),
        "seasonal_index": seasonal_index(series),
        "region_shares": region_shares(arrivals, year=test_year),
        "history": series[["year", "month", "arrival_count"]].to_dict("records"),
    }
    notes = (
        f"Log-linear trend + month indicators on the trailing {TREND_WINDOW_MONTHS} months. "
        f"Train {int(train_df['year'].min())}-{int(train_df['year'].max())}, test {test_year}. "
        f"MAPE {metrics['mape']:.2f}% vs {comparison['seasonal_naive']['mape']:.2f}% for a seasonal naive "
        f"forecast ({metrics['mape_improvement_over_seasonal_naive_pct']}% better). "
        f"Note: on the {validation_year} validation year the naive baseline wins instead — three years of "
        "post-COVID recovery is not enough data for stable model selection, and the report says so. "
        f"These metrics come from a model fitted to {int(train_df['year'].min())}-{int(train_df['year'].max())}; "
        f"the registered artifact is refitted on the full series through {test_year} so that serving a "
        f"{test_year + 1} forecast is a one-year step rather than two."
    )
    card = save_model(
        name="arrivals_forecaster",
        model=artifact,
        metrics=metrics,
        params={
            "algorithm": "LinearRegression on log(arrivals) ~ t + month",
            "trend_window_months": TREND_WINDOW_MONTHS,
            "test_year": test_year,
            "validation_year": validation_year,
        },
        n_train=int(len(train_df)),
        notes=notes,
    )
    logger.info("forecaster trained: %s", metrics)
    return {
        "card": card.version,
        "metrics": metrics,
        "comparison": comparison,
        "validation": validation,
        "per_month": [
            {"month": int(m), "actual": int(a), "predicted": int(round(p))}
            for m, a, p in zip(test_df["month"], actual, prediction)
        ],
    }


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    import json

    result = train()
    print(json.dumps({k: v for k, v in result.items() if k != "card"}, indent=2))
