from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.core.exceptions import ModelNotLoadedError
from backend.app.main import app
from backend.tests.conftest import auth_headers

client = TestClient(app)

_FULL_METRICS = {
    "model_name": "random_forest",
    "model_version": "rf-v2",
    "selected_features": ["duration", "src_bytes", "dst_bytes"],
    "training_rows": 1000,
    "test_rows": 200,
    "metrics": {
        "precision": 0.95,
        "recall": 0.93,
        "f1_score": 0.94,
        "roc_auc": 0.98,
        "false_positive_rate": 0.02,
    },
}


def test_model_info_returns_200_with_structured_body() -> None:
    mock_registry = MagicMock()
    mock_registry.load_metrics.return_value = _FULL_METRICS

    mock_observability = MagicMock()
    mock_observability.get_active_model_lineage.return_value = {
        "artifact_path": "backend/data/artifacts/model.joblib",
        "artifact_sha256": "abc",
        "metrics_path": "backend/data/artifacts/metrics.json",
        "metrics_sha256": "def",
        "registered_at": "2026-04-09T00:00:00+00:00",
    }

    with patch("backend.app.api.routes_model.get_model_registry", return_value=mock_registry), patch(
        "backend.app.api.routes_model.get_observability_service", return_value=mock_observability
    ):
        response = client.get("/model-info", headers=auth_headers(client, "viewer", "viewer123!"))

    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "random_forest"
    assert body["model_version"] == "rf-v2"
    assert body["thresholds"]["risk_threshold_high"] == 0.8
    assert body["monitoring"]["monitoring_endpoint"] == "/monitoring/events"
    assert body["selected_features"] == ["duration", "src_bytes", "dst_bytes"]
    assert body["training_rows"] == 1000
    assert body["test_rows"] == 200
    assert body["metrics"]["precision"] == 0.95


def test_model_info_returns_503_when_model_not_loaded() -> None:
    mock_registry = MagicMock()
    mock_registry.load_metrics.side_effect = ModelNotLoadedError("No artifact found")

    mock_observability = MagicMock()
    mock_observability.get_active_model_lineage.return_value = {
        "artifact_path": "backend/data/artifacts/model.joblib",
        "artifact_sha256": "abc",
        "metrics_path": "backend/data/artifacts/metrics.json",
        "metrics_sha256": "def",
        "registered_at": "2026-04-09T00:00:00+00:00",
    }

    with patch("backend.app.api.routes_model.get_model_registry", return_value=mock_registry), patch(
        "backend.app.api.routes_model.get_observability_service", return_value=mock_observability
    ):
        response = client.get("/model-info", headers=auth_headers(client, "viewer", "viewer123!"))

    assert response.status_code == 503
    body = response.json()
    assert body["error_code"] == "MODEL_NOT_LOADED"
    assert "No artifact found" in body["message"]
