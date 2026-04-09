from backend.app.core.config import Settings
from backend.app.schemas.inference import InferenceRequest
from backend.app.services.prediction_service import PredictionService


class StubRegistry:
    def load_model(self):
        class Pipeline:
            def predict_proba(self, _frame):
                return [[0.45, 0.55]]

        return {"pipeline": Pipeline(), "model_name": "stub"}


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


def test_prediction_uses_configurable_decision_threshold() -> None:
    settings = Settings(malicious_decision_threshold=0.6)
    service = PredictionService(settings=settings, model_registry=StubRegistry())

    result = service.predict(_request())
    assert result.prediction_label == "benign"


def test_prediction_uses_configurable_risk_thresholds() -> None:
    settings = Settings(
        malicious_decision_threshold=0.5,
        risk_threshold_medium=0.3,
        risk_threshold_high=0.5,
        risk_threshold_critical=0.9,
    )
    service = PredictionService(settings=settings, model_registry=StubRegistry())

    result = service.predict(_request())
    assert result.risk_level == "high"
