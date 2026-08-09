"""Online anti-scam scoring.

Serves the trained classifier when present, otherwise a calibrated benchmark
heuristic, so the endpoint always returns an explainable verdict. Every response
carries the benchmark, the ratio and the reasoning behind the score — a flag that
cannot be explained is not usable by a moderator and is not fair to the provider
it accuses.

The scorer is deliberately two-sided: it reports over-quoting *and* the
below-fair-wage case from ``inference.pricing``, so the same endpoint that
protects the tourist also protects the guide.
"""
from __future__ import annotations

import math

from features.scam import build_inference_row, normalise_season
from inference import pricing
from registry import get_card, load_model

SCAM_RATIO_THRESHOLD = 1.25
DEFAULT_THRESHOLD = 0.5


def classify_severity(ratio: float) -> str:
    if ratio < 1.10:
        return "Fair"
    if ratio < 1.30:
        return "Mild Overcharge"
    if ratio < 1.70:
        return "Moderate Overcharge"
    if ratio < 2.50:
        return "Severe Overcharge"
    return "Likely Scam"


def _heuristic_probability(ratio: float) -> float:
    """Smooth logistic around the 1.25 flag threshold (fallback when untrained)."""
    return round(1.0 / (1.0 + math.exp(-6.0 * (ratio - SCAM_RATIO_THRESHOLD))), 4)


def score(*, service_type: str, region: str | None, season: str | None, quoted_price_npr: float) -> dict:
    benchmark = pricing.fair_price(service_type, region or None, season or None)
    explanation: list[str] = []

    ratio = None
    if benchmark:
        fair = benchmark["fair_price_npr"]
        ratio = round(quoted_price_npr / fair, 3) if fair else None
        explanation.append(f"Fair benchmark ~{fair} NPR ({benchmark['granularity']}).")
        if ratio is not None:
            explanation.append(f"Quote is {ratio}x the benchmark.")
    else:
        explanation.append("No benchmark available for this service.")

    model = load_model("scam_classifier")
    card = get_card("scam_classifier")
    threshold = float(card.params.get("decision_threshold", DEFAULT_THRESHOLD)) if card else DEFAULT_THRESHOLD

    if model is not None:
        row = build_inference_row(
            service_type=service_type,
            region=region or "",
            quoted_price_npr=quoted_price_npr,
            season=normalise_season(season),
        )
        probability = float(model.predict_proba(row)[0, 1])
        model_version = card.version if card else "scam_classifier"
        explanation.append(
            f"Scored by the trained anti-scam classifier (flag threshold {threshold}); "
            "the model sees only the service, region, season and quoted price."
        )
    elif ratio is not None:
        probability = _heuristic_probability(ratio)
        model_version = "heuristic-benchmark"
        threshold = DEFAULT_THRESHOLD
        explanation.append("Scored by the benchmark heuristic (model not trained yet).")
    else:
        probability = 0.0
        model_version = "unknown"

    wage = pricing.wage_check(benchmark, quoted_price_npr)
    if wage["message"]:
        explanation.append(wage["message"])

    severity = classify_severity(ratio) if ratio is not None else None
    is_likely_scam = probability >= threshold or bool(ratio and ratio > SCAM_RATIO_THRESHOLD)

    return {
        "scam_probability": round(probability, 4),
        "is_likely_scam": is_likely_scam,
        "severity": severity,
        "benchmark_price_npr": benchmark["fair_price_npr"] if benchmark else None,
        "min_fair_npr": benchmark["min_fair_npr"] if benchmark else None,
        "max_fair_npr": benchmark["max_fair_npr"] if benchmark else None,
        "overcharge_ratio": ratio,
        "below_fair_wage": wage["below_fair_wage"],
        "below_fair_range": wage["below_fair_range"],
        "fair_wage_message": wage["message"],
        "model_version": model_version,
        "explanation": explanation,
    }
