"""Lightweight model registry with an optional MLflow backend.

Training writes artifacts here; inference loads the latest version. When MLflow
is installed and ``MLFLOW_TRACKING_URI`` is set, runs are also logged to MLflow —
otherwise everything is recorded in ``artifacts/model_registry.json`` so the
service has no hard dependency on a tracking server (see ADR-0006).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib

from app.config import get_settings

logger = logging.getLogger("guideu.ml.registry")


@dataclass
class ModelCard:
    name: str
    version: str
    #: Artifact location *relative to the configured artifact_dir* (i.e. just the
    #: filename). Older registries recorded an absolute path from the machine that
    #: trained the model; :func:`_resolve_artifact` still accepts those.
    artifact_path: str
    metrics: dict[str, float]
    params: dict[str, Any]
    trained_at: str
    n_train: int
    notes: str = ""


def _registry_path() -> Path:
    return Path(get_settings().artifact_dir) / "model_registry.json"


def _load_registry() -> dict[str, ModelCard]:
    path = _registry_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {name: ModelCard(**card) for name, card in raw.items()}


def _save_registry(cards: dict[str, ModelCard]) -> None:
    path = _registry_path()
    path.write_text(json.dumps({k: asdict(v) for k, v in cards.items()}, indent=2), encoding="utf-8")


def save_model(
    *, name: str, model: Any, metrics: dict[str, float], params: dict[str, Any], n_train: int, notes: str = ""
) -> ModelCard:
    """Persist a trained model + its card; optionally log to MLflow."""
    settings = get_settings()
    version = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    artifact_file = Path(settings.artifact_dir) / f"{name}.joblib"
    joblib.dump(model, artifact_file)

    card = ModelCard(
        name=name,
        version=f"{name}-{version}",
        # Store the filename, not the absolute path. The registry travels with the
        # artifacts (into a Docker image, a volume, or a marker's machine) and an
        # absolute training-host path would not exist at the other end.
        artifact_path=artifact_file.name,
        metrics={k: round(float(v), 4) for k, v in metrics.items()},
        params=params,
        trained_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        n_train=n_train,
        notes=notes,
    )
    cards = _load_registry()
    cards[name] = card
    _save_registry(cards)
    _maybe_log_mlflow(card)
    logger.info("saved model %s (%s) metrics=%s", name, card.version, card.metrics)
    return card


def _resolve_artifact(card: ModelCard) -> Path | None:
    """Find ``card``'s .joblib on *this* machine, or None if it is missing.

    Tried in order: the recorded path as-is (absolute paths from legacy
    registries, and relative paths from the process cwd), then the filename
    inside the configured ``artifact_dir``, then the conventional
    ``<artifact_dir>/<name>.joblib``. The second is what rescues a registry
    trained on the Windows host and served from the Linux container: the
    artifacts are right there in /app/artifacts, only the recorded path is
    meaningless.
    """
    artifact_dir = Path(get_settings().artifact_dir)
    recorded = Path(card.artifact_path)
    candidates = [recorded, artifact_dir / recorded.name, artifact_dir / f"{card.name}.joblib"]
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except OSError:  # e.g. a Windows path evaluated on Linux
            continue
    return None


def load_model(name: str) -> Any | None:
    card = _load_registry().get(name)
    if not card:
        return None
    path = _resolve_artifact(card)
    if path is None:
        logger.warning(
            "model %s is registered as %s but no artifact was found (looked in %s) — "
            "inference for it will fall back or return empty",
            name,
            card.artifact_path,
            get_settings().artifact_dir,
        )
        return None
    return joblib.load(path)


def loadable_models() -> dict[str, bool]:
    """Which registered models actually have an artifact on disk.

    Registration and loadability are not the same thing, and the difference is
    invisible from the outside: every inference path degrades quietly, so a
    dashboard reading the registry shows five healthy models while nothing can
    actually score. /health reports this so the gap is visible.
    """
    return {card.name: _resolve_artifact(card) is not None for card in list_models()}


def get_card(name: str) -> ModelCard | None:
    return _load_registry().get(name)


def list_models() -> list[ModelCard]:
    return list(_load_registry().values())


def _maybe_log_mlflow(card: ModelCard) -> None:
    settings = get_settings()
    if not settings.mlflow_tracking_uri:
        return
    try:  # pragma: no cover - optional dependency
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment("guideu")
        artifact = _resolve_artifact(card)
        with mlflow.start_run(run_name=card.version):
            mlflow.log_params(card.params)
            mlflow.log_metrics(card.metrics)
            if artifact is not None:
                mlflow.log_artifact(str(artifact))
    except Exception as exc:  # pragma: no cover
        logger.warning("MLflow logging skipped: %s", exc)
