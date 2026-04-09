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
            malicious_probability=0.9,
            confidence=0.9,
            risk_level="high",
            top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
            model_version="stub-model",
            timestamp=datetime.now(tz=timezone.utc),
        )


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


def test_alert_lifecycle_assignment_and_notes(tmp_path):
    service = AlertService(Settings(sqlite_db_path=tmp_path / "workflow.db"))
    app.dependency_overrides[get_prediction_service] = lambda: StubPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: service

    client = TestClient(app)
    analyst_headers = auth_headers(client)

    predict_resp = client.post("/predict", json=_PAYLOAD, headers=analyst_headers)
    assert predict_resp.status_code == 200

    recent = client.get("/alerts/recent?page_size=10&page=1", headers=auth_headers(client, "viewer", "viewer123!"))
    assert recent.status_code == 200
    body = recent.json()
    assert body["total"] >= 1
    alert_id = body["alerts"][0]["id"]

    status_resp = client.patch(
        f"/alerts/{alert_id}/status",
        json={"status": "acknowledged"},
        headers=analyst_headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["alert"]["status"] == "acknowledged"

    assign_resp = client.patch(
        f"/alerts/{alert_id}/assignment",
        json={"assigned_to": "analyst"},
        headers=analyst_headers,
    )
    assert assign_resp.status_code == 200
    assert assign_resp.json()["alert"]["assigned_to"] == "analyst"

    note_resp = client.post(
        f"/alerts/{alert_id}/notes",
        json={"note": "Investigated source IP, escalating to IR."},
        headers=analyst_headers,
    )
    assert note_resp.status_code == 200
    assert len(note_resp.json()["notes"]) >= 1

    detail_resp = client.get(f"/alerts/{alert_id}", headers=auth_headers(client, "viewer", "viewer123!"))
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["alert"]["status"] == "acknowledged"
    assert detail["alert"]["assigned_to"] == "analyst"

    app.dependency_overrides.clear()
