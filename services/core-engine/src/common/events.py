"""Centralised Redis event publishing for the core engine.

Domain apps publish compact JSON events to ``guideu:*.events`` channels; the
Node ``real-time-engine`` subscribes and fans them out over WebSockets. Keeping
this in one place (instead of duplicating ``publish_event`` in every app)
guarantees a single, consistent event contract — see
``docs/api-contracts.md``.

Publishing is best-effort and fault-isolated: a Redis outage must never break a
business transaction. Events are emitted on the post-commit hook so consumers
never observe an event for a row that later rolled back.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from django.conf import settings
from django.db import transaction

logger = logging.getLogger("guideu.events")


@lru_cache(maxsize=1)
def _redis_client():  # pragma: no cover - thin wrapper around redis-py
    import redis

    url = getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
    return redis.from_url(url)


def _publish_now(channel: str, payload: dict[str, Any]) -> None:
    try:
        _redis_client().publish(channel, json.dumps(payload, default=str))
        logger.debug("published %s -> %s", payload.get("event"), channel)
    except Exception as exc:  # pragma: no cover - runtime resilience
        logger.warning("could not publish event to Redis (%s): %s", channel, exc)


def publish_event(channel: str, payload: dict[str, Any], *, on_commit: bool = True) -> None:
    """Publish ``payload`` to a Redis ``channel``.

    By default the publish is deferred until the surrounding DB transaction
    commits. Set ``on_commit=False`` to publish immediately (e.g. for events not
    tied to a write).
    """
    if not getattr(settings, "EVENTS_ENABLED", True):
        return
    if on_commit and not getattr(settings, "EVENTS_PUBLISH_EAGER", False):
        transaction.on_commit(lambda: _publish_now(channel, payload))
    else:
        _publish_now(channel, payload)


# Canonical channel names — import these instead of hardcoding strings.
class Channels:
    USER = "guideu:user.events"
    BOOKING = "guideu:booking.events"
    PAYMENT = "guideu:payment.events"
    PERMIT = "guideu:permit.events"
    NOTIFICATION = "guideu:notification.events"
    REVIEW = "guideu:review.events"
