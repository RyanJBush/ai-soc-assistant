from fastapi import APIRouter, Depends

from backend.app.core.auth import require_roles
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.model_info import (
    ExplainabilityInfo,
    ModelInfoResponse,
    ModelLineage,
    ModelThresholds,
    MonitoringHookInfo,
)
from backend.app.services.model_observability_service import ModelObservabilityService
from backend.app.services.model_registry import get_model_registry

router = APIRouter(tags=["model"])

_EXPLAINABILITY_INFO = ExplainabilityInfo(
    supported_methods=["feature_importance", "sensitivity", "feature_importance+sensitivity", "heuristic"],
    primary_method="feature_importance+sensitivity",
    description=(
        "Feature contributions are computed by blending global model feature importances "
        "(40% weight) with local per-sample sensitivity analysis (60% weight). "
        "For models without built-in importances, sensitivity analysis alone is used. "
        "A heuristic fallback based on raw feature magnitudes is applied when both methods yield no signal."
    ),
)


def get_observability_service(settings: Settings = Depends(get_settings)) -> ModelObservabilityService:
    return ModelObservabilityService(settings)


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    dependencies=[Depends(require_roles("viewer", "analyst", "admin"))],
)
def model_info(
    settings: Settings = Depends(get_settings),
    observability_service: ModelObservabilityService = Depends(get_observability_service),
) -> ModelInfoResponse:
    registry = get_model_registry()
    metadata = registry.load_metrics()

    lineage = observability_service.get_active_model_lineage()
    if lineage is None:
        lineage = observability_service.register_active_model(metadata)

    return ModelInfoResponse(
        model_name=str(metadata.get("model_name", "unknown")),
        model_version=str(metadata.get("model_version", metadata.get("model_name", "unknown"))),
        selected_features=list(metadata.get("selected_features", [])),
        training_rows=int(metadata.get("training_rows", 0)),
        test_rows=int(metadata.get("test_rows", 0)),
        metrics=dict(metadata.get("metrics", {})),
        thresholds=ModelThresholds(
            malicious_decision_threshold=settings.malicious_decision_threshold,
            risk_threshold_medium=settings.risk_threshold_medium,
            risk_threshold_high=settings.risk_threshold_high,
            risk_threshold_critical=settings.risk_threshold_critical,
        ),
        lineage=ModelLineage(**lineage),
        monitoring=MonitoringHookInfo(
            monitoring_endpoint="/monitoring/events",
            supported_event_types=["drift.feature_shift", "performance.window", "prediction.volume"],
        ),
        explainability=_EXPLAINABILITY_INFO,
    )
