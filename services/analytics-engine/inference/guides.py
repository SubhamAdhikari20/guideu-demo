"""Verified-guide ranking.

Ranks a shortlist of candidate guides for one tourist by the rating the trained
match-quality model predicts that tourist would give each guide.

Two things are deliberately kept outside the model:

* **Hard requirements.** A guide who does not cover the requested region, or does
  not speak the requested language, is filtered down rather than scored — the
  dataset gives the model no way to learn that preference, and it is a
  constraint, not a taste.
* **Verification status.** Ranking an expired licence above a current one would
  undercut the whole point of the platform, so verified guides are ordered ahead
  of unverified ones regardless of predicted rating.

When no trained artifact is present the module falls back to the original
transparent weighted score, so the endpoint keeps working.
"""
from __future__ import annotations

import numpy as np

from features.guides import build_inference_frame, coverage_bonus
from registry import get_card, load_model

# Fallback weights — used only when no trained model is available.
CERT_WEIGHT = {
    "IFMGA Mountain Guide": 1.0,
    "NATHM Trekking Guide": 0.8,
    "Government Trekking Guide": 0.75,
    "Adventure Sports Guide": 0.75,
    "Cultural Specialist": 0.7,
    "NATHM Tour Guide": 0.65,
    "Bird-watching Specialist": 0.6,
    "City Guide (Licensed)": 0.55,
}
FALLBACK_WEIGHTS = {"certification": 0.35, "rating": 0.3, "region": 0.2, "language": 0.15}

# Multipliers applied after scoring. Not learned — see the module docstring.
UNVERIFIED_PENALTY = {"Verified": 1.0, "Pending Renewal": 0.9, "Expired": 0.6}
MISSING_REQUIREMENT_PENALTY = 0.5


def _fallback_score(guide: dict, wanted_region: str | None, wanted_language: str | None) -> tuple[float, dict]:
    components = {
        "certification": round(CERT_WEIGHT.get(guide.get("certification", ""), 0.5), 4),
        "rating": round(min(float(guide.get("average_rating") or 0) / 5.0, 1.0), 4),
        "region": round(coverage_bonus(guide.get("regions_covered"), wanted_region), 4),
        "language": round(coverage_bonus(guide.get("languages_spoken"), wanted_language), 4),
    }
    score = sum(FALLBACK_WEIGHTS[key] * components[key] for key in FALLBACK_WEIGHTS)
    return score, components


def rank(*, tourist: dict, candidates: list[dict]) -> dict:
    if not candidates:
        return {"model_version": "guide-rank-empty", "items": []}

    wanted_region = tourist.get("region")
    wanted_language = tourist.get("language")

    model = load_model("guide_ranker")
    ranked: list[dict] = []

    if model is not None:
        frame = build_inference_frame(tourist, candidates)
        predicted = np.clip(model.predict(frame), 1.0, 5.0)
        card = get_card("guide_ranker")
        model_version = card.version if card else "guide_ranker"

        for guide, predicted_rating in zip(candidates, predicted):
            region_match = coverage_bonus(guide.get("regions_covered"), wanted_region)
            language_match = coverage_bonus(guide.get("languages_spoken"), wanted_language)
            verification = UNVERIFIED_PENALTY.get(guide.get("verification_status", "Verified"), 1.0)

            # Predicted rating is on the 1-5 scale; normalise before applying the filters.
            base = float(predicted_rating) / 5.0
            requirement = 1.0 if (region_match and language_match) else MISSING_REQUIREMENT_PENALTY
            score = base * requirement * verification

            ranked.append(
                {
                    **guide,
                    "score": round(score, 4),
                    "predicted_rating": round(float(predicted_rating), 3),
                    "components": {
                        "predicted_match_rating": round(float(predicted_rating), 4),
                        "region_match": round(region_match, 4),
                        "language_match": round(language_match, 4),
                        "verification": round(verification, 4),
                    },
                }
            )
    else:
        model_version = "guide-rank-fallback"
        for guide in candidates:
            score, components = _fallback_score(guide, wanted_region, wanted_language)
            ranked.append({**guide, "score": round(score, 4), "components": components})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {"model_version": model_version, "items": ranked}
