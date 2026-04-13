from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.api.routes_predict import get_alert_service, get_prediction_service
from backend.app.core.config import Settings
from backend.app.main import app
from backend.app.schemas.inference import InferenceResponse, TopContributor
from backend.app.services.alert_service import AlertService
from backend.tests.conftest import auth_headers


class StubPredictionService:
    def predict(self, _request):
        return InferenceResponse(
            prediction_label="malicious",
            malicious_probability=0.88,
            confidence=0.88,
            risk_level="high",
            top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
            explain_method="heuristic",
            model_version="e2e-model",
            timestamp=datetime.now(tz=timezone.utc),
        )


_PAYLOAD = {
    "duration": 0,
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 120,
    "dst_bytes": 800,
    "count": 7,
    "srv_count": 7,
    "serror_rate": 0.2,
    "same_srv_rate": 0.9,
    "dst_host_count": 14,
    "dst_host_srv_count": 14,
}


def test_e2e_login_score_review_change_status(tmp_path):
    app.dependency_overrides[get_prediction_service] = lambda: StubPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: AlertService(Settings(sqlite_db_path=tmp_path / "e2e.db"))

    client = TestClient(app)
    analyst = auth_headers(client, "analyst", "analyst123!")
    viewer = auth_headers(client, "viewer", "viewer123!")

    score_resp = client.post("/predict", json=_PAYLOAD, headers=analyst)
    assert score_resp.status_code == 200

    recent_resp = client.get("/alerts/recent?page_size=5&page=1", headers=viewer)
    assert recent_resp.status_code == 200
    alert_id = recent_resp.json()["alerts"][0]["id"]

    detail_resp = client.get(f"/alerts/{alert_id}", headers=viewer)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["alert"]["status"] == "new"

    status_resp = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": "acknowledged"},
        headers=analyst,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["alert"]["status"] == "acknowledged"

    app.dependency_overrides.clear()
