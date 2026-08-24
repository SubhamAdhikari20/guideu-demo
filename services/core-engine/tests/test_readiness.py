"""Tests for the readiness probe.

The probe exists because every ML call in this project degrades gracefully.
When the analytics engine is unreachable the traveller still gets an answer,
computed from pricing benchmarks instead of a model, so a dead ML service and
a healthy one look identical from the outside. These tests pin the behaviour
that makes that difference visible.
"""
from __future__ import annotations

import requests
from django.test import Client


def _readyz(monkeypatch, *, health_payload=None, raises=None):
    class _Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return health_payload

    def fake_get(url, timeout=None):  # noqa: ARG001 - signature mirrors requests.get
        if raises is not None:
            raise raises
        return _Response()

    monkeypatch.setattr(requests, "get", fake_get)
    response = Client().get("/readyz/")
    assert response.status_code == 200
    return response.json()


def test_readyz_reports_ready_when_every_model_loads(monkeypatch, db):
    body = _readyz(
        monkeypatch,
        health_payload={
            "status": "healthy",
            "models": {f"m{i}": f"m{i}-v1" for i in range(5)},
            "models_loadable": 5,
            "unavailable": [],
        },
    )
    assert body["status"] == "ready"
    assert body["ml_predictions"] == "live"
    assert body["checks"]["analytics_engine"]["ok"] is True
    assert body["checks"]["analytics_engine"]["models_loaded"] == 5


def test_readyz_flags_unreachable_analytics_and_explains_the_docker_hostname(monkeypatch, db):
    """The real defect this guards: .env ships the docker-compose hostname,
    which does not resolve on a native run, so recommendations quietly fall
    back to benchmarks for the whole demo."""
    body = _readyz(
        monkeypatch,
        raises=requests.ConnectionError("Failed to resolve 'analytics-engine'"),
    )
    assert body["status"] == "degraded"
    assert body["ml_predictions"] == "falling back to benchmarks"
    analytics = body["checks"]["analytics_engine"]
    assert analytics["ok"] is False
    assert "localhost:8001" in analytics["hint"]


def test_readyz_flags_models_that_are_registered_but_cannot_load(monkeypatch, db):
    """A registry full of models that fail to load renders a perfect admin page
    while every prediction silently falls back. Registered is not loadable."""
    body = _readyz(
        monkeypatch,
        health_payload={
            "status": "healthy",
            "models": {f"m{i}": f"m{i}-v1" for i in range(5)},
            "models_loadable": 2,
            "unavailable": ["guide_ranker", "arrivals_forecaster", "tourist_segments"],
        },
    )
    assert body["status"] == "degraded"
    assert body["checks"]["analytics_engine"]["ok"] is False
    assert body["checks"]["analytics_engine"]["error"]
