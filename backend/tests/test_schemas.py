import pytest
from pydantic import ValidationError

from backend.app.schemas.inference import InferenceRequest


def test_inference_request_accepts_valid_payload() -> None:
    payload = {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 10,
        "dst_bytes": 20,
        "count": 2,
        "srv_count": 2,
        "serror_rate": 0.0,
        "same_srv_rate": 1.0,
        "dst_host_count": 2,
        "dst_host_srv_count": 2,
    }
    parsed = InferenceRequest(**payload)
    assert parsed.protocol_type == "tcp"


def test_inference_request_rejects_invalid_rates() -> None:
    with pytest.raises(ValidationError):
        InferenceRequest(
            duration=0,
            protocol_type="tcp",
            service="http",
            flag="SF",
            src_bytes=10,
            dst_bytes=20,
            count=2,
            srv_count=2,
            serror_rate=1.4,
            same_srv_rate=1.0,
            dst_host_count=2,
            dst_host_srv_count=2,
        )
