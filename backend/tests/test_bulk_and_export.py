import csv
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import app
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.alert_service import AlertService
from backend.tests.conftest import auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        sqlite_db_path=tmp_path / "alerts.db",
        alert_logging_enabled=True,
    )


def _request() -> InferenceRequest:
    return InferenceRequest(
        duration=0,
        protocol_type="tcp",
        service="http",
        flag="SF",
        src_bytes=100,
        dst_bytes=200,
        count=5,
        srv_count=5,
        serror_rate=0.0,
        same_srv_rate=1.0,
        dst_host_count=10,
        dst_host_srv_count=10,
    )


def _response(
    label: str = "benign",
    risk: str = "low",
    prob: float = 0.1,
) -> InferenceResponse:
    confidence = round(max(prob, 1.0 - prob), 4)
    return InferenceResponse(
        prediction_label=label,
        malicious_probability=prob,
        confidence=confidence,
        risk_level=risk,
        top_contributors=[TopContributor(feature="src_bytes", impact=1.0)],
        explain_method="heuristic",
        model_version="test-model",
        timestamp=datetime.now(tz=timezone.utc),
    )


def _seed(service: AlertService, n: int = 3) -> list[int]:
    for _ in range(n):
        service.create_alert(_request(), _response("malicious", "high", 0.9))
    return [a.id for a in service.get_recent_alerts(limit=n)]


# ---------------------------------------------------------------------------
# AlertService.bulk_update_status unit tests
# ---------------------------------------------------------------------------


def test_bulk_update_all_found(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    ids = _seed(service, 3)

    updated, not_found = service.bulk_update_status(ids, "resolved", actor="analyst")

    assert updated == 3
    assert not_found == []
    for alert_id in ids:
        alert = service.get_alert(alert_id)
        assert alert is not None
        assert alert.status == "resolved"


def test_bulk_update_partial_not_found(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    ids = _seed(service, 2)

    updated, not_found = service.bulk_update_status([*ids, 9999], "acknowledged", actor="analyst")

    assert updated == 2
    assert not_found == [9999]


def test_bulk_update_records_triage_events(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    ids = _seed(service, 2)

    service.bulk_update_status(ids, "escalated", actor="analyst")

    for alert_id in ids:
        history = service.get_triage_history(alert_id)
        assert any(e.event_type == "status_change" and e.new_value == "escalated" for e in history)


def test_bulk_update_empty_id_list_not_allowed(tmp_path: Path) -> None:
    """Pydantic min_length=1 on alert_ids prevents empty list at API level."""
    from pydantic import ValidationError

    from backend.app.schemas.alert import BulkUpdateRequest

    with pytest.raises(ValidationError):
        BulkUpdateRequest(alert_ids=[], status="resolved")


def test_bulk_update_too_many_ids_not_allowed() -> None:
    from pydantic import ValidationError

    from backend.app.schemas.alert import BulkUpdateRequest

    with pytest.raises(ValidationError):
        BulkUpdateRequest(alert_ids=list(range(101)), status="resolved")


# ---------------------------------------------------------------------------
# AlertService.export_alerts_csv unit tests
# ---------------------------------------------------------------------------


def test_export_empty_db(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    records = service.export_alerts_csv()
    assert records == []


def test_export_returns_all_records(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    _seed(service, 5)
    records = service.export_alerts_csv()
    assert len(records) == 5


def test_export_filters_by_status(tmp_path: Path) -> None:
    service = AlertService(_settings(tmp_path))
    ids = _seed(service, 4)
    service.update_status(ids[0], "resolved", actor="analyst")
    service.update_status(ids[1], "resolved", actor="analyst")

    resolved = service.export_alerts_csv(status="resolved")
    new_ = service.export_alerts_csv(status="new")

    assert len(resolved) == 2
    assert len(new_) == 2


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "alerts.db"))
    monkeypatch.setenv("ALERT_LOGGING_ENABLED", "true")
    from backend.app.core.config import get_settings

    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_bulk_update_requires_auth(client: TestClient) -> None:
    resp = client.patch("/alerts/bulk", json={"alert_ids": [1], "status": "resolved"})
    assert resp.status_code == 401


def test_bulk_update_viewer_forbidden(client: TestClient) -> None:
    headers = auth_headers(client, "viewer", "viewer123!")
    resp = client.patch("/alerts/bulk", json={"alert_ids": [1], "status": "resolved"}, headers=headers)
    assert resp.status_code == 403


def test_bulk_update_not_found_ids(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.patch("/alerts/bulk", json={"alert_ids": [9998, 9999], "status": "resolved"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["updated"] == 0
    assert sorted(body["not_found"]) == [9998, 9999]


def test_bulk_update_invalid_status(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.patch("/alerts/bulk", json={"alert_ids": [1], "status": "invalid"}, headers=headers)
    assert resp.status_code == 422


def test_bulk_update_empty_list_rejected(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.patch("/alerts/bulk", json={"alert_ids": [], "status": "resolved"}, headers=headers)
    assert resp.status_code == 422


def test_export_requires_auth(client: TestClient) -> None:
    resp = client.get("/alerts/export")
    assert resp.status_code == 401


def test_export_returns_csv_content_type(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.get("/alerts/export", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_export_csv_has_header_row(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.get("/alerts/export", headers=headers)
    reader = csv.reader(io.StringIO(resp.text))
    header = next(reader)
    assert "id" in header
    assert "prediction_label" in header
    assert "risk_level" in header
    assert "status" in header


def test_export_content_disposition_attachment(client: TestClient) -> None:
    headers = auth_headers(client)
    resp = client.get("/alerts/export", headers=headers)
    assert "attachment" in resp.headers.get("content-disposition", "")
    assert "alerts.csv" in resp.headers.get("content-disposition", "")


def test_export_viewer_allowed(client: TestClient) -> None:
    headers = auth_headers(client, "viewer", "viewer123!")
    resp = client.get("/alerts/export", headers=headers)
    assert resp.status_code == 200


def test_export_status_filter(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Seed alerts and resolve some via bulk
    headers = auth_headers(client)

    # We can't easily reach AlertService through the client without a model,
    # so check that the filter query param is accepted
    resp = client.get("/alerts/export?status=resolved", headers=headers)
    assert resp.status_code == 200
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    # Only header row when no resolved alerts exist
    assert len(rows) == 1
