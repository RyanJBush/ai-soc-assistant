from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.api.routes_predict import get_alert_service, get_prediction_service
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.main import app
from backend.app.schemas.inference import InferenceResponse, TopContributor


class StubPredictionService:
    def predict(self, _request):
        return InferenceResponse(
            prediction_label="benign",
            malicious_probability=0.1,
            confidence=0.9,
            risk_level="low",
            top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
            model_version="stub-model",
            timestamp=datetime.now(tz=timezone.utc),
        )


class StubAlertService:
    def create_alert(self, request, response):
        return None

    def get_recent_alerts(self, limit: int):
        return []


def test_predict_endpoint_returns_structured_response() -> None:
    app.dependency_overrides[get_prediction_service] = lambda: StubPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()

    client = TestClient(app)
    payload = {
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

    response = client.post("/predict", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["prediction_label"] == "benign"
    assert body["risk_level"] == "low"
    assert body["model_version"] == "stub-model"
    assert isinstance(body["top_contributors"], list)

    app.dependency_overrides.clear()


def test_predict_endpoint_returns_503_when_model_not_loaded() -> None:
    class ModelNotLoadedPredictionService:
        def predict(self, _request):
            raise ModelNotLoadedError("No model artifact found")

    app.dependency_overrides[get_prediction_service] = lambda: ModelNotLoadedPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()

    client = TestClient(app)
    payload = {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 0,
        "dst_bytes": 0,
        "count": 1,
        "srv_count": 1,
        "serror_rate": 0.0,
        "same_srv_rate": 1.0,
        "dst_host_count": 1,
        "dst_host_srv_count": 1,
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 503
    assert "No model artifact found" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_predict_endpoint_returns_500_on_prediction_error() -> None:
    class FailingPredictionService:
        def predict(self, _request):
            raise PredictionError("Internal pipeline failure")

    app.dependency_overrides[get_prediction_service] = lambda: FailingPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()

    client = TestClient(app)
    payload = {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 0,
        "dst_bytes": 0,
        "count": 1,
        "srv_count": 1,
        "serror_rate": 0.0,
        "same_srv_rate": 1.0,
        "dst_host_count": 1,
        "dst_host_srv_count": 1,
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 500
    assert "Internal pipeline failure" in response.json()["detail"]

    app.dependency_overrides.clear()


def test_predict_endpoint_returns_422_for_invalid_payload() -> None:
    client = TestClient(app)
    response = client.post("/predict", json={"duration": -1, "protocol_type": "ftp"})
    assert response.status_code == 422


def test_recent_alerts_endpoint_shape() -> None:
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    response = client.get("/alerts/recent?limit=5")
    assert response.status_code == 200
    assert response.json() == {"alerts": []}

    app.dependency_overrides.clear()


def test_recent_alerts_default_limit_is_within_bounds() -> None:
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    response = client.get("/alerts/recent")
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_recent_alerts_rejects_limit_below_minimum() -> None:
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    response = client.get("/alerts/recent?limit=0")
    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_recent_alerts_rejects_limit_above_maximum() -> None:
    app.dependency_overrides[get_alert_service] = lambda: StubAlertService()
    client = TestClient(app)

    response = client.get("/alerts/recent?limit=201")
    assert response.status_code == 422

    app.dependency_overrides.clear()
