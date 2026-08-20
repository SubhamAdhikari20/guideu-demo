"""The registry must survive being moved away from the machine that trained it.

Training bakes a card into artifacts/model_registry.json. That file travels with
the artifacts — into a Docker image, a named volume, a marker's checkout — while
the absolute path recorded on the training host does not. When the two disagree
every inference endpoint returns an empty result and the admin dashboard says
"train the model", even though the .joblib is sitting right there.
"""
from __future__ import annotations

import json

import joblib
import pytest

import registry
from app.config import get_settings


@pytest.fixture
def registry_dir(tmp_path, monkeypatch):
    """Point the registry at a throwaway artifact_dir for the duration of a test."""
    settings = get_settings()
    original = settings.artifact_dir
    monkeypatch.setattr(settings, "artifact_dir", tmp_path)
    yield tmp_path
    monkeypatch.setattr(settings, "artifact_dir", original)


def test_save_model_records_a_relative_path(registry_dir):
    registry.save_model(name="demo", model={"weights": [1, 2]}, metrics={"rmse": 0.5}, params={}, n_train=10)

    raw = json.loads((registry_dir / "model_registry.json").read_text(encoding="utf-8"))
    assert raw["demo"]["artifact_path"] == "demo.joblib"
    assert registry.load_model("demo") == {"weights": [1, 2]}


def test_load_model_recovers_from_a_foreign_absolute_path(registry_dir):
    """A registry trained elsewhere still loads, as long as the artifact is here."""
    joblib.dump({"weights": [3]}, registry_dir / "demo.joblib")
    (registry_dir / "model_registry.json").write_text(
        json.dumps(
            {
                "demo": {
                    "name": "demo",
                    "version": "demo-20260810085116",
                    # Exactly what a Windows training run used to write.
                    "artifact_path": r"C:\Users\someone\guideu\artifacts\demo.joblib",
                    "metrics": {"rmse": 0.5},
                    "params": {},
                    "trained_at": "2026-08-10T08:51:16+00:00",
                    "n_train": 10,
                    "notes": "",
                }
            }
        ),
        encoding="utf-8",
    )

    assert registry.load_model("demo") == {"weights": [3]}
    assert registry.loadable_models() == {"demo": True}


def test_missing_artifact_is_reported_not_hidden(registry_dir):
    (registry_dir / "model_registry.json").write_text(
        json.dumps(
            {
                "ghost": {
                    "name": "ghost",
                    "version": "ghost-1",
                    "artifact_path": "ghost.joblib",
                    "metrics": {},
                    "params": {},
                    "trained_at": "2026-08-10T08:51:16+00:00",
                    "n_train": 0,
                    "notes": "",
                }
            }
        ),
        encoding="utf-8",
    )

    assert registry.load_model("ghost") is None
    assert registry.loadable_models() == {"ghost": False}
