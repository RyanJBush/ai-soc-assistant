from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.alert_service import AlertService


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
        model_version="test-model",
        timestamp=datetime.now(tz=timezone.utc),
    )


def _service(tmp_path: Path, *, enabled: bool = True) -> AlertService:
    settings = Settings(
        sqlite_db_path=tmp_path / "alerts.db",
        alert_logging_enabled=enabled,
    )
    return AlertService(settings)


def test_create_alert_inserts_record(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_alert(_request(), _response("benign", "low", 0.1))

    alerts = service.get_recent_alerts(limit=10)
    assert len(alerts) == 1
    assert alerts[0].prediction_label == "benign"
    assert alerts[0].risk_level == "low"
    assert 0.0 < alerts[0].confidence <= 1.0


def test_create_alert_disabled_does_not_insert(tmp_path: Path) -> None:
    service = _service(tmp_path, enabled=False)
    service.create_alert(_request(), _response())

    alerts = service.get_recent_alerts(limit=10)
    assert alerts == []


def test_get_recent_alerts_returns_newest_first(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_alert(_request(), _response("benign", "low", 0.1))
    service.create_alert(_request(), _response("malicious", "high", 0.9))

    alerts = service.get_recent_alerts(limit=10)
    assert len(alerts) == 2
    assert alerts[0].prediction_label == "malicious"
    assert alerts[1].prediction_label == "benign"


def test_get_recent_alerts_respects_limit(tmp_path: Path) -> None:
    service = _service(tmp_path)
    for _ in range(5):
        service.create_alert(_request(), _response())

    alerts = service.get_recent_alerts(limit=3)
    assert len(alerts) == 3


def test_get_recent_alerts_empty_when_no_records(tmp_path: Path) -> None:
    service = _service(tmp_path)
    assert service.get_recent_alerts(limit=10) == []


def test_alert_record_contains_input_snapshot(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_alert(_request(), _response())

    alert = service.get_recent_alerts(limit=1)[0]
    assert isinstance(alert.input_snapshot, dict)
    assert alert.input_snapshot["protocol_type"] == "tcp"
    assert alert.input_snapshot["service"] == "http"


def test_create_alert_sets_created_at_timestamp(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_alert(_request(), _response())

    alert = service.get_recent_alerts(limit=1)[0]
    assert isinstance(alert.created_at, datetime)


def test_multiple_alerts_have_unique_ids(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_alert(_request(), _response("benign", "low", 0.2))
    service.create_alert(_request(), _response("malicious", "high", 0.9))

    alerts = service.get_recent_alerts(limit=10)
    ids = [a.id for a in alerts]
    assert len(ids) == len(set(ids))
