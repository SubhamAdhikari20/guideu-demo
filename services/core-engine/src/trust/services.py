"""Anti-scam price-check service.

Resolves a fair benchmark for a (service, region, season), computes the
overcharge ratio, and asks the analytics-engine for a calibrated scam
probability. If the ML service is unavailable it degrades gracefully to the
deterministic benchmark rule, so the feature always works.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from src.catalog.models import PricingBenchmark
from src.common.services import get_analytics_client

from .models import classify_severity


@dataclass
class PriceCheckResult:
    service_type: str
    region: str | None
    season: str | None
    quoted_price_npr: int
    benchmark_price_npr: int | None
    overcharge_ratio: float | None
    is_likely_scam: bool
    severity: str | None
    scam_probability: float | None
    source: str  # "ml" | "benchmark" | "unknown"
    explanation: list[str]
    # Fair-wage protection — a quote can be unfairly low as well as unfairly high.
    below_fair_wage: bool = False
    below_fair_range: bool = False
    fair_wage_message: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


# Flag when the quote exceeds the fair benchmark by >25% (dataset convention).
SCAM_RATIO_THRESHOLD = 1.25

# Services whose price is somebody's labour. Under-quoting these is a fairness
# problem for the provider, not a bargain for the tourist.
LABOUR_SERVICES = {"Licensed Guide", "Porter"}
WAGE_FLOOR_TOLERANCE = 0.95


def check_price(*, service_type: str, region: str | None, season: str | None, quoted_price_npr: int) -> PriceCheckResult:
    benchmark = PricingBenchmark.fair_price_for(service_type=service_type, region_name=region, season=season)
    explanation: list[str] = []

    if benchmark is None:
        # No local sample for this service. The analytics-engine keeps its own
        # benchmark table, so ask it before giving up — otherwise an unknown
        # service silently answers "not a scam", which fails in the unsafe
        # direction for the one feature that exists to warn people.
        ml_only = get_analytics_client().score_scam(
            service_type=service_type, region=region or "", season=season or "", quoted_price_npr=quoted_price_npr
        )
        if ml_only and "scam_probability" in ml_only:
            explanation.append("No local benchmark for this service; scored by the anti-scam model.")
            ml_ratio = ml_only.get("overcharge_ratio")
            ml_severity = ml_only.get("severity") or (
                classify_severity(ml_ratio) if ml_ratio is not None
                else ("Likely Scam" if ml_only.get("is_likely_scam") else "Unknown")
            )
            return PriceCheckResult(
                service_type=service_type, region=region, season=season, quoted_price_npr=quoted_price_npr,
                benchmark_price_npr=ml_only.get("benchmark_price_npr"),
                overcharge_ratio=ml_ratio,
                is_likely_scam=bool(ml_only.get("is_likely_scam")), severity=ml_severity,
                scam_probability=ml_only.get("scam_probability"), source="ml", explanation=explanation,
                below_fair_wage=bool(ml_only.get("below_fair_wage")),
                below_fair_range=bool(ml_only.get("below_fair_range")),
                fair_wage_message=ml_only.get("fair_wage_message"),
            )
        explanation.append(
            "No fair-price benchmark exists for this service yet, so this quote could not be checked."
        )
        return PriceCheckResult(
            service_type=service_type, region=region, season=season, quoted_price_npr=quoted_price_npr,
            benchmark_price_npr=None, overcharge_ratio=None, is_likely_scam=False, severity="Unknown",
            scam_probability=None, source="unknown", explanation=explanation,
        )

    fair = benchmark["fair_price_npr"]
    floor = benchmark["min_fair_npr"]
    ratio = round(quoted_price_npr / fair, 3) if fair else None
    severity = classify_severity(ratio) if ratio is not None else None
    scope = {
        "service+region+season": f"for {benchmark['region']} in {benchmark['season']}",
        "service+region": f"for {benchmark['region']}",
    }.get(benchmark.get("granularity", ""), "across Nepal")
    explanation.append(f"Fair benchmark is ~{fair} NPR {scope} (n={benchmark['sample_size']} samples).")
    if ratio is not None:
        explanation.append(f"Quoted price is {ratio}x the fair benchmark.")

    below_range = bool(floor and quoted_price_npr < floor)
    below_wage = bool(service_type in LABOUR_SERVICES and floor and quoted_price_npr < floor * WAGE_FLOOR_TOLERANCE)
    wage_message = None
    if below_wage:
        shortfall = round((floor - quoted_price_npr) / floor * 100, 1)
        wage_message = (
            f"This is {shortfall}% below the fair rate for a {service_type.lower()}. "
            f"Paying under the fair range pushes licensed workers out of the market — "
            f"the fair rate is about {fair} NPR."
        )
        explanation.append(wage_message)
    elif below_range:
        explanation.append("Quote is below the usual fair range — check what is included.")

    # Try the ML service for a calibrated probability; fall back to the rule.
    ml = get_analytics_client().score_scam(
        service_type=service_type, region=region or "", season=season or "", quoted_price_npr=quoted_price_npr
    )
    if ml and "scam_probability" in ml:
        explanation.append("Scored by the anti-scam model.")
        # Either service raising the wage flag is enough to raise it — under-paying
        # a guide or porter is the failure we would rather over-report than miss.
        # The message itself comes from the local benchmark when we have one,
        # because that is resolved to the region while the model may have fallen
        # back to the national average. Mixing the two put two different
        # shortfall figures in the same response.
        return PriceCheckResult(
            service_type=service_type, region=region, season=season, quoted_price_npr=quoted_price_npr,
            benchmark_price_npr=fair, overcharge_ratio=ratio, is_likely_scam=bool(ml.get("is_likely_scam")),
            severity=ml.get("severity") or severity, scam_probability=ml.get("scam_probability"),
            source="ml", explanation=explanation,
            below_fair_wage=bool(ml.get("below_fair_wage")) or below_wage,
            below_fair_range=bool(ml.get("below_fair_range")) or below_range,
            fair_wage_message=wage_message or ml.get("fair_wage_message"),
        )

    return PriceCheckResult(
        service_type=service_type, region=region, season=season, quoted_price_npr=quoted_price_npr,
        benchmark_price_npr=fair, overcharge_ratio=ratio,
        is_likely_scam=bool(ratio and ratio > SCAM_RATIO_THRESHOLD), severity=severity,
        scam_probability=None, source="benchmark", explanation=explanation,
        below_fair_wage=below_wage, below_fair_range=below_range, fair_wage_message=wage_message,
    )
