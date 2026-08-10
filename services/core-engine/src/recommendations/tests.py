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


@pytest.fixture
def offline_ml(monkeypatch):
    """Simulate an unreachable analytics-engine.

    These tests used to rely on nothing listening on port 8001, which made them
    pass or fail depending on whether the ML service happened to be running —
    the guide test broke the moment it was. Patching the client makes the
    fallback path the thing actually under test.
    """
    class _Offline:
        def recommend_routes(self, **_kwargs):
            return None

        def rank_guides(self, **_kwargs):
            return None

        def forecast_arrivals(self, **_kwargs):
            return None

    monkeypatch.setattr("src.recommendations.views.get_analytics_client", lambda: _Offline())


@pytest.fixture
def online_ml(monkeypatch):
    """A stub analytics-engine that ranks the second route/guide first."""
    class _Online:
        def recommend_routes(self, **_kwargs):
            return {
                "model_version": "test-ranker-1",
                "items": [
                    {"route_id": "RTE0002", "score": 0.9, "components": {}, "why": ["Because it is gentle."]},
                    {"route_id": "RTE0001", "score": 0.4, "components": {}, "why": ["Because it is hard."]},
                ],
            }

        def rank_guides(self, **_kwargs):
            return {
                "model_version": "test-guide-1",
                "items": [
                    {"guide_id": "GDE00002", "score": 0.9, "components": {}},
                    {"guide_id": "GDE00001", "score": 0.3, "components": {}},
                ],
            }

    monkeypatch.setattr("src.recommendations.views.get_analytics_client", lambda: _Online())


@pytest.mark.django_db
def test_route_feed_falls_back_to_top_routes_without_ml(client, catalog, offline_ml):
    """With no ML service reachable the feed still returns ranked routes."""
    resp = client.get("/api/v1/recommendations/routes/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "fallback"
    # Most rewarding route (highest badge_points) comes first.
    assert body["results"][0]["route_name"] == "Everest Base Camp"


@pytest.mark.django_db
def test_guide_feed_falls_back_to_top_rated_without_ml(client, catalog, offline_ml):
    resp = client.get("/api/v1/recommendations/guides/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "fallback"
    assert body["results"][0]["guide_code"] == "EBC-01"  # highest average_rating


@pytest.mark.django_db
def test_route_feed_uses_ml_ordering_and_carries_reasons(client, catalog, online_ml):
    """When the ML service answers, its ordering wins and its reasons come through."""
    resp = client.get("/api/v1/recommendations/routes/")
    body = resp.json()
    assert body["source"] == "ml"
    assert body["model_version"] == "test-ranker-1"
    # The stub ranked the easy route first, against the fallback's own ordering.
    assert body["results"][0]["route_name"] == "Ghorepani Poon Hill"
    assert body["results"][0]["why"] == ["Because it is gentle."]


@pytest.mark.django_db
def test_guide_feed_uses_ml_ordering(client, catalog, online_ml):
    body = client.get("/api/v1/recommendations/guides/").json()
    assert body["source"] == "ml"
    # The stub ranked the lower-rated guide first, so this cannot be the fallback.
    assert body["results"][0]["guide_code"] == "POON-01"


@pytest.mark.django_db
def test_feed_requires_authentication():
    resp = APIClient().get("/api/v1/recommendations/routes/")
    assert resp.status_code in (401, 403)
