"""Online route recommendation.

Scores the whole route catalog for one tourist with the trained ranker, applies
the season filter, de-duplicates by route concept, and returns the top-k with an
explanation of why each route surfaced.

Explanations come from the model itself rather than from a separate narrative:
for a linear ranker the contribution of a feature is its standardised value times
its coefficient, so the same numbers that produced the ranking are the ones shown
to the user. If no trained artifact is present the module falls back to the
adventure-match term alone, which keeps the endpoint serving during a cold start.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from data.loader import load_interactions, load_routes
from features.recommender import (
    FEATURE_NAMES,
    build_route_profile,
    item_matrix,
    pair_features,
    season_fit,
    user_vector,
)
from registry import get_card, load_model

# Human-readable names for the learned features, used in the "why" lines.
"""Fallback cap when the model card does not carry one."""
MAX_PER_TREK = 3

FEATURE_LABELS = {
    "gap_adventure": "match between route difficulty and your adventure preference",
    "gap_altitude": "match between route altitude and your adventure preference",
    "gap_cost": "match between route cost and your price sensitivity",
    "popularity": "how often other travellers engage with this route",
    "difficulty_norm": "route difficulty",
    "cost_norm": "route cost",
    "altitude_norm": "route altitude",
    "duration_norm": "trek length",
    "pref_adventure_score": "your adventure score",
    "pref_culture_score": "your culture score",
    "pref_nature_score": "your nature score",
    "risk_tolerance": "your risk tolerance",
    "price_sensitivity": "your price sensitivity",
}
TOP_REASONS = 3


@lru_cache(maxsize=1)
def _bundle() -> dict:
    """Trained artifact if available, else a profile built live from the dataset."""
    artifact = load_model("route_recommender")
    if artifact and "routes" in artifact:
        profile = pd.DataFrame(artifact["routes"])
        return {
            "profile": profile,
            "model": artifact.get("model"),
            "feature_names": artifact.get("feature_names", FEATURE_NAMES),
            "items": item_matrix(profile),
            "popularity": profile["popularity"].to_numpy(dtype=float),
        }
    try:
        interactions = load_interactions()
    except FileNotFoundError:
        interactions = None
    profile = build_route_profile(load_routes(), interactions)
    return {
        "profile": profile,
        "model": None,
        "feature_names": FEATURE_NAMES,
        "items": item_matrix(profile),
        "popularity": profile["popularity"].to_numpy(dtype=float),
    }


def _contributions(model, features: np.ndarray, names: list[str]) -> np.ndarray | None:
    """Per-feature contribution matrix for a linear ranker, else None."""
    try:
        scaler = model.named_steps["scale"]
        classifier = model.named_steps["clf"]
    except (AttributeError, KeyError):
        return None
    if not hasattr(classifier, "coef_"):
        return None
    return scaler.transform(features) * classifier.coef_[0]


def _reasons(contribution_row: np.ndarray | None, names: list[str]) -> list[str]:
    if contribution_row is None:
        return ["Ranked by how well the route difficulty matches your adventure preference."]
    order = np.argsort(-contribution_row)
    lines = []
    for index in order[:TOP_REASONS]:
        if contribution_row[index] <= 0:
            break
        label = FEATURE_LABELS.get(names[index], names[index])
        lines.append(f"Driven by {label}.")
    return lines or ["Ranked by overall fit against your travel profile."]


def recommend(*, tourist: dict, season: str | None = None, top_k: int = 5) -> dict:
    bundle = _bundle()
    profile = bundle["profile"]
    model = bundle["model"]
    names = list(bundle["feature_names"])

    vector = user_vector(tourist)
    features = pair_features(vector, bundle["items"], bundle["popularity"])

    if model is not None:
        scores = model.predict_proba(features)[:, 1]
        model_version = (get_card("route_recommender").version if get_card("route_recommender") else "route_recommender")
    else:
        # Cold start: the single signal the data supports.
        scores = 1.0 - np.abs(bundle["items"][:, 0] - vector[0])
        model_version = "content-fallback"

    # Season is a re-ranking multiplier, not a learned feature — a route that is
    # closed in the requested month should not be recommended for it.
    season_multiplier = profile["best_seasons"].map(lambda s: season_fit(s, season)).to_numpy(dtype=float)
    scores = scores * season_multiplier

    contributions = _contributions(model, features, names) if model is not None else None

    # Diversity constraint, matching the configuration the model card reports:
    # one row per variant, and at most MAX_PER_TREK variants of the same trek, so
    # a shortlist is not four packagings of one trail.
    card = get_card("route_recommender")
    max_per_trek = int((card.params.get("max_per_trek") if card else None) or MAX_PER_TREK)

    order = np.argsort(-scores)
    seen: set[str] = set()
    trek_counts: dict[str, int] = {}
    concept_col = profile.columns.get_loc("concept")
    has_trek = "trek" in profile.columns
    trek_col = profile.columns.get_loc("trek") if has_trek else None

    items: list[dict] = []
    for index in order:
        concept = profile.iat[index, concept_col]
        if concept in seen:
            continue
        if has_trek:
            trek = profile.iat[index, trek_col]
            if trek_counts.get(trek, 0) >= max_per_trek:
                continue
            trek_counts[trek] = trek_counts.get(trek, 0) + 1
        seen.add(concept)
        row = profile.iloc[index]
        items.append(
            {
                "route_id": row["route_id"],
                "route_name": row["route_name"],
                "region": row["region"],
                "difficulty": row["difficulty"],
                "score": round(float(scores[index]), 4),
                "components": {
                    "adventure_match": round(float(1.0 - abs(row["difficulty_norm"] - vector[0])), 4),
                    "season_fit": round(float(season_multiplier[index]), 4),
                    "popularity": round(float(row["popularity"]), 4),
                    "cost_match": round(float(1.0 - abs(row["cost_norm"] - (1.0 - vector[4]))), 4),
                },
                "why": _reasons(contributions[index] if contributions is not None else None, names),
            }
        )
        if len(items) >= top_k:
            break

    return {"model_version": model_version, "items": items}


def clear_cache() -> None:
    _bundle.cache_clear()
