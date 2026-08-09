"""Shared pytest setup for the core-engine.

Tests run without the Docker stack, so swap the Redis-backed cache (used by DRF
throttling) for a local in-memory one. This keeps tests hermetic — no Redis, no
network — without changing any production setting.
"""
import pytest


@pytest.fixture(autouse=True)
def _local_cache(settings):
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }
