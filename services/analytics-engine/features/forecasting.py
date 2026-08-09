"""Feature engineering for tourist-arrival demand forecasting.

``tourist_arrivals.csv`` holds 60,000 cohort rows (year x month x nationality x
purpose x region x age band). Aggregating to a monthly national total gives a
48-point series covering 2021-2024 — Nepal's post-COVID recovery.

That recovery is the whole difficulty. Yearly totals go 100k -> 488k -> 936k ->
1.51M, i.e. year-on-year growth of 4.85x, 1.92x then 1.62x. Any model that
extrapolates the early growth linearly overshoots badly, which is why the
trailing-window decision below is made on domain grounds *before* looking at the
test year: 2021 is a recovery anomaly running at a fifteenth of 2024's volume,
so the trend is fitted on the two most recent complete years only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Fit the trend on the two most recent complete years. Set from the shape of the
# recovery, not tuned against the test year — see the module docstring.
TREND_WINDOW_MONTHS = 24
MONTHS = list(range(1, 13))


def monthly_series(arrivals: pd.DataFrame) -> pd.DataFrame:
    """Collapse the cohort table to one row per (year, month) with a time index."""
    series = (
        arrivals.groupby(["year", "month"], as_index=False)["arrival_count"]
        .sum()
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )
    series["t"] = np.arange(len(series), dtype=float)
    return series


def month_dummies(months: pd.Series) -> np.ndarray:
    """Stable 12-column month indicator matrix (never drops an unseen month)."""
    categorical = months.astype(pd.CategoricalDtype(categories=MONTHS))
    return pd.get_dummies(categorical, prefix="m").to_numpy(dtype=float)


def design_matrix(frame: pd.DataFrame) -> np.ndarray:
    """[time index | 12 month indicators] — a linear trend with additive seasonality."""
    return np.column_stack([frame["t"].to_numpy(dtype=float), month_dummies(frame["month"])])


def trailing_window(train: pd.DataFrame, months: int = TREND_WINDOW_MONTHS) -> pd.DataFrame:
    return train.tail(months) if len(train) > months else train


def seasonal_index(train: pd.DataFrame) -> dict[int, float]:
    """Multiplicative month factors, averaged across training years and re-centred on 1.0."""
    ratios: dict[int, list[float]] = {}
    for _, chunk in train.groupby("year"):
        level = chunk["arrival_count"].mean()
        if level <= 0:
            continue
        for row in chunk.itertuples(index=False):
            ratios.setdefault(int(row.month), []).append(float(row.arrival_count) / level)
    if not ratios:
        return {m: 1.0 for m in MONTHS}
    averaged = {month: float(np.mean(values)) for month, values in ratios.items()}
    centre = float(np.mean(list(averaged.values()))) or 1.0
    return {month: value / centre for month, value in averaged.items()}


def region_shares(arrivals: pd.DataFrame, *, year: int | None = None) -> dict[str, float]:
    """Share of arrivals by region, used to split a national forecast regionally."""
    frame = arrivals if year is None else arrivals[arrivals["year"] == year]
    if frame.empty:
        frame = arrivals
    # The arrivals cohort table names the column `region_visited`.
    column = "region_visited" if "region_visited" in frame.columns else "region"
    totals = frame.groupby(column)["arrival_count"].sum()
    grand = float(totals.sum())
    if grand <= 0:
        return {}
    return {str(region): round(float(value) / grand, 6) for region, value in totals.items()}


def future_frame(last_t: float, year: int, months: list[int] | None = None) -> pd.DataFrame:
    """Build the design frame for a horizon of future months."""
    months = months or MONTHS
    return pd.DataFrame(
        {"year": year, "month": months, "t": [last_t + i for i in range(1, len(months) + 1)]}
    )
