"""Fair-price benchmarking, served from the dataset.

Builds cached aggregations at three granularities and falls back progressively:
(service, region, season) -> (service, region) -> (service). This is both a
standalone endpoint and the benchmark source for the scam scorer.

It also implements the **below-fair-wage protection**. Price transparency has an
asymmetric failure mode: publishing a fair range helps a tourist spot an
overcharge, but it equally helps them anchor every negotiation at the bottom of
that range, and for the labour services in this market — guides and porters —
the bottom of the range is somebody's daily wage. The platform therefore flags
under-quoting as loudly as over-quoting, and refuses to present an
under-fair-wage quote as a good deal.
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from data.loader import load_pricing

# Services where the price is a person's labour rather than a good or a fee.
# Under-quoting these is a fairness problem, not a bargain.
LABOUR_SERVICES = {"Licensed Guide", "Porter"}

# How far below the fair floor a quote must fall before it is called out.
WAGE_FLOOR_TOLERANCE = 0.95


@lru_cache(maxsize=1)
def _lookups() -> dict[str, pd.DataFrame]:
    pricing = load_pricing()
    aggregation = {"fair_price_npr": "mean", "min_fair_npr": "mean", "max_fair_npr": "mean", "benchmark_id": "size"}
    return {
        "srs": pricing.groupby(["service_type", "region", "season"]).agg(aggregation),
        "sr": pricing.groupby(["service_type", "region"]).agg(aggregation),
        "s": pricing.groupby(["service_type"]).agg(aggregation),
    }


def _row_to_dict(row, *, service_type, region, season, granularity) -> dict:
    return {
        "service_type": service_type,
        "region": region,
        "season": season,
        "fair_price_npr": int(round(row["fair_price_npr"])),
        "min_fair_npr": int(round(row["min_fair_npr"])),
        "max_fair_npr": int(round(row["max_fair_npr"])),
        "currency": "NPR",
        "granularity": granularity,
        "sample_basis": int(row["benchmark_id"]),
        "is_labour_service": service_type in LABOUR_SERVICES,
    }


def fair_price(service_type: str, region: str | None = None, season: str | None = None) -> dict | None:
    lookups = _lookups()
    if region and season:
        try:
            row = lookups["srs"].loc[(service_type, region, season)]
            return _row_to_dict(row, service_type=service_type, region=region, season=season,
                                granularity="service+region+season")
        except KeyError:
            pass
    if region:
        try:
            row = lookups["sr"].loc[(service_type, region)]
            return _row_to_dict(row, service_type=service_type, region=region, season=season,
                                granularity="service+region")
        except KeyError:
            pass
    try:
        row = lookups["s"].loc[service_type]
        return _row_to_dict(row, service_type=service_type, region=region, season=season, granularity="service")
    except KeyError:
        return None


def wage_check(benchmark: dict | None, quoted_price_npr: float) -> dict:
    """Is this quote unfairly *low* for the provider?

    Returns a verdict for every service so the caller can render one consistent
    price bar, but only labour services raise the fair-wage concern.
    """
    if not benchmark:
        return {"below_fair_range": False, "below_fair_wage": False, "shortfall_pct": None, "message": None}

    floor = benchmark["min_fair_npr"]
    below_range = quoted_price_npr < floor
    shortfall = round((floor - quoted_price_npr) / floor * 100, 1) if floor and below_range else None
    below_wage = bool(
        benchmark["is_labour_service"] and floor and quoted_price_npr < floor * WAGE_FLOOR_TOLERANCE
    )

    if below_wage:
        message = (
            f"This is {shortfall}% below the fair rate for a {benchmark['service_type'].lower()}. "
            "Paying under the fair range pushes licensed workers out of the market — please consider the "
            f"fair rate of {benchmark['fair_price_npr']} NPR."
        )
    elif below_range:
        message = f"Quote is {shortfall}% below the usual fair range — check what is included."
    else:
        message = None

    return {
        "below_fair_range": below_range,
        "below_fair_wage": below_wage,
        "shortfall_pct": shortfall,
        "message": message,
    }
