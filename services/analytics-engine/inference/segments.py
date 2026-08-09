"""Online tourist segmentation, used for cold start.

A tourist who has just signed up has no interaction history. Assigning them to
the nearest segment gives the recommender a starting profile that is better than
the population average, and gives the app a short phrase to show back to the user
("looks like you're a nature-loving, safety-first traveller — is that right?"),
which doubles as a way to correct a bad guess early.

The segments are an operational partition, not discovered personality types —
see ``features/segments.py`` for why that distinction is made explicitly.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from features.segments import SEGMENT_FEATURES
from registry import get_card, load_model


@lru_cache(maxsize=1)
def _artifact() -> dict | None:
    return load_model("tourist_segments")


def assign(tourist: dict) -> dict:
    """Nearest segment for a (possibly partial) tourist profile."""
    artifact = _artifact()
    if not artifact:
        return {"model_version": "untrained", "segment_id": None, "name": None, "centroid": {}, "segments": []}

    row = {name: float(tourist.get(name) if tourist.get(name) is not None else 0.5) for name in SEGMENT_FEATURES}
    frame = pd.DataFrame([row], columns=SEGMENT_FEATURES)
    segment_id = int(artifact["model"].predict(frame)[0])

    segments = artifact.get("segments", [])
    match = next((s for s in segments if s["segment_id"] == segment_id), None)
    card = get_card("tourist_segments")

    return {
        "model_version": card.version if card else "tourist_segments",
        "segment_id": segment_id,
        "name": match["name"] if match else None,
        "size": match["size"] if match else None,
        "centroid": match["centroid"] if match else {},
        "segments": [{"segment_id": s["segment_id"], "name": s["name"], "size": s["size"]} for s in segments],
    }


def cold_start_profile(tourist: dict | None = None) -> dict:
    """Segment centroid to seed the recommender when the user has no history."""
    assignment = assign(tourist or {})
    centroid = assignment.get("centroid") or {}
    return {name: centroid.get(name, 0.5) for name in SEGMENT_FEATURES}


def clear_cache() -> None:
    _artifact.cache_clear()
