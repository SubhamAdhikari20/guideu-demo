from __future__ import annotations

from datetime import date

import pytest
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
