from datetime import datetime

from pydantic import BaseModel


class ModelLineage(BaseModel):
    artifact_path: str
    artifact_sha256: str
    metrics_path: str
    metrics_sha256: str
    registered_at: datetime | str | None = None


class ModelThresholds(BaseModel):
    malicious_decision_threshold: float
    risk_threshold_medium: float
    risk_threshold_high: float
    risk_threshold_critical: float


class MonitoringHookInfo(BaseModel):
    monitoring_endpoint: str
    supported_event_types: list[str]


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    selected_features: list[str]
    training_rows: int
    test_rows: int
    metrics: dict[str, float]
    thresholds: ModelThresholds
    lineage: ModelLineage
    monitoring: MonitoringHookInfo
