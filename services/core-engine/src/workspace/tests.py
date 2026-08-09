from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from src.authentication.models import User
from src.catalog.models import Region, TrekkingRoute
from src.workspace.models import TravelWorkspace, WorkspaceItem


@pytest.fixture
def tourist(db):
    return User.objects.create_user(email="t@e.com", username="t", password="pass12345")


@pytest.fixture
def other(db):
    return User.objects.create_user(email="o@e.com", username="o", password="pass12345")


def auth(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_create_trip_and_add_items_then_budget_summary(tourist):
    client = auth(tourist)

    trip = client.post(
        "/api/v1/workspace/trips/",
        {"title": "Annapurna 2026", "start_date": "2026-10-01", "end_date": "2026-10-07", "total_budget_npr": "50000.00"},
    )
    assert trip.status_code == 201
    trip_id = trip.json()["id"]

    for cost, kind in [("12000.00", "guide"), ("8000.00", "accommodation")]:
        r = client.post(
            "/api/v1/workspace/items/",
            {"workspace": trip_id, "item_type": kind, "day_number": 1, "estimated_cost_npr": cost, "custom_title": kind},
        )
        assert r.status_code == 201

    summary = client.get(f"/api/v1/workspace/trips/{trip_id}/budget-summary/").json()
    assert summary["total_planned_npr"] == 20000.0
    assert summary["remaining_npr"] == 30000.0
    assert summary["is_over_budget"] is False


@pytest.mark.django_db
def test_end_date_before_start_is_rejected(tourist):
    r = auth(tourist).post(
        "/api/v1/workspace/trips/",
        {"title": "Bad", "start_date": "2026-10-07", "end_date": "2026-10-01"},
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_reorder_updates_day_and_order(tourist):
    client = auth(tourist)
    trip = TravelWorkspace.objects.create(
        tourist=tourist, title="T", start_date="2026-10-01", end_date="2026-10-05"
    )
    a = WorkspaceItem.objects.create(workspace=trip, item_type="custom", day_number=1, display_order=0)
    b = WorkspaceItem.objects.create(workspace=trip, item_type="custom", day_number=1, display_order=1)

    r = client.post(
        "/api/v1/workspace/items/reorder/",
        [{"item_id": b.id, "day_number": 2, "display_order": 0},
         {"item_id": a.id, "day_number": 1, "display_order": 0}],
        format="json",
    )
    assert r.status_code == 200
    b.refresh_from_db()
    assert b.day_number == 2


@pytest.mark.django_db
def test_apply_ai_suggestions_seeds_items_from_routes(tourist):
    region = Region.objects.create(name="Khumbu", slug="khumbu")
    for i in range(3):
        TrekkingRoute.objects.create(
            external_id=f"RTE000{i}", route_name=f"Route {i}", region=region,
            difficulty="Hard", badge_points=100 - i, estimated_cost_usd=400,
        )
    client = auth(tourist)
    trip = TravelWorkspace.objects.create(
        tourist=tourist, title="AI Trip", start_date="2026-10-01", end_date="2026-10-03"
    )
    # ML service is unreachable in tests, so this exercises the fallback path.
    r = client.post(f"/api/v1/workspace/trips/{trip.id}/apply-suggestions/")
    assert r.status_code == 201
    assert len(r.json()["items"]) >= 1
    assert WorkspaceItem.objects.filter(workspace=trip, item_type="destination").exists()


@pytest.mark.django_db
def test_cannot_see_other_users_trip(tourist, other):
    trip = TravelWorkspace.objects.create(
        tourist=other, title="Theirs", start_date="2026-10-01", end_date="2026-10-05"
    )
    assert auth(tourist).get(f"/api/v1/workspace/trips/{trip.id}/").status_code == 404
