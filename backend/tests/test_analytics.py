from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import app
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.alert_service import AlertService
from backend.app.services.analytics_service import AnalyticsService
from backend.tests.conftest import auth_headers


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


def _seed_alerts(service: AlertService) -> None:
    service.create_alert(_request(), _response("benign", "low", 0.1))
    service.create_alert(_request(), _response("malicious", "high", 0.9))
    service.create_alert(_request(), _response("malicious", "critical", 0.95))


# ---------------------------------------------------------------------------
# AnalyticsService unit tests
# ---------------------------------------------------------------------------


def test_analytics_empty_db(tmp_path: Path) -> None:
    service = AnalyticsService(_settings(tmp_path))
    result = service.get_analytics(days=14)
    assert result.total_alerts == 0
    assert result.malicious_count == 0
    assert result.benign_count == 0
    assert result.open_count == 0
    assert result.malicious_rate == 0.0
    assert result.avg_resolution_hours is None
    assert result.by_risk_level == {"low": 0, "medium": 0, "high": 0, "critical": 0}
    assert result.by_status == {"new": 0, "acknowledged": 0, "escalated": 0, "resolved": 0}
    assert result.alert_volume_by_day == []


def test_analytics_totals(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    assert result.total_alerts == 3
    assert result.malicious_count == 2
    assert result.benign_count == 1
    assert abs(result.malicious_rate - 2 / 3) < 0.001


def test_analytics_by_risk_level(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    assert result.by_risk_level["low"] == 1
    assert result.by_risk_level["high"] == 1
    assert result.by_risk_level["critical"] == 1
    assert result.by_risk_level["medium"] == 0


def test_analytics_by_status_all_new(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    assert result.by_status["new"] == 3
    assert result.by_status["resolved"] == 0
    assert result.open_count == 3


def test_analytics_open_count_excludes_resolved(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    alerts = alert_service.get_recent_alerts(limit=10)
    alert_service.update_status(alerts[0].id, "resolved", actor="analyst")

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    assert result.open_count == 2
    assert result.by_status["resolved"] == 1


def test_analytics_avg_resolution_hours(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    alerts = alert_service.get_recent_alerts(limit=10)
    alert_service.update_status(alerts[0].id, "resolved", actor="analyst")

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    # Resolution happened almost immediately so hours should be close to 0
    assert result.avg_resolution_hours is not None
    assert result.avg_resolution_hours >= 0.0


def test_analytics_volume_by_day_today(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    service = AnalyticsService(settings)
    result = service.get_analytics(days=14)

    assert len(result.alert_volume_by_day) >= 1
    total_volume = sum(d.count for d in result.alert_volume_by_day)
    assert total_volume == 3


def test_analytics_days_parameter_respected(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    alert_service = AlertService(settings)
    _seed_alerts(alert_service)

    service = AnalyticsService(settings)
    result = service.get_analytics(days=1)

    # All alerts inserted today, so volume should still be 3 with days=1
    total_volume = sum(d.count for d in result.alert_volume_by_day)
    assert total_volume == 3


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "alerts.db"))
    monkeypatch.setenv("ALERT_LOGGING_ENABLED", "true")
    # Clear the settings cache so the monkeypatched env is picked up
    from backend.app.core.config import get_settings

    get_settings.cache_clear()
    yield TestClient(app)
    get_settings.cache_clear()


def test_analytics_endpoint_requires_auth(client: TestClient) -> None:
    response = client.get("/analytics")
    assert response.status_code == 401


def test_analytics_endpoint_viewer_allowed(client: TestClient) -> None:
    headers = auth_headers(client, "viewer", "viewer123!")
    response = client.get("/analytics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "malicious_rate" in data
    assert "by_risk_level" in data
    assert "by_status" in data
    assert "alert_volume_by_day" in data


def test_analytics_endpoint_days_param(client: TestClient) -> None:
    headers = auth_headers(client, "analyst", "analyst123!")
    response = client.get("/analytics?days=7", headers=headers)
    assert response.status_code == 200
    assert response.json()["days"] == 7


def test_analytics_endpoint_days_out_of_range(client: TestClient) -> None:
    headers = auth_headers(client, "analyst", "analyst123!")
    response = client.get("/analytics?days=0", headers=headers)
    assert response.status_code == 422


def test_analytics_endpoint_days_max(client: TestClient) -> None:
    headers = auth_headers(client, "analyst", "analyst123!")
    response = client.get("/analytics?days=91", headers=headers)
    assert response.status_code == 422


def test_analytics_endpoint_schema(client: TestClient) -> None:
    headers = auth_headers(client)
    response = client.get("/analytics", headers=headers)
    data = response.json()
    assert isinstance(data["total_alerts"], int)
    assert isinstance(data["malicious_count"], int)
    assert isinstance(data["benign_count"], int)
    assert isinstance(data["open_count"], int)
    assert isinstance(data["malicious_rate"], float)
    assert isinstance(data["by_risk_level"], dict)
    assert isinstance(data["by_status"], dict)
    assert isinstance(data["alert_volume_by_day"], list)
    # All risk levels present
    for level in ("low", "medium", "high", "critical"):
        assert level in data["by_risk_level"]
    # All statuses present
    for status in ("new", "acknowledged", "escalated", "resolved"):
        assert status in data["by_status"]
