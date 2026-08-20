"""Hermetic settings for the core-engine test suite.

The repository-level ``.env`` is intended for Docker and may select PostgreSQL
or Redis.  Tests must never inherit those service choices: a contributor should
get the same result from ``pytest`` whether or not the Docker stack is running.
"""
from __future__ import annotations

from .dev import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "guideu-tests",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EVENTS_PUBLISH_EAGER = False
EVENTS_ENABLED = False
