"""GuideU analytics-engine — FastAPI application factory.

Serves anti-scam scoring, route recommendations, guide ranking and price
benchmarking. Boots and serves with only pandas + scikit-learn; trained model
artifacts are loaded lazily from the registry when present (ADR-0006).
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import forecasting, guides, health, pricing, recommendations, scam, segments
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("guideu.ml.app")

DESCRIPTION = """
GuideU's machine-learning service.

* **/api/v1/scam/score** — explainable overcharge / scam probability, including the
  below-fair-wage flag that protects guides from under-quoting
* **/api/v1/recommendations/routes** — personalised route ranking from the learned ranker
* **/api/v1/guides/rank** — verified-guide ranking by predicted match quality
* **/api/v1/segments/assign** — cold-start tourist segment
* **/api/v1/forecast/arrivals** — projected monthly tourist arrivals
* **/api/v1/pricing/benchmark** — fair-price transparency
* **/api/v1/models** — model registry (versions, metrics, fairness)

Internal endpoints require the `X-API-Key` header.
""".strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the models and the pricing table before the first request arrives.

    Everything here is lazily cached on first use, which used to mean the first
    recommendation of the process paid for loading the artifact and building the
    2,000-route profile. The core-engine's HTTP client gives up after 4 seconds,
    so that one cold request timed out and the app quietly served its
    non-personalised fallback instead. Warming at startup costs a second of boot
    time and removes the whole failure mode.
    """
    started = time.perf_counter()
    warmed = []
    try:
        from inference import forecasting as forecasting_inf
        from inference import pricing as pricing_inf
        from inference import recommender, segments as segments_inf

        recommender.recommend(tourist={"pref_adventure_score": 0.5}, top_k=1)
        warmed.append("recommender")
        pricing_inf.fair_price("Licensed Guide")
        warmed.append("pricing")
        forecasting_inf.forecast()
        warmed.append("forecast")
        segments_inf.assign({})
        warmed.append("segments")
    except Exception as exc:  # pragma: no cover - warm-up must never block boot
        logger.warning("warm-up skipped (%s): %s", type(exc).__name__, exc)

    logger.info("warm-up complete in %.2fs: %s", time.perf_counter() - started, ", ".join(warmed) or "nothing")
    yield


def create_app() -> FastAPI:
    get_settings()  # ensure artifact dir exists, fail fast on bad config
    app = FastAPI(
        title="GuideU Analytics Engine",
        version="1.0.0",
        description=DESCRIPTION,
        lifespan=lifespan,
        contact={"name": "GuideU"},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(scam.router)
    app.include_router(recommendations.router)
    app.include_router(guides.router)
    app.include_router(segments.router)
    app.include_router(forecasting.router)
    app.include_router(pricing.router)

    @app.get("/", tags=["health"])
    async def index() -> dict:
        return {"service": "guideu-analytics-engine", "docs": "/docs", "health": "/health"}

    return app


app = create_app()
