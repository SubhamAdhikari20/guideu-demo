"""Development settings — zero-setup local runs.

Defaults to SQLite so the project boots with no external services, but honours
``DJANGO_DB_ENGINE=postgresql`` (+ creds) when Postgres is available.
"""
from __future__ import annotations

import os

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK

DEBUG = True

# ---- Cache -----------------------------------------------------------------
# base.py points the cache at Redis, which is right in Docker and in production
# but breaks a bare ``manage.py runserver``: Django's RedisCache has no
# ignore-errors mode, so with no Redis listening every cached endpoint returns
# 500 rather than simply missing the cache.
#
# Both compose files set REDIS_URL explicitly, so its presence in the
# environment is a reliable signal for "Redis is actually available". Without
# it, fall back to local memory and keep the promise this module's docstring
# makes. Throttling shares this cache, so it stays per-process in that mode —
# fine for local development, and the container path is unchanged.
if not os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "guideu-dev",
        }
    }

# Permissive CORS in development only.
CORS_ALLOW_ALL_ORIGINS = True

# Print emails to the console instead of sending them.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Make domain events fire immediately so they are observable without a worker.
EVENTS_PUBLISH_EAGER = True

# Browsable API is handy while developing.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)
