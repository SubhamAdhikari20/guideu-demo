"""Train + validate the tourist segmentation used for cold-start recommendations.

K-means over the five survey scores. The script does two things that a segment
model in a student project usually skips:

* it reports the silhouette score for every k it considered, which shows the
  clusters are *not* geometrically well separated (~0.13 everywhere); and
* it validates the partition **extrinsically**, by testing whether segment
  membership actually predicts the difficulty of the routes those tourists went
  on to book. A one-way ANOVA answers that, and the effect size is reported
  alongside the p-value so a significant-but-tiny result cannot be dressed up.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data.loader import load_interactions, load_routes, load_tourists
from features.recommender import POSITIVE_INTERACTIONS
from features.segments import SEGMENT_FEATURES, build_segment_matrix, describe_segments
from registry import save_model

logger = logging.getLogger("guideu.ml.train.segments")

SEED = 42
K_RANGE = range(2, 9)
N_CLUSTERS = 4
SILHOUETTE_SAMPLE = 8000


def _silhouette_sweep(X: np.ndarray) -> dict[str, float]:
    rng = np.random.default_rng(0)
    sample = rng.choice(len(X), min(SILHOUETTE_SAMPLE, len(X)), replace=False)
    scores = {}
    for k in K_RANGE:
        labels = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(X)
        scores[f"k={k}"] = round(float(silhouette_score(X[sample], labels[sample])), 4)
    return scores


def _behavioural_validation(tourists: pd.DataFrame) -> dict:
    """Do the segments differ in what their members actually book?"""
    routes = load_routes()[["route_id", "difficulty_level", "estimated_cost_usd", "max_altitude_m"]]
    interactions = load_interactions()
    positives = interactions[
        (interactions["item_type"] == "Route") & (interactions["interaction_type"].isin(POSITIVE_INTERACTIONS))
    ]
    joined = positives.merge(tourists[["tourist_id", "segment"]], on="tourist_id", how="inner").merge(
        routes, left_on="item_id", right_on="route_id", how="inner"
    )
    if joined.empty:
        return {"available": False}

    profile = (
        joined.groupby("segment")
        .agg(
            n_bookings=("route_id", "size"),
            mean_difficulty=("difficulty_level", "mean"),
            mean_cost_usd=("estimated_cost_usd", "mean"),
            mean_altitude_m=("max_altitude_m", "mean"),
        )
        .round(3)
    )

    groups = [chunk["difficulty_level"].to_numpy() for _, chunk in joined.groupby("segment")]
    f_stat, p_value = stats.f_oneway(*groups) if len(groups) > 1 else (float("nan"), float("nan"))
    spread = float(profile["mean_difficulty"].max() - profile["mean_difficulty"].min())
    pooled_sd = float(joined["difficulty_level"].std())

    return {
        "available": True,
        "profile": profile.reset_index().to_dict("records"),
        "anova_f": round(float(f_stat), 3),
        "anova_p": float(p_value),
        "difficulty_spread": round(spread, 3),
        "pooled_sd": round(pooled_sd, 3),
        # Spread between the extreme segment means in standard deviations.
        "effect_size_cohens_d": round(spread / pooled_sd, 3) if pooled_sd else 0.0,
    }


def train() -> dict:
    tourists = load_tourists()
    frame = build_segment_matrix(tourists)

    scaler = StandardScaler().fit(frame)
    X = scaler.transform(frame)
    silhouettes = _silhouette_sweep(X)

    model = Pipeline(
        [("scale", StandardScaler()), ("kmeans", KMeans(n_clusters=N_CLUSTERS, n_init=10, random_state=SEED))]
    )
    labels = model.fit_predict(frame)
    tourists = tourists.assign(segment=labels)

    kmeans = model.named_steps["kmeans"]
    centroids = model.named_steps["scale"].inverse_transform(kmeans.cluster_centers_)
    population_mean = frame.mean().round(4).to_dict()
    segments = describe_segments(centroids, labels, population_mean)

    validation = _behavioural_validation(tourists)
    chosen_silhouette = silhouettes[f"k={N_CLUSTERS}"]

    metrics = {
        "silhouette": chosen_silhouette,
        "inertia": round(float(kmeans.inertia_), 2),
        "n_clusters": float(N_CLUSTERS),
        "n_tourists": float(len(tourists)),
    }
    if validation["available"]:
        metrics["behaviour_anova_f"] = validation["anova_f"]
        metrics["behaviour_effect_size"] = validation["effect_size_cohens_d"]

    notes = (
        f"K-means (k={N_CLUSTERS}) over the five survey scores, used to give cold-start users a starting "
        f"profile. Silhouette is {chosen_silhouette} and stays near 0.13 for every k in {list(K_RANGE)}, so "
        "these are an operational partition of a diffuse preference cloud, not naturally separated personas. "
    )
    if validation["available"]:
        notes += (
            f"Extrinsic check: booked-route difficulty differs by segment (ANOVA F={validation['anova_f']}, "
            f"p={validation['anova_p']:.2e}) but the spread between extreme segments is only "
            f"{validation['effect_size_cohens_d']} SD — statistically clear, practically small."
        )

    artifact = {
        "model": model,
        "features": SEGMENT_FEATURES,
        "segments": segments,
        "population_mean": population_mean,
    }
    card = save_model(
        name="tourist_segments",
        model=artifact,
        metrics=metrics,
        params={"algorithm": "KMeans", "n_clusters": N_CLUSTERS, "features": SEGMENT_FEATURES},
        n_train=len(tourists),
        notes=notes,
    )
    logger.info("segments trained: %s", metrics)
    return {
        "card": card.version,
        "metrics": metrics,
        "silhouette_sweep": silhouettes,
        "segments": segments,
        "behavioural_validation": validation,
    }


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    import json

    result = train()
    print(json.dumps({k: v for k, v in result.items() if k != "card"}, indent=2, default=str))
