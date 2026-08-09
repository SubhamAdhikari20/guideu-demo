from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from src.currency import services

# Seed deterministic rates so tests never hit the live API.
_RATES = {"NPR": 1.0, "USD": 0.0075, "EUR": 0.0069, "GBP": 0.0059, "INR": 0.63, "AUD": 0.0114, "JPY": 1.12}


@pytest.fixture(autouse=True)
def seed_rates():
    cache.set(services.CACHE_KEY, _RATES, 3600)
    yield
    cache.delete(services.CACHE_KEY)


def test_convert_uses_cached_rate():
    assert services.convert(10000, "USD") == 75.0


@pytest.mark.django_db
def test_rates_endpoint():
    resp = APIClient().get("/api/v1/currency/rates/")
    assert resp.status_code == 200
    assert resp.json()["base"] == "NPR"
    assert resp.json()["rates"]["USD"] == 0.0075


@pytest.mark.django_db
def test_convert_endpoint():
    resp = APIClient().get("/api/v1/currency/convert/?amount=5000&to=USD")
    assert resp.status_code == 200
    assert resp.json()["converted"] == 37.5


@pytest.mark.django_db
def test_convert_endpoint_rejects_unknown_currency():
    resp = APIClient().get("/api/v1/currency/convert/?amount=5000&to=XYZ")
    assert resp.status_code == 400
