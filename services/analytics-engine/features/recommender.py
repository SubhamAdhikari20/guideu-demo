"""Feature engineering for the route recommender.

The recommender is a **learned** ranker, not a hand-weighted score. For a
(tourist, route) pair we build a small, readable feature vector and train a
logistic model to predict "would this tourist choose this route?". Learning the
weights instead of setting them matters here: the exploratory analysis of the
dataset found that only one of the four hand-picked signals in the original
heuristic carries any information (see docs/ml.md), and a learned model
discovers that on its own rather than spending 20% of its score on noise.

Two dataset properties drive the design:

* **The catalog is cloned, twice over.** 2,000 route rows cover only 375
  distinct route names, and those 375 names are 26 real treks packaged as
  variants ("Everest Base Camp (Classic)", "(Budget)", "(Express)"...). A top-k
  of raw route IDs therefore fills with near-duplicates. The profile carries two
  grouping columns: ``concept`` (the full variant name, 375 values) is the
  granularity offline metrics are reported at, and ``trek`` (the base trek, 26
  values) is what the served list de-duplicates on, because showing a traveller
  four packagings of the same trail is not a shortlist.
* **Feedback is extremely sparse.** Users average 1.15 positive route events, so
  user-user or item-item collaborative filtering has almost nothing to work
  with. The features are therefore content/profile based, with popularity as the
  only collaborative term.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Tourist survey columns used as-is. These are the "who is asking" half of a pair.
USER_FEATURES = [
    "pref_adventure_score",
    "pref_culture_score",
    "pref_nature_score",
    "risk_tolerance",
    "price_sensitivity",
]

# Route columns, normalised to [0,1] so coefficients are comparable.
ITEM_FEATURES = ["difficulty_norm", "cost_norm", "altitude_norm", "duration_norm"]

# Cross terms — how well this route matches this tourist. ``gap_adventure`` is
# the one the model leans on; the others are kept so the thesis can show they
# were offered to the model and rejected.
CROSS_FEATURES = ["gap_adventure", "gap_altitude", "gap_cost"]

FEATURE_NAMES = USER_FEATURES + ITEM_FEATURES + CROSS_FEATURES + ["popularity"]

# Columns persisted in the model artifact so inference never re-reads the CSVs.
PROFILE_COLS = [
    "route_id", "route_name", "concept", "trek", "region", "difficulty", "difficulty_level",
    "best_seasons", "duration_days", "max_altitude_m", "estimated_cost_usd",
    "difficulty_norm", "cost_norm", "altitude_norm", "duration_norm", "popularity",
]

# "Everest Base Camp (Classic)" -> "Everest Base Camp".
VARIANT_SUFFIX = r"\s*\([^)]*\)\s*$"

SEASON_TOKENS = {
    "Spring": ["Spring", "All-year"],
    "Summer": ["Summer", "All-year"],
    "Monsoon": ["Summer", "All-year"],
    "Autumn": ["Autumn", "All-year"],
    "Winter": ["Winter", "All-year"],
}

POSITIVE_INTERACTIONS = ["Book", "Complete"]


def _minmax(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    if span == 0:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - series.min()) / span


def build_route_profile(routes: pd.DataFrame, interactions: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per route: normalised content features + a train-period popularity prior."""
    profile = routes.copy()
    profile["concept"] = profile["route_name"]
    profile["trek"] = profile["route_name"].str.replace(VARIANT_SUFFIX, "", regex=True)
    profile["difficulty_norm"] = ((profile["difficulty_level"].astype(float) - 1.0) / 3.0).clip(0, 1)
    profile["cost_norm"] = _minmax(profile["estimated_cost_usd"].astype(float))
    profile["altitude_norm"] = _minmax(profile["max_altitude_m"].astype(float))
    profile["duration_norm"] = _minmax(profile["duration_days"].astype(float))

    counts = None
    if interactions is not None and not interactions.empty:
        route_inter = interactions[interactions["item_type"] == "Route"]
        counts = route_inter.groupby("item_id").size().rename("interaction_count")
    if counts is not None:
        profile = profile.merge(counts, left_on="route_id", right_index=True, how="left")
    if "interaction_count" not in profile:
        profile["interaction_count"] = 0.0
    profile["interaction_count"] = profile["interaction_count"].fillna(0.0)

    peak = profile["interaction_count"].max()
    profile["popularity"] = profile["interaction_count"] / peak if peak else 0.0
    return profile


def item_matrix(profile: pd.DataFrame) -> np.ndarray:
    """(n_routes, 4) matrix of the normalised content features, in ITEM_FEATURES order."""
    return profile[ITEM_FEATURES].to_numpy(dtype=float)


def pair_features(user_vector: np.ndarray, items: np.ndarray, popularity: np.ndarray) -> np.ndarray:
    """Build the (n_items, n_features) design matrix for one tourist against many routes.

    ``user_vector`` follows USER_FEATURES order; ``items`` follows ITEM_FEATURES
    order. Vectorised over items so scoring the whole 2,000-route catalog for a
    single request stays a couple of milliseconds.
    """
    user_vector = np.asarray(user_vector, dtype=float)
    n = len(items)
    adventure = user_vector[0]
    price_sensitivity = user_vector[4]

    repeated = np.repeat(user_vector.reshape(1, -1), n, axis=0)
    gap_adventure = np.abs(items[:, 0] - adventure).reshape(-1, 1)
    gap_altitude = np.abs(items[:, 2] - adventure).reshape(-1, 1)
    # A price-sensitive tourist should prefer a cheaper route: compare the route's
    # normalised cost against (1 - price_sensitivity) as the tolerated cost level.
    gap_cost = np.abs(items[:, 1] - (1.0 - price_sensitivity)).reshape(-1, 1)

    return np.hstack([repeated, items, gap_adventure, gap_altitude, gap_cost, popularity.reshape(-1, 1)])


def user_vector(tourist: dict) -> np.ndarray:
    """Map an API payload (or a dataset row) onto USER_FEATURES, defaulting to neutral 0.5."""
    return np.array([float(tourist.get(name, 0.5) if tourist.get(name) is not None else 0.5) for name in USER_FEATURES])


def season_fit(best_seasons: str, season: str | None) -> float:
    """Post-filter helper: 1.0 when the route is in season, 0.3 when it is not.

    Season is applied as a re-ranking multiplier rather than a learned feature —
    the dataset shows no relationship between a tourist's survey scores and the
    month they travel, so there is nothing for the model to learn, but a route
    that is closed in the requested month should still not be recommended.
    """
    if not season:
        return 1.0
    tokens = SEASON_TOKENS.get(str(season).title(), [season])
    text = str(best_seasons or "")
    return 1.0 if any(token in text for token in tokens) else 0.3


def build_training_pairs(
    profile: pd.DataFrame,
    tourists: pd.DataFrame,
    train_interactions: pd.DataFrame,
    *,
    n_negatives: int = 8,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Pointwise training data: each observed positive against `n_negatives` sampled routes.

    Pointwise + negative sampling is the simplest formulation that still learns a
    ranking, and it keeps the model a plain logistic regression whose
    coefficients can be read directly in the thesis.
    """
    rng = np.random.default_rng(seed)
    items = item_matrix(profile)
    popularity = profile["popularity"].to_numpy(dtype=float)
    index_of = {route_id: i for i, route_id in enumerate(profile["route_id"])}

    survey = tourists.set_index("tourist_id")[USER_FEATURES]
    positives = train_interactions[
        (train_interactions["item_type"] == "Route")
        & (train_interactions["interaction_type"].isin(POSITIVE_INTERACTIONS))
        & (train_interactions["tourist_id"].isin(survey.index))
    ]

    users = positives["tourist_id"].to_numpy()
    chosen = positives["item_id"].to_numpy()
    if len(users) == 0:
        return np.empty((0, len(FEATURE_NAMES))), np.empty(0)

    vectors = survey.loc[users].to_numpy(dtype=float)
    n_items = len(profile)

    blocks: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for row, (vector, route_id) in enumerate(zip(vectors, chosen)):
        if route_id not in index_of:
            continue
        sampled = rng.integers(0, n_items, n_negatives)
        indices = np.concatenate([[index_of[route_id]], sampled])
        blocks.append(pair_features(vector, items[indices], popularity[indices]))
        label = np.zeros(len(indices))
        label[0] = 1.0
        labels.append(label)

    if not blocks:
        return np.empty((0, len(FEATURE_NAMES))), np.empty(0)
    return np.vstack(blocks), np.concatenate(labels)
