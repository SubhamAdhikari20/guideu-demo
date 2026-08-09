"""End-to-end journeys across the whole stack.

Unlike the per-app unit tests, these drive a real user flow through several apps
with a real JWT (register -> login -> use protected APIs), so they catch wiring
problems between auth, catalog, recommendations, workspace, currency and safety.
"""
from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from src.catalog.models import Region, TrekkingRoute
from src.currency import services as currency_services


@pytest.fixture
def seeded_catalog(db):
    region = Region.objects.create(name="Khumbu", slug="khumbu")
    TrekkingRoute.objects.create(
        external_id="RTE0001", route_name="Everest Base Camp", region=region,
        difficulty="Hard", badge_points=200, estimated_cost_usd=1400,
    )
    # Avoid a live currency API call in tests.
    cache.set(currency_services.CACHE_KEY, {"NPR": 1.0, "USD": 0.0075}, 3600)


@pytest.mark.django_db
def test_tourist_plans_a_trip_end_to_end(seeded_catalog):
    client = APIClient()

    # 1. Register
    reg = client.post(
        "/api/v1/auth/register/",
        {"username": "journey", "email": "journey@test.com",
         "password": "JourneyTest123!", "first_name": "Journey"},
    )
    assert reg.status_code == 201

    # 2. Log in with a real JWT
    tok = client.post(
        "/api/v1/auth/token/",
        {"email": "journey@test.com", "password": "JourneyTest123!"},
    )
    assert tok.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tok.json()['access']}")

    # 3. Browse the catalog and the personalised feed
    assert client.get("/api/v1/catalog/routes/").status_code == 200
    feed = client.get("/api/v1/recommendations/routes/")
    assert feed.status_code == 200 and len(feed.json()["results"]) >= 1

    # 4. Plan a trip
    trip = client.post(
        "/api/v1/workspace/trips/",
        {"title": "My Trek", "start_date": "2026-10-01", "end_date": "2026-10-05",
         "total_budget_npr": "40000.00"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    item = client.post(
        "/api/v1/workspace/items/",
        {"workspace": trip_id, "item_type": "custom", "custom_title": "Day hike",
         "day_number": 1, "estimated_cost_npr": "3000.00"},
    )
    assert item.status_code == 201

    budget = client.get(f"/api/v1/workspace/trips/{trip_id}/budget-summary/")
    assert budget.status_code == 200
    assert budget.json()["total_planned_npr"] == 3000.0

    # 5. Convert a price
    conv = client.get("/api/v1/currency/convert/?amount=40000&to=USD")
    assert conv.status_code == 200 and conv.json()["converted"] == 300.0

    # 6. Raise a safety SOS
    sos = client.post("/api/v1/safety/sos/", {"message": "All good, testing"})
    assert sos.status_code == 201


@pytest.mark.django_db
def test_anonymous_user_cannot_reach_protected_apis():
    client = APIClient()
    assert client.get("/api/v1/workspace/trips/").status_code in (401, 403)
    assert client.post("/api/v1/safety/sos/", {"message": "x"}).status_code in (401, 403)
