"""Multi-currency support.

All prices are stored in NPR. This converts NPR to the tourist's currency for
display only. Rates are cached in Redis (6h) and fetched from a free API, with a
static fallback so the feature never hard-fails when the network/API is down.
"""
from __future__ import annotations

import logging
from decimal import Decimal

import requests
from django.core.cache import cache

logger = logging.getLogger("guideu.currency")

SUPPORTED_CURRENCIES = ["NPR", "USD", "EUR", "GBP", "INR", "AUD", "JPY"]
CACHE_KEY = "currency_rates"
CACHE_TTL = 60 * 60 * 6  # 6 hours

# Approximate NPR -> X fallback rates (used only if the live API is unreachable).
_FALLBACK_RATES = {
    "NPR": 1.0, "USD": 0.0075, "EUR": 0.0069,
    "GBP": 0.0059, "INR": 0.63, "AUD": 0.0114, "JPY": 1.12,
}


def fetch_live_rates() -> dict[str, float]:
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/NPR", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()["rates"]
        rates = {cur: float(data.get(cur, _FALLBACK_RATES[cur])) for cur in SUPPORTED_CURRENCIES}
        rates["NPR"] = 1.0
        return rates
    except (requests.RequestException, KeyError, ValueError) as exc:  # pragma: no cover - network
        logger.warning("currency rate fetch failed, using fallback: %s", exc)
        return dict(_FALLBACK_RATES)


def get_rates() -> dict[str, float]:
    rates = cache.get(CACHE_KEY)
    if rates:
        return rates
    rates = fetch_live_rates()
    cache.set(CACHE_KEY, rates, CACHE_TTL)
    return rates


def convert(amount_npr: Decimal | float, to_currency: str) -> float:
    rate = get_rates().get(to_currency.upper(), 1.0)
    return round(float(amount_npr) * rate, 2)


def convert_all(amount_npr: Decimal | float) -> dict[str, float]:
    return {cur: round(float(amount_npr) * rate, 2) for cur, rate in get_rates().items()}
