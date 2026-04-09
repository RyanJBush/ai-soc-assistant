from fastapi.testclient import TestClient

from backend.app.main import app
from backend.tests.conftest import auth_headers


def test_monitoring_event_round_trip() -> None:
    client = TestClient(app)
    analyst = auth_headers(client, "analyst", "analyst123!")

    create_resp = client.post(
        "/monitoring/events",
        json={
            "event_type": "drift.feature_shift",
            "model_version": "test-model",
            "payload": {"psi": 0.21, "feature": "src_bytes"},
        },
        headers=analyst,
    )
    assert create_resp.status_code == 200

    list_resp = client.get("/monitoring/events?limit=5", headers=analyst)
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert len(body["events"]) >= 1
    assert body["events"][0]["event_type"] in {"drift.feature_shift", "performance.window", "prediction.volume"}
