import pytest
from pydantic import ValidationError

from backend.app.schemas.alert import RecentAlertsResponse
from backend.app.schemas.inference import InferenceRequest, TopContributor
from backend.app.schemas.model_info import ModelInfoResponse, ModelLineage, ModelThresholds, MonitoringHookInfo

_VALID = dict(
    duration=0,
    protocol_type="tcp",
    service="http",
    flag="SF",
    src_bytes=10,
    dst_bytes=20,
    count=2,
    srv_count=2,
    serror_rate=0.0,
    same_srv_rate=1.0,
    dst_host_count=2,
    dst_host_srv_count=2,
)


def test_inference_request_accepts_valid_payload() -> None:
    parsed = InferenceRequest(**_VALID)
    assert parsed.protocol_type == "tcp"


def test_inference_request_rejects_invalid_rates() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "serror_rate": 1.4})


def test_inference_request_rejects_negative_duration() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "duration": -1})


def test_inference_request_rejects_negative_src_bytes() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "src_bytes": -10})


def test_inference_request_rejects_negative_dst_bytes() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "dst_bytes": -1})


def test_inference_request_rejects_negative_count() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "count": -1})


def test_inference_request_rejects_invalid_protocol_type() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "protocol_type": "ftp"})


def test_inference_request_accepts_all_protocol_types() -> None:
    for proto in ("tcp", "udp", "icmp"):
        parsed = InferenceRequest(**{**_VALID, "protocol_type": proto})
        assert parsed.protocol_type == proto


def test_inference_request_rejects_same_srv_rate_above_one() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "same_srv_rate": 1.1})


def test_inference_request_accepts_serror_rate_boundary_values() -> None:
    InferenceRequest(**{**_VALID, "serror_rate": 0.0})
    InferenceRequest(**{**_VALID, "serror_rate": 1.0})


def test_inference_request_rejects_empty_service() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "service": ""})


def test_inference_request_rejects_service_too_long() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "service": "x" * 33})


def test_inference_request_accepts_service_at_max_length() -> None:
    parsed = InferenceRequest(**{**_VALID, "service": "x" * 32})
    assert len(parsed.service) == 32


def test_inference_request_rejects_empty_flag() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(**{**_VALID, "flag": ""})


def test_top_contributor_stores_feature_and_impact() -> None:
    contributor = TopContributor(feature="src_bytes", impact=0.75)
    assert contributor.feature == "src_bytes"
    assert contributor.impact == 0.75


def test_model_info_response_round_trips() -> None:
    info = ModelInfoResponse(
        model_name="random_forest",
        model_version="v1",
        selected_features=["duration", "src_bytes"],
        training_rows=1000,
        test_rows=200,
        metrics={"precision": 0.95, "recall": 0.93},
        thresholds=ModelThresholds(
            malicious_decision_threshold=0.5,
            risk_threshold_medium=0.5,
            risk_threshold_high=0.8,
            risk_threshold_critical=0.93,
        ),
        lineage=ModelLineage(
            artifact_path="a.joblib",
            artifact_sha256="abc",
            metrics_path="m.json",
            metrics_sha256="def",
        ),
        monitoring=MonitoringHookInfo(
            monitoring_endpoint="/monitoring/events",
            supported_event_types=["drift.feature_shift"],
        ),
    )
    assert info.model_name == "random_forest"
    assert info.metrics["precision"] == 0.95


def test_recent_alerts_response_empty() -> None:
    resp = RecentAlertsResponse(alerts=[])
    assert resp.alerts == []
