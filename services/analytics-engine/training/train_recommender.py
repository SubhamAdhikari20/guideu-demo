"""Train + evaluate the learned route recommender.

Replaces the original hand-weighted content score. The model is a logistic
regression over (tourist, route) pair features, trained pointwise with negative
sampling on 2021-2023 interactions and evaluated on 2024 positive feedback.

Three baselines are scored through the identical harness so the thesis can quote
a like-for-like lift: random, popularity-only, and the previous hand-weighted
heuristic. Metrics are reported at two granularities:

* **route level** — did we surface the exact ``route_id`` the tourist chose?
* **concept level** — did we surface the right *trek*? The catalog stores each
  trek ~5-6 times under one name, so route-level precision has a low structural
  ceiling that says more about the data generator than about the model.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data.loader import load_interactions, load_routes, load_tourists
from evaluation.metrics import mean_metrics, ranking_metrics
from features.recommender import (
    FEATURE_NAMES,
    POSITIVE_INTERACTIONS,
    PROFILE_COLS,
    USER_FEATURES,
    build_route_profile,
    build_training_pairs,
    item_matrix,
    pair_features,
)
from registry import save_model

logger = logging.getLogger("guideu.ml.train.recommender")

TOP_K = 10
MAX_EVAL_USERS = 3000
N_NEGATIVES = 8
SEED = 42

# At most this many variants of the same base trek in one shortlist. Picked from
# the diversity sweep this script prints: a cap of 3 guarantees at least four
# distinct treks in a top-10 and keeps a 1.38x lift over popularity, where a cap
# of 1 would force maximum variety but drop the model back to baseline accuracy.
MAX_PER_TREK = 3

# The weights the sprint-1 heuristic used, kept only to score it as a baseline.
LEGACY_WEIGHTS = {"adventure_fit": 0.45, "season_fit": 0.2, "budget_fit": 0.2, "popularity": 0.15}
LEGACY_BUDGET_USD = {"Budget": 800, "Mid-range": 1500, "Comfort": 2500, "Luxury": 4000}


def _diversify(
    order: np.ndarray,
    concepts: np.ndarray,
    treks: np.ndarray | None,
    k: int,
    max_per_trek: int,
) -> np.ndarray:
    """Take the top-k, one row per variant and at most ``max_per_trek`` per base trek.

    Collapsing all the way down to one row per trek is tempting but costs a lot
    of accuracy (see the comparison table in ``train``), because it throws away
    the model's ability to pick *which* packaging of a trek fits the traveller.
    A cap keeps the shortlist varied without that collapse.
    """
    seen_concepts: set[str] = set()
    trek_counts: dict[str, int] = {}
    kept: list[int] = []
    for index in order:
        concept = concepts[index]
        if concept in seen_concepts:
            continue
        if treks is not None:
            trek = treks[index]
            if trek_counts.get(trek, 0) >= max_per_trek:
                continue
            trek_counts[trek] = trek_counts.get(trek, 0) + 1
        seen_concepts.add(concept)
        kept.append(index)
        if len(kept) >= k:
            break
    return np.asarray(kept, dtype=int)


def _evaluate_ranker(
    score_fn,
    *,
    eval_users: list[str],
    relevant: pd.Series,
    route_ids: np.ndarray,
    concepts: np.ndarray,
    concept_of: dict[str, str],
    treks: np.ndarray | None = None,
    max_per_trek: int = 0,
    dedupe: bool = False,
) -> dict[str, float]:
    """Score one ranking strategy over every evaluation user.

    Metrics are always reported at route and variant-concept granularity
    whatever the diversity settings, so the strategies stay comparable.
    """
    route_rows: list[dict[str, float]] = []
    concept_rows: list[dict[str, float]] = []

    for tourist_id in eval_users:
        scores = score_fn(tourist_id)
        order = np.argsort(-scores)
        if dedupe:
            order = _diversify(order, concepts, treks, TOP_K, max_per_trek or len(order))
        else:
            order = order[:TOP_K]

        ranked_routes = list(route_ids[order])
        truth = relevant[tourist_id]
        route_rows.append(ranking_metrics(ranked_routes, truth, TOP_K))

        ranked_concepts = [concept_of[r] for r in ranked_routes]
        truth_concepts = {concept_of[r] for r in truth if r in concept_of}
        concept_rows.append(ranking_metrics(ranked_concepts, truth_concepts, TOP_K))

    metrics = mean_metrics(route_rows)
    metrics.update({f"concept_{k}": v for k, v in mean_metrics(concept_rows).items()})
    return metrics


def _legacy_scores(profile: pd.DataFrame, tourists: pd.DataFrame) -> dict:
    """Pre-computed pieces of the old hand-weighted heuristic (baseline only)."""
    cost = profile["estimated_cost_usd"].to_numpy(dtype=float)
    return {
        "difficulty_norm": profile["difficulty_norm"].to_numpy(dtype=float),
        "popularity": profile["popularity"].to_numpy(dtype=float),
        "budget_vectors": {band: np.exp(-np.abs(cost - target) / target) for band, target in LEGACY_BUDGET_USD.items()},
        "budget_band": tourists.set_index("tourist_id")["budget_band"],
    }


def train() -> dict:
    routes = load_routes()
    tourists = load_tourists()
    interactions = load_interactions()
    interactions = interactions.assign(year=pd.to_datetime(interactions["interaction_date"]).dt.year)

    train_inter = interactions[interactions["year"] <= 2023]
    test_inter = interactions[interactions["year"] == 2024]

    # Popularity comes from the train period only — otherwise the 2024 labels leak in.
    profile = build_route_profile(routes, train_inter)
    X, y = build_training_pairs(profile, tourists, train_inter, n_negatives=N_NEGATIVES, seed=SEED)
    if len(X) == 0:
        raise RuntimeError("No training pairs built — check the interaction log and tourist table.")

    model = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))])
    model.fit(X, y)

    coefficients = dict(zip(FEATURE_NAMES, model.named_steps["clf"].coef_[0].round(4).tolist()))
    logger.info("recommender coefficients: %s", coefficients)

    # ---------------- offline evaluation ----------------
    route_ids = profile["route_id"].to_numpy()
    concepts = profile["concept"].to_numpy()
    concept_of = dict(zip(route_ids, concepts))
    items = item_matrix(profile)
    popularity = profile["popularity"].to_numpy(dtype=float)

    positives = test_inter[
        (test_inter["item_type"] == "Route") & (test_inter["interaction_type"].isin(POSITIVE_INTERACTIONS))
    ]
    relevant = positives.groupby("tourist_id")["item_id"].agg(set)
    survey = tourists.set_index("tourist_id")[USER_FEATURES]
    eval_users = [u for u in relevant.index if u in survey.index][:MAX_EVAL_USERS]
    if not eval_users:
        raise RuntimeError("No evaluation users with 2024 positive feedback.")

    vectors = {u: survey.loc[u].to_numpy(dtype=float) for u in eval_users}
    legacy = _legacy_scores(profile, tourists)
    rng = np.random.default_rng(SEED)
    random_scores = rng.random(len(profile))

    def learned(tourist_id: str) -> np.ndarray:
        features = pair_features(vectors[tourist_id], items, popularity)
        return model.predict_proba(features)[:, 1]

    def legacy_heuristic(tourist_id: str) -> np.ndarray:
        adventure = vectors[tourist_id][0]
        band = legacy["budget_band"].get(tourist_id)
        budget = legacy["budget_vectors"].get(band, np.full(len(profile), 0.7))
        return (
            LEGACY_WEIGHTS["adventure_fit"] * (1.0 - np.abs(legacy["difficulty_norm"] - adventure))
            + LEGACY_WEIGHTS["season_fit"] * 1.0
            + LEGACY_WEIGHTS["budget_fit"] * budget
            + LEGACY_WEIGHTS["popularity"] * legacy["popularity"]
        )

    treks = profile["trek"].to_numpy()
    shared = {
        "eval_users": eval_users,
        "relevant": relevant,
        "route_ids": route_ids,
        "concepts": concepts,
        "concept_of": concept_of,
    }
    comparison = {
        "random": _evaluate_ranker(lambda _u: random_scores, **shared),
        "popularity": _evaluate_ranker(lambda _u: popularity, **shared),
        "content_heuristic_legacy": _evaluate_ranker(legacy_heuristic, **shared),
        "learned_ranker": _evaluate_ranker(learned, **shared),
        "learned_ranker_variant_deduped": _evaluate_ranker(learned, **shared, dedupe=True),
    }
    # Diversity sweep: how much accuracy does a per-trek cap cost?
    for cap in (1, 2, 3):
        comparison[f"learned_ranker_max_{cap}_per_trek"] = _evaluate_ranker(
            learned, **shared, treks=treks, max_per_trek=cap, dedupe=True
        )

    chosen = comparison[f"learned_ranker_max_{MAX_PER_TREK}_per_trek"]
    baseline = comparison["popularity"]
    unconstrained = comparison["learned_ranker"]

    metrics = dict(chosen)
    metrics["lift_hit_rate_over_popularity"] = round(
        chosen[f"hit_rate_at_{TOP_K}"] / max(baseline[f"hit_rate_at_{TOP_K}"], 1e-9), 3
    )
    metrics["lift_concept_hit_rate_over_popularity"] = round(
        chosen[f"concept_hit_rate_at_{TOP_K}"] / max(baseline[f"concept_hit_rate_at_{TOP_K}"], 1e-9), 3
    )
    # Ranking quality of the model itself, before the diversity constraint. This
    # is the number that answers "does personalisation beat popularity?"; the
    # metric above is what the deployed, diversity-capped endpoint achieves.
    metrics["model_only_lift_over_popularity"] = round(
        unconstrained[f"hit_rate_at_{TOP_K}"] / max(baseline[f"hit_rate_at_{TOP_K}"], 1e-9), 3
    )
    metrics["n_eval_users"] = float(len(eval_users))

    artifact = {
        "model": model,
        "routes": profile[PROFILE_COLS].to_dict("records"),
        "feature_names": FEATURE_NAMES,
        "coefficients": coefficients,
        "top_k_default": TOP_K,
    }
    notes = (
        "Learned pointwise ranker (logistic regression) over tourist x route pair features, "
        f"{N_NEGATIVES} sampled negatives per positive. Trained on interactions <=2023, evaluated on "
        f"2024 positive feedback over {len(eval_users)} users. As a ranker it beats the popularity "
        f"baseline by {metrics['model_only_lift_over_popularity']}x on hit-rate@10. The served list also "
        f"caps variants of the same base trek at {MAX_PER_TREK} (the catalog hides 26 real treks behind "
        "375 variant names and 2,000 rows), which trades some accuracy for a shortlist that is not four "
        f"packagings of one trail: {metrics['lift_hit_rate_over_popularity']}x as deployed."
    )
    card = save_model(
        name="route_recommender",
        model=artifact,
        metrics=metrics,
        params={
            "algorithm": "LogisticRegression (pointwise ranker)",
            "n_negatives": N_NEGATIVES,
            "features": FEATURE_NAMES,
            "coefficients": coefficients,
            "max_per_trek": MAX_PER_TREK,
        },
        n_train=int(len(X)),
        notes=notes,
    )
    logger.info("recommender trained: %s", metrics)
    return {"card": card.version, "metrics": metrics, "comparison": comparison, "coefficients": coefficients}


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    import json

    result = train()
    print(json.dumps({"metrics": result["metrics"], "comparison": result["comparison"]}, indent=2))
