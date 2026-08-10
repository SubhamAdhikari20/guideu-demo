"""Online demand forecasting.

Projects monthly tourist arrivals forward from the trained log-trend model and
splits the national total by region using recent historical shares. The admin
dashboard uses this to plan guide capacity, and the app uses it to tell a
traveller whether the month they picked is a busy one.

Forecasts are returned with an explicit accuracy caveat. The model was fitted on
three years of post-COVID recovery, and its own evaluation shows model selection
is unstable on that much data, so presenting a bare number without the error
band would overstate what it knows.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from features.forecasting import MONTHS, design_matrix
from registry import get_card, load_model

# Typical error from the 2024 held-out year, used to render a band.
FALLBACK_MAPE = 17.2

# How far past the last observed year the trend may be projected before the
# result stops being meaningful. The model multiplies a growth rate every month,
# so two or three years out it compounds a post-COVID recovery rate far beyond
# anything the market could sustain — projecting 2026 from data ending in 2024
# produced 6.5M arrivals against a real-world figure nearer 1.15M. Beyond this
# horizon the caller gets an explicit warning rather than a confident number.
MAX_RELIABLE_HORIZON_YEARS = 1


@lru_cache(maxsize=1)
def _artifact() -> dict | None:
    return load_model("arrivals_forecaster")


def _seasonal_fallback(artifact: dict, months: list[int], horizon_year: int) -> np.ndarray:
    """Last observed year's level times the stored seasonal index."""
    history = pd.DataFrame(artifact["history"])
    last_year = int(history["year"].max())
    level = history[history["year"] == last_year]["arrival_count"].mean()
    index = artifact.get("seasonal_index", {})
    steps = max(horizon_year - last_year, 0)
    return np.array([level * float(index.get(m, index.get(str(m), 1.0))) for m in months]) * (1.0 ** steps)


def forecast(*, year: int | None = None, months: list[int] | None = None, region: str | None = None) -> dict:
    artifact = _artifact()
    months = months or MONTHS

    if not artifact:
        return {"model_version": "untrained", "year": year, "items": [], "note": "Forecast model not trained yet."}

    last_year = int(artifact["last_year"])
    target_year = year or last_year + 1
    last_t = float(artifact["last_t"])
    steps_to_year = (target_year - last_year - 1) * 12

    frame = pd.DataFrame(
        {"month": months, "t": [last_t + steps_to_year + i for i in range(1, len(months) + 1)]}
    )
    model = artifact.get("model")
    if model is not None:
        predicted = np.exp(model.predict(design_matrix(frame)))
    else:
        predicted = _seasonal_fallback(artifact, months, target_year)

    share = 1.0
    shares = artifact.get("region_shares", {})
    if region:
        share = float(shares.get(region, 0.0))

    card = get_card("arrivals_forecaster")
    mape = float(card.metrics.get("mape", FALLBACK_MAPE)) if card else FALLBACK_MAPE
    band = mape / 100.0

    items = []
    for month, value in zip(months, predicted):
        point = float(value) * share
        items.append(
            {
                "year": target_year,
                "month": int(month),
                "predicted_arrivals": int(round(point)),
                "lower_estimate": int(round(point * (1 - band))),
                "upper_estimate": int(round(point * (1 + band))),
            }
        )

    peak = max(items, key=lambda row: row["predicted_arrivals"]) if items else None
    horizon = max(target_year - last_year, 0)

    note = (
        "Fitted on three years of post-COVID recovery data; treat the band, not the point estimate, "
        "as the forecast."
    )
    if horizon > MAX_RELIABLE_HORIZON_YEARS:
        note = (
            f"Projected {horizon} years past the last observed year ({last_year}). The trend compounds a "
            "post-COVID recovery rate, so figures this far out overstate demand badly and should not be "
            f"planned against — forecast {last_year + 1} for a usable number. " + note
        )

    return {
        "model_version": card.version if card else "arrivals_forecaster",
        "year": target_year,
        "region": region,
        "expected_error_pct": round(mape, 2),
        "peak_month": peak["month"] if peak else None,
        "items": items,
        # Let callers default their year picker to the last year the model can
        # actually speak to, instead of "whatever year it is now".
        "last_observed_year": last_year,
        "horizon_years": horizon,
        "reliable": horizon <= MAX_RELIABLE_HORIZON_YEARS,
        "note": note,
    }


def region_options() -> list[str]:
    artifact = _artifact()
    return sorted((artifact or {}).get("region_shares", {}).keys())


def clear_cache() -> None:
    _artifact.cache_clear()
