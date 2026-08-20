from __future__ import annotations

from fastapi import APIRouter

from registry import list_models, loadable_models

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness probe + currently registered model versions.

    ``models`` is what the registry claims; ``unavailable`` is the subset whose
    artifact could not be found on this machine. The two disagree whenever a
    registry is copied somewhere its .joblib files are not (the classic case: a
    registry trained on the host, served from a container), and every inference
    path degrades silently in that state — so it is reported rather than hidden.
    """
    cards = list_models()
    loadable = loadable_models()
    unavailable = sorted(name for name, ok in loadable.items() if not ok)
    return {
        "status": "degraded" if unavailable else "healthy",
        "service": "guideu-analytics-engine",
        "models": {card.name: card.version for card in cards},
        "models_loadable": sum(1 for ok in loadable.values() if ok),
        "unavailable": unavailable,
    }
