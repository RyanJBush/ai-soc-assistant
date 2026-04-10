from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app.api.routes_predict import get_alert_service, get_prediction_service
from backend.app.core.config import Settings
from backend.app.main import app
from backend.tests.conftest import auth_headers
from backend.app.schemas.inference import InferenceResponse, TopContributor
from backend.app.services.alert_service import AlertService


class DeterministicPredictionService:
    def predict(self, _request):
        return InferenceResponse(
            prediction_label="malicious",
            malicious_probability=0.91,
            confidence=0.91,
            risk_level="high",
            top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
            explain_method="heuristic",
            model_version="phase6-test-model",
            timestamp=datetime(2026, 4, 7, tzinfo=timezone.utc),
        )


_PAYLOAD = {
    "duration": 0,
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 200,
    "dst_bytes": 400,
    "count": 5,
    "srv_count": 5,
    "serror_rate": 0.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 20,
    "dst_host_srv_count": 20,
}


def _client() -> TestClient:
    return TestClient(app)


def _temp_alert_service(tmp_path: Path) -> AlertService:
    settings = Settings(sqlite_db_path=tmp_path / "phase6-alerts.db", alert_logging_enabled=True)
    return AlertService(settings)


def test_health_endpoint_contract() -> None:
    response = _client().get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info_endpoint_contract() -> None:
    metrics = {
        "model_name": "phase6-model",
        "selected_features": ["duration", "src_bytes"],
        "training_rows": 1200,
        "test_rows": 400,
        "metrics": {"precision": 0.9, "recall": 0.88},
    }
    registry = MagicMock()
    registry.load_metrics.return_value = metrics

    with patch("backend.app.api.routes_model.get_model_registry", return_value=registry):
        client = _client()
        response = client.get("/model-info", headers=auth_headers(client, "viewer", "viewer123!"))

    assert response.status_code == 200
    body = response.json()
    assert body["model_name"] == "phase6-model"
    assert body["model_version"] == "phase6-model"
    assert body["training_rows"] == 1200


def test_predict_endpoint_contract_and_payload_shape() -> None:
    app.dependency_overrides[get_prediction_service] = lambda: DeterministicPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: AlertService(Settings(alert_logging_enabled=False))

    client = _client()
    response = client.post("/predict", json=_PAYLOAD, headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    assert body["prediction_label"] == "malicious"
    assert body["risk_level"] == "high"
    assert body["model_version"] == "phase6-test-model"

    app.dependency_overrides.clear()


def test_predict_rejects_invalid_payload() -> None:
    client = _client()
    response = client.post("/predict", json={"duration": -1, "protocol_type": "ftp"}, headers=auth_headers(client))
    assert response.status_code == 422


def test_alert_logging_and_recent_alert_retrieval(tmp_path: Path) -> None:
    app.dependency_overrides[get_prediction_service] = lambda: DeterministicPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: _temp_alert_service(tmp_path)

    client = _client()
    predict_response = client.post("/predict", json=_PAYLOAD, headers=auth_headers(client))
    assert predict_response.status_code == 200

    alerts_response = client.get("/alerts/recent?limit=5", headers=auth_headers(client, "viewer", "viewer123!"))
    assert alerts_response.status_code == 200
    body = alerts_response.json()
    assert len(body["alerts"]) == 1
    assert body["alerts"][0]["prediction_label"] == "malicious"
    assert body["alerts"][0]["risk_level"] == "high"

    app.dependency_overrides.clear()


def test_alert_recent_respects_limit(tmp_path: Path) -> None:
    app.dependency_overrides[get_prediction_service] = lambda: DeterministicPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: _temp_alert_service(tmp_path)

    client = _client()
    for _ in range(3):
        response = client.post("/predict", json=_PAYLOAD, headers=auth_headers(client))
        assert response.status_code == 200

    alerts_response = client.get("/alerts/recent?limit=2", headers=auth_headers(client, "viewer", "viewer123!"))
    assert alerts_response.status_code == 200
    assert len(alerts_response.json()["alerts"]) == 2

    app.dependency_overrides.clear()
