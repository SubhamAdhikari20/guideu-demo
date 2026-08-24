"""Top-level non-API views: a service index, a liveness probe and a readiness probe."""
from __future__ import annotations

import logging

import requests
from django.conf import settings
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger("guideu.health")


def service_index(request) -> JsonResponse:
    """Human-friendly index of the core engine's entry points."""
    return JsonResponse(
        {
            "service": "guideu-core-engine",
            "status": "ok",
            "docs": "/api/docs/",
            "schema": "/api/schema/",
            "admin": "/admin/",
            "api_root": "/api/v1/",
            "health": "/healthz/",
            "readiness": "/readyz/",
        }
    )


def healthz(request) -> JsonResponse:
    """Liveness probe used by orchestrators. Says nothing about dependencies."""
    return JsonResponse({"status": "healthy"})


def readyz(request) -> JsonResponse:
    """Readiness probe that reports whether each dependency is actually reachable.

    Every machine-learning call in this project degrades gracefully: if the
    analytics engine cannot be reached the caller silently gets a benchmark
    answer instead of a model answer. That is the right behaviour for a
    traveller, but it also means a completely dead ML service looks identical
    to a healthy one from the outside, and a wrong ANALYTICS_ENGINE_URL can sit
    unnoticed through an entire demo. This endpoint exists so the degradation
    is visible on purpose rather than discovered by accident.
    """
    checks: dict[str, dict] = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = {"ok": True, "engine": connection.vendor}
    except Exception as exc:  # noqa: BLE001 - probe must never raise
        checks["database"] = {"ok": False, "error": str(exc)[:200]}

    analytics_url = getattr(settings, "ANALYTICS_ENGINE_URL", "").rstrip("/")
    analytics: dict = {"ok": False, "url": analytics_url}
    try:
        response = requests.get(f"{analytics_url}/health", timeout=3)
        response.raise_for_status()
        body = response.json()
        loadable = body.get("models_loadable")
        analytics.update(
            ok=True,
            models_loaded=len(body.get("models", {})),
            models_loadable=loadable,
            unavailable=body.get("unavailable", []),
        )
        # Registered but unloadable models are the failure mode that shipped a
        # full model registry page while every prediction fell back to rules.
        if loadable is not None and body.get("models") and loadable < len(body["models"]):
            analytics["ok"] = False
            analytics["error"] = "some registered models cannot be loaded"
    except (requests.RequestException, ValueError) as exc:
        analytics["error"] = str(exc)[:200]
        analytics["hint"] = (
            "Running natively? ANALYTICS_ENGINE_URL must be http://localhost:8001. "
            "The docker-compose value (http://analytics-engine:8001) only resolves inside compose."
        )
        logger.warning("readiness: analytics engine unreachable at %s (%s)", analytics_url, exc)
    checks["analytics_engine"] = analytics

    ready = all(part.get("ok") for part in checks.values())
    payload = {
        "status": "ready" if ready else "degraded",
        "ml_predictions": "live" if analytics.get("ok") else "falling back to benchmarks",
        "checks": checks,
    }
    # 200 either way: a degraded core engine still serves traffic. The status
    # field is what a human or a probe should read, not the HTTP code.
    return JsonResponse(payload)
