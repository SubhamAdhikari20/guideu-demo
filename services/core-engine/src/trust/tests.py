"""Tests for the anti-scam price check and the fair-wage protection.

The fair-wage rule is the project's answer to a specific ethical risk: price
transparency helps a tourist spot an overcharge, but it equally helps them
anchor every negotiation at the bottom of the published range, and for guides
and porters that floor is a daily wage. These tests pin the behaviour down so it
cannot be quietly regressed.

The analytics-engine is not running during tests, so ``check_price`` falls back
to its own benchmark rule — which is exactly the path that must stay correct
when the ML service is unavailable.
"""
from __future__ import annotations

import pytest

from src.catalog.models import PricingBenchmark, Region
from src.trust.services import check_price


@pytest.fixture
def benchmarked_region(db):
    region = Region.objects.create(name="Langtang", slug="langtang")
    PricingBenchmark.objects.create(
        external_id="PRC000001",
        service_type="Porter",
        region=region,
        season="Peak (Autumn)",
        fair_price_npr=3000,
        min_fair_npr=2400,
        max_fair_npr=3600,
        unit="per day",
    )
    PricingBenchmark.objects.create(
        external_id="PRC000002",
        service_type="TIMS Permit",
        region=region,
        season="Peak (Autumn)",
        fair_price_npr=2000,
        min_fair_npr=1600,
        max_fair_npr=2400,
        unit="per permit",
    )
    return region


@pytest.mark.django_db
def test_overcharge_is_flagged(benchmarked_region):
    result = check_price(
        service_type="Porter", region="Langtang", season="Peak (Autumn)", quoted_price_npr=9000
    )
    assert result.is_likely_scam is True
    assert result.overcharge_ratio == 3.0
    assert result.below_fair_wage is False


@pytest.mark.django_db
def test_fair_quote_is_not_flagged(benchmarked_region):
    result = check_price(
        service_type="Porter", region="Langtang", season="Peak (Autumn)", quoted_price_npr=3000
    )
    assert result.is_likely_scam is False
    assert result.below_fair_wage is False
    assert result.below_fair_range is False


@pytest.mark.django_db
def test_underpaying_a_porter_raises_the_fair_wage_flag(benchmarked_region):
    """Half the fair floor for a labour service must be called out, not celebrated."""
    result = check_price(
        service_type="Porter", region="Langtang", season="Peak (Autumn)", quoted_price_npr=1200
    )
    assert result.below_fair_range is True
    assert result.below_fair_wage is True
    assert result.fair_wage_message is not None
    assert "fair rate" in result.fair_wage_message


@pytest.mark.django_db
def test_cheap_permit_is_not_a_wage_problem(benchmarked_region):
    """A permit is a fee, not somebody's labour — no fair-wage flag."""
    result = check_price(
        service_type="TIMS Permit", region="Langtang", season="Peak (Autumn)", quoted_price_npr=800
    )
    assert result.below_fair_range is True
    assert result.below_fair_wage is False


@pytest.mark.django_db
def test_unknown_service_degrades_gracefully(benchmarked_region):
    result = check_price(
        service_type="Hot Air Balloon", region="Langtang", season="Peak (Autumn)", quoted_price_npr=5000
    )
    assert result.source == "unknown"
    assert result.is_likely_scam is False
    assert result.benchmark_price_npr is None
