from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from src.authentication.models import User
from src.catalog.models import GuideRegistry, Region, TrekkingRoute


@pytest.fixture
def tourist(db):
    return User.objects.create_user(email="t@example.com", username="t", password="pass12345")


@pytest.fixture
def client(tourist):
    api = APIClient()
    api.force_authenticate(user=tourist)
    return api


@pytest.fixture
def catalog(db):
    region = Region.objects.create(name="Khumbu", slug="khumbu")
    TrekkingRoute.objects.create(
        external_id="RTE0001", route_name="Everest Base Camp", region=region,
        difficulty="Hard", difficulty_level=4, max_altitude_m=5364, duration_days=14,
        best_seasons="Autumn", badge_points=200, estimated_cost_usd=1400,
    )
    TrekkingRoute.objects.create(
        external_id="RTE0002", route_name="Ghorepani Poon Hill", region=region,
        difficulty="Easy", difficulty_level=1, max_altitude_m=3210, duration_days=4,
        best_seasons="Spring", badge_points=80, estimated_cost_usd=400,
    )
    GuideRegistry.objects.create(
        external_id="GDE00001", guide_code="EBC-01", ntb_license_no="NTB-1",
        certification="IFMGA Mountain Guide", regions_covered="Khumbu",
        languages_spoken="English", average_rating=4.8,
    )
    GuideRegistry.objects.create(
        external_id="GDE00002", guide_code="POON-01", ntb_license_no="NTB-2",
        certification="NATHM Trekking Guide", regions_covered="Annapurna",
        languages_spoken="English,Nepali", average_rating=4.2,
    )


@pytest.mark.django_db
def test_route_feed_falls_back_to_top_routes_without_ml(client, catalog):
    """With no ML service reachable the feed still returns ranked routes."""
    resp = client.get("/api/v1/recommendations/routes/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "fallback"
    # Most rewarding route (highest badge_points) comes first.
    assert body["results"][0]["route_name"] == "Everest Base Camp"


@pytest.mark.django_db
def test_guide_feed_falls_back_to_top_rated_without_ml(client, catalog):
    resp = client.get("/api/v1/recommendations/guides/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "fallback"
    assert body["results"][0]["guide_code"] == "EBC-01"  # highest average_rating


@pytest.mark.django_db
def test_feed_requires_authentication():
    resp = APIClient().get("/api/v1/recommendations/routes/")
    assert resp.status_code in (401, 403)
