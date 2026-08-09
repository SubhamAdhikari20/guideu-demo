"""HTTP client for the FastAPI ``analytics-engine`` (ML service).

Keeps all ML calls behind one typed surface so views/Celery tasks never embed
URLs or auth headers. Network failures degrade gracefully — callers receive
``None`` and can fall back to a deterministic benchmark lookup.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger("guideu.ml")


class AnalyticsEngineClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: float = 4.0):
        self.base_url = (base_url or getattr(settings, "ANALYTICS_ENGINE_URL", "http://localhost:8001")).rstrip("/")
        self.api_key = api_key or getattr(settings, "ANALYTICS_API_KEY", "")
        self.timeout = timeout

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        try:
            resp = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers={"X-API-Key": self.api_key},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.warning("analytics-engine call failed (%s): %s", path, exc)
            return None

    def score_scam(self, *, service_type: str, region: str, season: str, quoted_price_npr: float) -> dict[str, Any] | None:
        return self._post(
            "/api/v1/scam/score",
            {
                "service_type": service_type,
                "region": region,
                "season": season,
                "quoted_price_npr": quoted_price_npr,
            },
        )

    def recommend_routes(self, *, tourist: dict[str, Any], season: str | None = None, top_k: int = 5) -> dict[str, Any] | None:
        return self._post(
            "/api/v1/recommendations/routes",
            {"tourist": tourist, "season": season, "top_k": top_k},
        )

    def rank_guides(self, *, tourist: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        return self._post("/api/v1/guides/rank", {"tourist": tourist, "candidates": candidates})

    def assign_segment(self, *, tourist: dict[str, Any]) -> dict[str, Any] | None:
        """Cold-start segment for a tourist with no interaction history."""
        return self._post("/api/v1/segments/assign", tourist)

    def forecast_arrivals(
        self, *, year: int | None = None, months: list[int] | None = None, region: str | None = None
    ) -> dict[str, Any] | None:
        """Projected monthly arrivals, used for capacity planning and busy-month hints."""
        return self._post("/api/v1/forecast/arrivals", {"year": year, "months": months, "region": region})


def get_analytics_client() -> AnalyticsEngineClient:
    return AnalyticsEngineClient()
