"""Feature engineering for the verified-guide ranking model.

The original ranker was a fixed weighted sum over certification tier, rating,
region overlap and language overlap. It was defensible but it was not learned:
nothing in it came from the data, so it could not be evaluated and could not be
wrong in a measurable way.

This module builds the supervised alternative. The label is the explicit 1-5
rating a tourist gave a guide in ``recommendation_interactions.csv`` (~4.3k
rated pairs), and the task is to predict how well a *particular* tourist will
rate a *particular* guide — i.e. match quality, not general guide quality.
Ranking candidates by predicted rating then personalises the shortlist.

A caveat worth stating: ``average_rating`` is the guide's registry-wide rating
and is not recomputed per period, so it carries a little information from the
test window. It is kept because the app shows it to users anyway, and because on
its own it predicts *worse* than the global mean (RMSE 0.705 vs 0.688), so it is
a weak feature rather than a leak that would flatter the model.
"""
from __future__ import annotations

import pandas as pd

GUIDE_CATEGORICAL = ["certification", "verification_status"]
TOURIST_CATEGORICAL = ["experience_level", "budget_band", "travel_style"]
CATEGORICAL_FEATURES = GUIDE_CATEGORICAL + TOURIST_CATEGORICAL

GUIDE_NUMERIC = ["years_experience", "average_rating", "total_trips_completed", "n_languages", "n_regions"]
TOURIST_NUMERIC = [
    "pref_adventure_score",
    "pref_culture_score",
    "pref_nature_score",
    "risk_tolerance",
    "price_sensitivity",
    "age",
]
NUMERIC_FEATURES = GUIDE_NUMERIC + TOURIST_NUMERIC

FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "rating"

# Sensible fallbacks so a partially-populated API payload still scores.
DEFAULTS = {
    "certification": "Government Trekking Guide",
    "verification_status": "Verified",
    "experience_level": "First-time",
    "budget_band": "Mid-range",
    "travel_style": "Solo",
    "years_experience": 5.0,
    "average_rating": 4.0,
    "total_trips_completed": 50.0,
    "n_languages": 2.0,
    "n_regions": 2.0,
    "pref_adventure_score": 0.5,
    "pref_culture_score": 0.5,
    "pref_nature_score": 0.5,
    "risk_tolerance": 0.5,
    "price_sensitivity": 0.5,
    "age": 35.0,
}


def _count_csv_field(series: pd.Series) -> pd.Series:
    """'Nepali, English, French' -> 3. Empty/missing -> 0."""
    text = series.fillna("").astype(str).str.strip()
    counted = text.str.count(",") + 1
    return counted.where(text != "", 0)


def add_guide_counts(guides: pd.DataFrame) -> pd.DataFrame:
    """Add the derived language/region breadth columns."""
    frame = guides.copy()
    frame["n_languages"] = _count_csv_field(frame["languages_spoken"])
    frame["n_regions"] = _count_csv_field(frame["regions_covered"])
    return frame


def build_rating_frame(
    interactions: pd.DataFrame, guides: pd.DataFrame, tourists: pd.DataFrame
) -> pd.DataFrame:
    """Join rated (tourist, guide) pairs onto both profiles. One row per rating."""
    rated = interactions[(interactions["item_type"] == "Guide") & interactions["rating"].notna()].copy()
    rated["year"] = pd.to_datetime(rated["interaction_date"]).dt.year
    joined = rated.merge(add_guide_counts(guides), left_on="item_id", right_on="guide_id", how="inner").merge(
        tourists, on="tourist_id", how="inner"
    )
    return joined


def build_inference_frame(tourist: dict, candidates: list[dict]) -> pd.DataFrame:
    """Design matrix for one tourist against a list of candidate guides."""
    rows = []
    for guide in candidates:
        row = {}
        for name in FEATURES:
            value = guide.get(name, tourist.get(name))
            row[name] = DEFAULTS[name] if value is None else value
        # Breadth counts are derived when the caller sends raw CSV strings.
        if guide.get("languages_spoken") is not None:
            row["n_languages"] = float(len([p for p in str(guide["languages_spoken"]).split(",") if p.strip()]))
        if guide.get("regions_covered") is not None:
            row["n_regions"] = float(len([p for p in str(guide["regions_covered"]).split(",") if p.strip()]))
        rows.append(row)
    frame = pd.DataFrame(rows, columns=FEATURES)
    for name in NUMERIC_FEATURES:
        frame[name] = pd.to_numeric(frame[name], errors="coerce").fillna(DEFAULTS[name])
    for name in CATEGORICAL_FEATURES:
        frame[name] = frame[name].fillna(DEFAULTS[name]).astype(str)
    return frame


def coverage_bonus(csv_field: str | None, wanted: str | None) -> float:
    """Does the guide cover the region / speak the language the tourist asked for?

    Kept as an explicit post-model filter rather than a feature: the dataset has
    no signal linking a tourist's survey scores to the region they pick, so the
    model cannot learn it, but a guide who does not work in the requested region
    is simply not a valid candidate.
    """
    if not wanted:
        return 1.0
    items = {part.strip().lower() for part in str(csv_field or "").split(",")}
    return 1.0 if wanted.strip().lower() in items else 0.0
