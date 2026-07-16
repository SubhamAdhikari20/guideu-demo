"""Production settings — secure defaults, fail fast on misconfiguration."""
from __future__ import annotations

import os

from .base import *  # noqa: F401,F403
from .base import INSECURE_DEV_SECRET_KEY, SECRET_KEY

DEBUG = False

# Fail fast rather than booting insecurely.
if SECRET_KEY == INSECURE_DEV_SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

if os.environ.get("DJANGO_DB_ENGINE", "").endswith("sqlite3"):
    raise RuntimeError("A real database (PostgreSQL) is required in production.")

# ---- Transport / browser security -----------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Rotate + blacklist refresh tokens in production.
SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = True  # noqa: F405
