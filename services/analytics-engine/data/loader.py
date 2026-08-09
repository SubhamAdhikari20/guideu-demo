"""Dataset access layer.

Thin, cached readers over the Travel Planning CSVs. Keeping all file access here
means training, features, and inference never hardcode paths or column quirks.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import get_settings


def dataset_dir() -> Path:
    return Path(get_settings().dataset_dir)


def _read(name: str, **kwargs) -> pd.DataFrame:
    path = dataset_dir() / name
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file '{name}' not found in {dataset_dir()}. "
            "Set GUIDEU_DATASET_DIR or mount the Travel Planning package."
        )
    return pd.read_csv(path, **kwargs)


@lru_cache(maxsize=1)
def load_routes() -> pd.DataFrame:
    return _read("trekking_routes.csv")


@lru_cache(maxsize=1)
def load_guides() -> pd.DataFrame:
    return _read("verified_guides.csv")


@lru_cache(maxsize=1)
def load_tourists() -> pd.DataFrame:
    return _read("tourists.csv")


@lru_cache(maxsize=1)
def load_events() -> pd.DataFrame:
    return _read("cultural_events.csv")


@lru_cache(maxsize=1)
def load_pricing() -> pd.DataFrame:
    return _read("pricing_benchmarks.csv")


@lru_cache(maxsize=1)
def load_scam_reports() -> pd.DataFrame:
    df = _read("scam_reports.csv", parse_dates=["reported_date"])
    return df


@lru_cache(maxsize=1)
def load_interactions() -> pd.DataFrame:
    df = _read("recommendation_interactions.csv", parse_dates=["interaction_date"])
    return df


@lru_cache(maxsize=1)
def load_bookings() -> pd.DataFrame:
    return _read("bookings.csv", parse_dates=["booking_date", "travel_start_date", "travel_end_date"])


@lru_cache(maxsize=1)
def load_arrivals() -> pd.DataFrame:
    """Cohort-level arrivals — the input to demand forecasting."""
    return _read("tourist_arrivals.csv")


@lru_cache(maxsize=1)
def load_gamification() -> pd.DataFrame:
    """Badge/points log, used for the badge-affinity view of a segment."""
    return _read("gamification_log.csv", parse_dates=["earned_date"])


def clear_cache() -> None:
    for fn in (
        load_routes, load_guides, load_tourists, load_events, load_pricing,
        load_scam_reports, load_interactions, load_bookings, load_arrivals,
        load_gamification,
    ):
        fn.cache_clear()
