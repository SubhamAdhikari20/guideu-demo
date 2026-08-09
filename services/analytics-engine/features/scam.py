"""Feature engineering for the anti-scam classifier.

Design choices that matter for the thesis:

* **Protected attributes are excluded.** ``nationality`` / ``continent`` are
  never features — the dataset encodes a real-world nationality price-bias and we
  refuse to let the model launder that into automated discrimination. They are
  used only in the post-hoc fairness audit.
* **The trivially-leaking columns are excluded.** In the generator,
  ``was_flagged_by_app`` is a deterministic step function of ``overcharge_ratio``
  (0 below ~1.25, 1 above), and the ratio is just quote ÷ benchmark. Feeding
  either back would produce a meaningless perfect score. The model instead sees
  only what the app knows when a tourist types in a quote — the service, the
  region, the season and the price — so it has to learn the price band for that
  cell and judge the quote against it.
* **Season is derived, not looked up.** ``scam_reports.csv`` has no season
  column, but it has ``reported_date``, and the benchmark table is keyed by
  season. Deriving it from the month gives the model the same context the
  benchmark has, and it is equally available at request time.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FEATURES = ["quoted_price_npr", "log_quoted_price"]
CATEGORICAL_FEATURES = ["service_type", "region", "season"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "was_flagged_by_app"
PROTECTED = ["nationality", "continent"]  # documented, never used as features

# The four season tiers used by pricing_benchmarks.csv, mapped from calendar month.
MONTH_TO_SEASON = {
    12: "Off (Winter)", 1: "Off (Winter)", 2: "Off (Winter)",
    3: "Peak (Spring)", 4: "Peak (Spring)", 5: "Peak (Spring)",
    6: "Off (Monsoon)", 7: "Off (Monsoon)", 8: "Off (Monsoon)",
    9: "Peak (Autumn)", 10: "Peak (Autumn)", 11: "Peak (Autumn)",
}
DEFAULT_SEASON = "Peak (Autumn)"


def season_from_month(month: int) -> str:
    return MONTH_TO_SEASON.get(int(month), DEFAULT_SEASON)


def normalise_season(season: str | None, *, month: int | None = None) -> str:
    """Accept either a benchmark-style season, a plain season name, or a month."""
    if season:
        text = str(season).strip()
        if text in MONTH_TO_SEASON.values():
            return text
        simple = {
            "spring": "Peak (Spring)",
            "autumn": "Peak (Autumn)",
            "fall": "Peak (Autumn)",
            "winter": "Off (Winter)",
            "summer": "Off (Monsoon)",
            "monsoon": "Off (Monsoon)",
        }
        if text.lower() in simple:
            return simple[text.lower()]
    if month is not None:
        return season_from_month(month)
    return DEFAULT_SEASON


def build_scam_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) for training/evaluation."""
    frame = df.copy()
    if "season" not in frame.columns:
        frame["season"] = pd.to_datetime(frame["reported_date"]).dt.month.map(season_from_month)
    frame["log_quoted_price"] = np.log1p(frame["quoted_price_npr"].astype(float))
    return frame[FEATURES], frame[TARGET].astype(int)


def build_inference_row(
    *, service_type: str, region: str, quoted_price_npr: float, season: str | None = None
) -> pd.DataFrame:
    """Single-row feature frame for online scoring."""
    return pd.DataFrame(
        [
            {
                "service_type": service_type,
                "region": region,
                "season": normalise_season(season),
                "quoted_price_npr": float(quoted_price_npr),
                "log_quoted_price": float(np.log1p(quoted_price_npr)),
            }
        ]
    )
