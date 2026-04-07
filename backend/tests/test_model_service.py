import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.schemas.inference import InferenceRequest
from backend.app.services.model_registry import ModelRegistry
from backend.app.services.prediction_service import PredictionService


class DummyPipeline:
    def predict_proba(self, _frame: pd.DataFrame):
        return [[0.2, 0.8]]


class LowRiskPipeline:
    """Returns 0.2 malicious probability — below 0.5 threshold."""

    def predict_proba(self, _frame: pd.DataFrame):
        return [[0.8, 0.2]]


class MediumRiskPipeline:
    """Returns 0.65 malicious probability — above 0.5 but below risk_threshold_high=0.8."""

    def predict_proba(self, _frame: pd.DataFrame):
        return [[0.35, 0.65]]


class FailingPipeline:
    def predict_proba(self, _frame: pd.DataFrame):
        raise RuntimeError("Simulated pipeline crash")


class MissingModelRegistry:
    def load_model(self):
        raise ModelNotLoadedError("missing model")


_BASE_REQUEST = dict(
    duration=0,
    protocol_type="tcp",
    service="http",
    flag="SF",
    src_bytes=10,
    dst_bytes=20,
    count=2,
    srv_count=2,
    serror_rate=0.1,
    same_srv_rate=1.0,
    dst_host_count=2,
    dst_host_srv_count=2,
)


def _make_service(tmp_path: Path, pipeline, *, risk_threshold_high: float = 0.8) -> PredictionService:
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"
    joblib.dump({"pipeline": pipeline, "model_name": "dummy"}, model_path)
    metrics_path.write_text(json.dumps({"model_name": "dummy", "metrics": {}}))
    settings = Settings(
        model_artifact_path=model_path,
        metrics_path=metrics_path,
        risk_threshold_high=risk_threshold_high,
    )
    return PredictionService(settings=settings, model_registry=ModelRegistry(settings))


def test_model_registry_loads_artifacts(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"

    joblib.dump({"pipeline": DummyPipeline(), "model_name": "dummy"}, model_path)
    metrics_path.write_text(json.dumps({"model_name": "dummy", "metrics": {}}))

    settings = Settings(model_artifact_path=model_path, metrics_path=metrics_path)
    registry = ModelRegistry(settings)

    model = registry.load_model()
    metrics = registry.load_metrics()

    assert model["model_name"] == "dummy"
    assert metrics["model_name"] == "dummy"


def test_model_registry_raises_when_model_file_missing(tmp_path: Path) -> None:
    settings = Settings(
        model_artifact_path=tmp_path / "nonexistent.joblib",
        metrics_path=tmp_path / "metrics.json",
    )
    with pytest.raises(ModelNotLoadedError):
        ModelRegistry(settings).load_model()


def test_model_registry_raises_when_metrics_file_missing(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    joblib.dump({"pipeline": DummyPipeline(), "model_name": "dummy"}, model_path)
    settings = Settings(
        model_artifact_path=model_path,
        metrics_path=tmp_path / "nonexistent.json",
    )
    with pytest.raises(ModelNotLoadedError):
        ModelRegistry(settings).load_metrics()


def test_prediction_service_returns_high_risk_for_high_probability(tmp_path: Path) -> None:
    service = _make_service(tmp_path, DummyPipeline(), risk_threshold_high=0.7)
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    assert response.prediction_label == "malicious"
    assert response.risk_level == "high"
    assert response.model_version == "dummy"


def test_prediction_service_re_raises_model_not_loaded() -> None:
    settings = Settings()
    service = PredictionService(settings=settings, model_registry=MissingModelRegistry())

    with pytest.raises(ModelNotLoadedError):
        service.predict(InferenceRequest(**_BASE_REQUEST))


def test_prediction_service_returns_medium_risk(tmp_path: Path) -> None:
    # 0.65 malicious probability: above 0.5 (malicious) but below 0.8 threshold
    service = _make_service(tmp_path, MediumRiskPipeline(), risk_threshold_high=0.8)
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    assert response.prediction_label == "malicious"
    assert response.risk_level == "medium"


def test_prediction_service_returns_low_risk_for_low_probability(tmp_path: Path) -> None:
    # 0.2 malicious probability: below 0.5 → benign + low
    service = _make_service(tmp_path, LowRiskPipeline())
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    assert response.prediction_label == "benign"
    assert response.risk_level == "low"


def test_prediction_service_raises_prediction_error_on_pipeline_failure(tmp_path: Path) -> None:
    service = _make_service(tmp_path, FailingPipeline())
    with pytest.raises(PredictionError):
        service.predict(InferenceRequest(**_BASE_REQUEST))


def test_prediction_service_response_has_top_contributors(tmp_path: Path) -> None:
    service = _make_service(tmp_path, DummyPipeline())
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    assert len(response.top_contributors) == 3
    features = [c.feature for c in response.top_contributors]
    assert all(f in {"src_bytes", "dst_bytes", "serror_rate", "count", "srv_count"} for f in features)
    # Contributors must be sorted by descending impact
    impacts = [c.impact for c in response.top_contributors]
    assert impacts == sorted(impacts, reverse=True)


def test_prediction_service_top_contributors_impact_in_range(tmp_path: Path) -> None:
    service = _make_service(tmp_path, DummyPipeline())
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    for contributor in response.top_contributors:
        assert 0.0 <= contributor.impact <= 1.0


def test_prediction_service_confidence_is_max_probability(tmp_path: Path) -> None:
    service = _make_service(tmp_path, DummyPipeline())
    response = service.predict(InferenceRequest(**_BASE_REQUEST))

    # DummyPipeline returns [0.2, 0.8], so confidence = max(0.2, 0.8) = 0.8
    assert response.confidence == pytest.approx(0.8, abs=0.001)
    assert response.malicious_probability == pytest.approx(0.8, abs=0.001)
