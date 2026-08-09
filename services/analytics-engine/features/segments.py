"""Feature engineering and naming for tourist segmentation.

Segments exist to solve cold start. A tourist who has just installed the app has
no interaction history, and the recommender needs a user vector; assigning them
to the nearest segment gives a defensible starting profile that is better than
the population average.

What the segments are *not* is discovered personality types. The silhouette
score sits around 0.13 for every k from 2 to 8, which means the preference space
is a diffuse cloud with no natural cluster boundaries — the synthetic generator
drew the five survey scores close to independently. The partition is therefore
an operational device, validated by whether segment membership predicts booking
behaviour (it does, weakly but significantly), not by geometric separation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEGMENT_FEATURES = [
    "pref_culture_score",
    "pref_adventure_score",
    "pref_nature_score",
    "risk_tolerance",
    "price_sensitivity",
]

# How a dimension is described when a centroid sits well above / below the mean.
DIMENSION_LABELS = {
    "pref_culture_score": ("Culture-focused", "Less culture-driven"),
    "pref_adventure_score": ("Adventure-seeking", "Gentle-pace"),
    "pref_nature_score": ("Nature-loving", "Urban-leaning"),
    "risk_tolerance": ("Risk-tolerant", "Safety-first"),
    "price_sensitivity": ("Budget-conscious", "Comfort-spending"),
}

DEVIATION_THRESHOLD = 0.05


def build_segment_matrix(tourists: pd.DataFrame) -> pd.DataFrame:
    """Survey columns with missing values filled at the neutral midpoint."""
    return tourists[SEGMENT_FEATURES].astype(float).fillna(0.5)


def name_segment(centroid: dict[str, float], population_mean: dict[str, float]) -> str:
    """Describe a centroid by its two strongest deviations from the population."""
    deviations = sorted(
        ((name, centroid[name] - population_mean[name]) for name in SEGMENT_FEATURES),
        key=lambda pair: -abs(pair[1]),
    )
    parts = []
    for name, delta in deviations[:2]:
        if abs(delta) < DEVIATION_THRESHOLD:
            continue
        high, low = DIMENSION_LABELS[name]
        parts.append(high if delta > 0 else low)
    return " / ".join(parts) if parts else "Balanced traveller"


def describe_segments(centroids: np.ndarray, labels: np.ndarray, population_mean: dict[str, float]) -> list[dict]:
    """Turn raw cluster centres into the persona records stored in the artifact."""
    described = []
    for index, centre in enumerate(centroids):
        centroid = {name: round(float(value), 4) for name, value in zip(SEGMENT_FEATURES, centre)}
        described.append(
            {
                "segment_id": int(index),
                "name": name_segment(centroid, population_mean),
                "size": int((labels == index).sum()),
                "centroid": centroid,
            }
        )
    return described
