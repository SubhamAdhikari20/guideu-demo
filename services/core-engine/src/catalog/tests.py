from __future__ import annotations

from datetime import date

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from src.catalog.models import CulturalEvent


@pytest.mark.django_db
def test_upcoming_groups_festivals_by_month_and_dedupes_regions():
    this_month = date.today().month
    # Same festival in two regions in the current month -> one entry, two regions.
    CulturalEvent.objects.create(
        external_id="CEV1", festival_name="Dashain", event_type="Religious",
        start_month=this_month, duration_days=15, region="Bagmati", year=2024,
        significance="High", badge_points=120,
    )
    CulturalEvent.objects.create(
        external_id="CEV2", festival_name="Dashain", event_type="Religious",
        start_month=this_month, duration_days=15, region="Gandaki", year=2024,
        significance="High", badge_points=120,
    )

    resp = APIClient().get("/api/v1/catalog/events/upcoming/?months=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["from_month"] == this_month
    festivals = body["months"][0]["festivals"]
    assert len(festivals) == 1
    assert festivals[0]["festival_name"] == "Dashain"
    assert festivals[0]["regions"] == ["Bagmati", "Gandaki"]


@pytest.mark.django_db
def test_upcoming_does_not_cache_an_empty_calendar():
    """An unseeded database must not pin the empty state into the cache.

    The calendar is cached for 30 minutes. If that cache is allowed to hold the
    "no festivals" answer, seeding the catalog appears to do nothing until it
    expires — which is precisely what happened on a freshly-started Docker
    stack whose Postgres was seeded after the page had been opened once.
    """
    this_month = date.today().month
    client = APIClient()
    # The calendar cache is process-wide and outlives a test, so start clean.
    cache.clear()

    # Hit it while empty, exactly as someone would before seeding.
    first = client.get("/api/v1/catalog/events/upcoming/?months=1")
    assert first.status_code == 200
    assert first.json()["months"][0]["festivals"] == []

    CulturalEvent.objects.create(
        external_id="CEV3", festival_name="Tihar", event_type="Religious",
        start_month=this_month, duration_days=5, region="Bagmati", year=2024,
        significance="High", badge_points=100,
    )

    # The very next request must reflect the new data, not the cached blank.
    second = client.get("/api/v1/catalog/events/upcoming/?months=1")
    festivals = second.json()["months"][0]["festivals"]
    assert [f["festival_name"] for f in festivals] == ["Tihar"]
