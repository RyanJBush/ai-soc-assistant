from datetime import datetime, timezone
from pathlib import Path

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
            explain_method="heuristic",
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


def _service(tmp_path: Path) -> AlertService:
    return AlertService(Settings(sqlite_db_path=tmp_path / "triage.db"))


def test_triage_history_records_status_change(tmp_path: Path) -> None:
    service = _service(tmp_path)
    from backend.app.schemas.inference import InferenceRequest

    request = InferenceRequest(**{k: v for k, v in _PAYLOAD.items()})
    response = StubPredictionService().predict(request)
    service.create_alert(request, response)
    alerts = service.get_recent_alerts(limit=1)
    alert_id = alerts[0].id

    service.update_status(alert_id, "acknowledged", actor="analyst")
    history = service.get_triage_history(alert_id)

    assert len(history) == 1
    event = history[0]
    assert event.event_type == "status_change"
    assert event.new_value == "acknowledged"
    assert event.old_value == "new"
    assert event.actor == "analyst"
    assert isinstance(event.created_at, datetime)


def test_triage_history_records_assignment_change(tmp_path: Path) -> None:
    service = _service(tmp_path)
    from backend.app.schemas.inference import InferenceRequest

    request = InferenceRequest(**{k: v for k, v in _PAYLOAD.items()})
    response = StubPredictionService().predict(request)
    service.create_alert(request, response)
    alert_id = service.get_recent_alerts(limit=1)[0].id

    service.assign_alert(alert_id, "analyst-bob", actor="admin")
    history = service.get_triage_history(alert_id)

    assert len(history) == 1
    event = history[0]
    assert event.event_type == "assignment_change"
    assert event.new_value == "analyst-bob"
    assert event.old_value is None
    assert event.actor == "admin"


def test_triage_history_accumulates_multiple_events(tmp_path: Path) -> None:
    service = _service(tmp_path)
    from backend.app.schemas.inference import InferenceRequest

    request = InferenceRequest(**{k: v for k, v in _PAYLOAD.items()})
    response = StubPredictionService().predict(request)
    service.create_alert(request, response)
    alert_id = service.get_recent_alerts(limit=1)[0].id

    service.update_status(alert_id, "acknowledged", actor="analyst")
    service.assign_alert(alert_id, "analyst-bob", actor="analyst")
    service.update_status(alert_id, "escalated", actor="analyst")

    history = service.get_triage_history(alert_id)
    assert len(history) == 3
    event_types = [e.event_type for e in history]
    assert event_types == ["status_change", "assignment_change", "status_change"]


def test_triage_history_api_endpoint(tmp_path: Path) -> None:
    service = _service(tmp_path)
    app.dependency_overrides[get_prediction_service] = lambda: StubPredictionService()
    app.dependency_overrides[get_alert_service] = lambda: service

    client = TestClient(app)
    analyst_headers = auth_headers(client)

    predict_resp = client.post("/predict", json=_PAYLOAD, headers=analyst_headers)
    assert predict_resp.status_code == 200

    recent = client.get("/alerts/recent?page_size=5", headers=analyst_headers)
    alert_id = recent.json()["alerts"][0]["id"]

    client.patch(f"/alerts/{alert_id}/status", json={"status": "acknowledged"}, headers=analyst_headers)
    client.patch(f"/alerts/{alert_id}/assignment", json={"assigned_to": "analyst"}, headers=analyst_headers)

    history_resp = client.get(f"/alerts/{alert_id}/history", headers=analyst_headers)
    assert history_resp.status_code == 200
    body = history_resp.json()
    assert body["alert_id"] == alert_id
    assert len(body["events"]) == 2
    assert body["events"][0]["event_type"] == "status_change"
    assert body["events"][1]["event_type"] == "assignment_change"

    app.dependency_overrides.clear()


def test_triage_history_returns_404_for_missing_alert(tmp_path: Path) -> None:
    service = _service(tmp_path)
    app.dependency_overrides[get_alert_service] = lambda: service

    client = TestClient(app)
    viewer_headers = auth_headers(client, "viewer", "viewer123!")

    resp = client.get("/alerts/9999/history", headers=viewer_headers)
    assert resp.status_code == 404

    app.dependency_overrides.clear()
