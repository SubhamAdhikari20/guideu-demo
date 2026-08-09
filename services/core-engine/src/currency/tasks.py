from __future__ import annotations

from celery import shared_task
from django.core.cache import cache

from . import services


@shared_task
def refresh_currency_rates() -> dict[str, float]:
    """Refresh the cached exchange rates (scheduled via Celery Beat)."""
    rates = services.fetch_live_rates()
    cache.set(services.CACHE_KEY, rates, services.CACHE_TTL)
    return rates
