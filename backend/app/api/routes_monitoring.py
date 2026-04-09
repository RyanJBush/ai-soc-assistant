from fastapi import APIRouter, Depends, Query

from backend.app.core.auth import require_roles
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.monitoring import MonitoringEventRecord, MonitoringEventRequest, MonitoringEventsResponse
from backend.app.services.model_observability_service import ModelObservabilityService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def get_observability_service(settings: Settings = Depends(get_settings)) -> ModelObservabilityService:
    return ModelObservabilityService(settings)


@router.post("/events", response_model=dict)
def create_monitoring_event(
    request: MonitoringEventRequest,
    service: ModelObservabilityService = Depends(get_observability_service),
    user=Depends(require_roles("analyst", "admin")),
) -> dict:
    del user
    service.record_monitoring_event(
        event_type=request.event_type,
        model_version=request.model_version,
        payload=request.payload,
    )
    return {"status": "accepted"}


@router.get("/events", response_model=MonitoringEventsResponse)
def get_monitoring_events(
    limit: int = Query(default=20, ge=1, le=200),
    service: ModelObservabilityService = Depends(get_observability_service),
    user=Depends(require_roles("analyst", "admin")),
) -> MonitoringEventsResponse:
    del user
    rows = service.recent_monitoring_events(limit=limit)
    return MonitoringEventsResponse(events=[MonitoringEventRecord(**row) for row in rows])
