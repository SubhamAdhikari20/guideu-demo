from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from src.authentication.models import User
from src.safety.models import SosAlert


@pytest.fixture
def tourist(db):
    return User.objects.create_user(email="t@e.com", username="t", password="pass12345")


def auth(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_raise_sos_records_alert_for_the_user(tourist):
    resp = auth(tourist).post(
        "/api/v1/safety/sos/",
        {"latitude": "28.000000", "longitude": "84.000000", "message": "Need help on the trail"},
    )
    assert resp.status_code == 201
    alert = SosAlert.objects.get()
    assert alert.user == tourist
    assert alert.status == SosAlert.Status.ACTIVE


@pytest.mark.django_db
def test_resolve_marks_alert_resolved(tourist):
    client = auth(tourist)
    alert_id = client.post("/api/v1/safety/sos/", {"message": "help"}).json()["id"]
    resp = client.post(f"/api/v1/safety/sos/{alert_id}/resolve/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"


@pytest.mark.django_db
def test_user_only_sees_own_alerts(tourist):
    other = User.objects.create_user(email="o@e.com", username="o", password="pass12345")
    SosAlert.objects.create(user=other, message="theirs")
    resp = auth(tourist).get("/api/v1/safety/sos/")
    rows = resp.json()
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert rows == []
