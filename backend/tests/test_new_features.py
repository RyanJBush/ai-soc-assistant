"""Tests for the new Phase 2–4 features:

- Consistent error envelope (error_code, message, timestamp)
- Optional API-key authentication
- Model-based feature contributors (RF feature_importances_, LR coef_)
- Background-task alert creation (non-blocking)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes_predict import get_alert_service, get_prediction_service
from backend.app.core.config import Settings
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.main import app
from backend.app.ml.preprocessing import build_preprocessor
from backend.app.schemas.errors import ErrorResponse
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.model_registry import ModelRegistry
from backend.app.services.prediction_service import PredictionService

# ---------------------------------------------------------------------------
# Module-level stub pipelines (must be picklable for joblib.dump)
# ---------------------------------------------------------------------------


class _NoPipelinePipeline:
    """A stub that acts like a plain callable (no named_steps); exercises heuristic fallback."""

    def predict_proba(self, _frame: pd.DataFrame):
        return [[0.3, 0.7]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PAYLOAD = {
    "duration": 0,
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 100,
    "dst_bytes": 200,
    "count": 5,
    "srv_count": 5,
    "serror_rate": 0.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 10,
    "dst_host_srv_count": 10,
}

_BASE_REQUEST = InferenceRequest(**_PAYLOAD)


class StubAlertService:
    def create_alert(self, request, response):
        pass

    def get_recent_alerts(self, limit: int):
        return []


def _stub_response() -> InferenceResponse:
    return InferenceResponse(
        prediction_label="benign",
        malicious_probability=0.1,
        confidence=0.9,
        risk_level="low",
        top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
        model_version="stub-model",
        timestamp=datetime.now(tz=timezone.utc),
    )


def _make_stub_svc():
    class StubPredictionService:
        def predict(self, _r):
            return _stub_response()

    return StubPredictionService()


# ---------------------------------------------------------------------------
# Error Envelope Schema
# ---------------------------------------------------------------------------


def test_error_response_has_required_fields() -> None:
    err = ErrorResponse(error_code="TEST_ERROR", message="something went wrong")
    assert err.error_code == "TEST_ERROR"
    assert err.message == "something went wrong"
    assert isinstance(err.timestamp, datetime)


def test_error_response_timestamp_is_utc() -> None:
    err = ErrorResponse(error_code="X", message="y")
    assert err.timestamp.tzinfo is not None


def test_error_response_serialises_timestamp_as_string() -> None:
    err = ErrorResponse(error_code="X", message="y")
    data = err.model_dump(mode="json")
    assert isinstance(data["timestamp"], str)


def test_model_not_loaded_returns_envelope() -> None:
    class FailService:
        def predict(self, _r):
            raise ModelNotLoadedError("artifact missing")

    app.dependency_overrides[get_prediction_service] = lambda: FailService()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    resp = client.post("/predict", json=_PAYLOAD)
    assert resp.status_code == 503
    body = resp.json()
    assert body["error_code"] == "MODEL_NOT_LOADED"
    assert "artifact missing" in body["message"]
    assert "timestamp" in body

    app.dependency_overrides.clear()


def test_prediction_error_returns_envelope() -> None:
    class FailService:
        def predict(self, _r):
            raise PredictionError("pipeline exploded")

    app.dependency_overrides[get_prediction_service] = lambda: FailService()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    resp = client.post("/predict", json=_PAYLOAD)
    assert resp.status_code == 500
    body = resp.json()
    assert body["error_code"] == "PREDICTION_FAILED"
    assert "pipeline exploded" in body["message"]
    assert "timestamp" in body

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------


def test_predict_passes_without_api_key_when_not_configured() -> None:
    """When API_KEY is unset, requests pass through without any header."""
    app.dependency_overrides[get_prediction_service] = lambda: _make_stub_svc()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    resp = client.post("/predict", json=_PAYLOAD)
    assert resp.status_code == 200

    app.dependency_overrides.clear()


def test_predict_returns_401_when_api_key_configured_and_missing(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "secret-token")
    from backend.app.core import config

    config.get_settings.cache_clear()

    app.dependency_overrides[get_prediction_service] = lambda: _make_stub_svc()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/predict", json=_PAYLOAD)
    assert resp.status_code == 401

    config.get_settings.cache_clear()
    app.dependency_overrides.clear()


def test_predict_returns_401_for_wrong_api_key(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "secret-token")
    from backend.app.core import config

    config.get_settings.cache_clear()

    app.dependency_overrides[get_prediction_service] = lambda: _make_stub_svc()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/predict", json=_PAYLOAD, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401

    config.get_settings.cache_clear()
    app.dependency_overrides.clear()


def test_predict_passes_with_correct_api_key(monkeypatch) -> None:
    monkeypatch.setenv("API_KEY", "secret-token")
    from backend.app.core import config

    config.get_settings.cache_clear()

    app.dependency_overrides[get_prediction_service] = lambda: _make_stub_svc()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/predict", json=_PAYLOAD, headers={"X-API-Key": "secret-token"})
    assert resp.status_code == 200

    config.get_settings.cache_clear()
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Background-task alert creation
# ---------------------------------------------------------------------------


def test_predict_creates_alert_via_background_task() -> None:
    """Alert service's create_alert should be called as a background task."""
    created = []

    class TrackingAlertService:
        def create_alert(self, request, response):
            created.append((request, response))

        def get_recent_alerts(self, limit: int):
            return []

    app.dependency_overrides[get_prediction_service] = lambda: _make_stub_svc()
    app.dependency_overrides[get_alert_service] = lambda: TrackingAlertService()
    client = TestClient(app)

    resp = client.post("/predict", json=_PAYLOAD)
    assert resp.status_code == 200
    # TestClient runs background tasks synchronously
    assert len(created) == 1

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Model-based feature contributors (RF feature_importances_)
# ---------------------------------------------------------------------------


def _make_real_rf_pipeline(tmp_path: Path) -> PredictionService:
    """Build a small fitted Random Forest pipeline for contributor tests."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline

    from backend.app.ml.feature_map import FEATURE_COLUMNS

    rng = np.random.default_rng(42)
    n = 40
    data = {col: rng.integers(0, 10, n).astype(float) for col in FEATURE_COLUMNS}
    data["protocol_type"] = rng.choice(["tcp", "udp", "icmp"], n)
    data["service"] = rng.choice(["http", "ftp", "smtp"], n)
    data["flag"] = rng.choice(["SF", "S0", "REJ"], n)
    X = pd.DataFrame(data, columns=FEATURE_COLUMNS)
    y = rng.integers(0, 2, n)

    pipeline = Pipeline(
        [
            ("preprocessor", build_preprocessor(scale_numeric=False)),
            ("model", RandomForestClassifier(n_estimators=10, random_state=42)),
        ]
    )
    pipeline.fit(X, y)

    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"
    joblib.dump({"pipeline": pipeline, "model_name": "rf_test"}, model_path)
    metrics_path.write_text(json.dumps({"model_name": "rf_test", "metrics": {}}))
    settings = Settings(model_artifact_path=model_path, metrics_path=metrics_path)
    return PredictionService(settings=settings, model_registry=ModelRegistry(settings))


def test_rf_contributors_use_feature_importances(tmp_path: Path) -> None:
    service = _make_real_rf_pipeline(tmp_path)
    response = service.predict(_BASE_REQUEST)

    from backend.app.ml.feature_map import FEATURE_COLUMNS

    assert len(response.top_contributors) == 3
    for contributor in response.top_contributors:
        assert contributor.feature in FEATURE_COLUMNS
        assert 0.0 <= contributor.impact <= 1.0


def test_rf_contributors_sorted_descending(tmp_path: Path) -> None:
    service = _make_real_rf_pipeline(tmp_path)
    response = service.predict(_BASE_REQUEST)

    impacts = [c.impact for c in response.top_contributors]
    assert impacts == sorted(impacts, reverse=True)


def test_rf_top_contributor_has_impact_of_one(tmp_path: Path) -> None:
    service = _make_real_rf_pipeline(tmp_path)
    response = service.predict(_BASE_REQUEST)

    assert response.top_contributors[0].impact == pytest.approx(1.0, abs=0.001)


# ---------------------------------------------------------------------------
# Heuristic fallback (pipeline without feature_importances_ or coef_)
# ---------------------------------------------------------------------------


def test_heuristic_fallback_when_model_has_no_importances(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"
    joblib.dump({"pipeline": _NoPipelinePipeline(), "model_name": "minimal"}, model_path)
    metrics_path.write_text(json.dumps({"model_name": "minimal", "metrics": {}}))
    settings = Settings(model_artifact_path=model_path, metrics_path=metrics_path)
    service = PredictionService(settings=settings, model_registry=ModelRegistry(settings))

    response = service.predict(_BASE_REQUEST)
    assert len(response.top_contributors) == 3
    assert response.top_contributors[0].impact == pytest.approx(1.0, abs=0.001)
