import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import ModelNotLoadedError
from backend.app.schemas.inference import InferenceRequest
from backend.app.services.model_registry import ModelRegistry
from backend.app.services.prediction_service import PredictionService


class DummyPipeline:
    def predict_proba(self, _frame: pd.DataFrame):
        return [[0.2, 0.8]]


class MissingModelRegistry:
    def load_model(self):
        raise ModelNotLoadedError("missing model")


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


def test_prediction_service_returns_high_risk_for_high_probability(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"

    joblib.dump({"pipeline": DummyPipeline(), "model_name": "dummy"}, model_path)
    metrics_path.write_text(json.dumps({"model_name": "dummy", "metrics": {}}))

    settings = Settings(
        model_artifact_path=model_path,
        metrics_path=metrics_path,
        risk_threshold_high=0.7,
    )
    service = PredictionService(settings=settings, model_registry=ModelRegistry(settings))

    request = InferenceRequest(
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

    response = service.predict(request)
    assert response.prediction_label == "malicious"
    assert response.risk_level == "high"
    assert response.model_version == "dummy"


def test_prediction_service_re_raises_model_not_loaded() -> None:
    settings = Settings()
    service = PredictionService(settings=settings, model_registry=MissingModelRegistry())

    request = InferenceRequest(
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

    with pytest.raises(ModelNotLoadedError):
        service.predict(request)
