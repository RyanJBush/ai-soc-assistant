import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.core.auth import verify_api_key
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.alert import RecentAlertsResponse
from backend.app.schemas.inference import InferenceRequest, InferenceResponse
from backend.app.services.alert_service import AlertService
from backend.app.services.model_registry import get_model_registry
from backend.app.services.prediction_service import PredictionService

router = APIRouter(tags=["inference"], dependencies=[Depends(verify_api_key)])
logger = logging.getLogger(__name__)


def get_prediction_service(
    settings: Settings = Depends(get_settings),
) -> PredictionService:
    return PredictionService(settings=settings, model_registry=get_model_registry())


def get_alert_service(settings: Settings = Depends(get_settings)) -> AlertService:
    return AlertService(settings=settings)


@router.post("/predict", response_model=InferenceResponse)
def predict(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PredictionService = Depends(get_prediction_service),
    alert_service: AlertService = Depends(get_alert_service),
) -> InferenceResponse:
    logger.info(
        "predict request: protocol=%s service=%s flag=%s src_bytes=%d dst_bytes=%d",
        request.protocol_type,
        request.service,
        request.flag,
        request.src_bytes,
        request.dst_bytes,
    )
    response = prediction_service.predict(request)
    background_tasks.add_task(alert_service.create_alert, request=request, response=response)
    logger.info(
        "predict response: label=%s risk=%s confidence=%.4f model=%s",
        response.prediction_label,
        response.risk_level,
        response.confidence,
        response.model_version,
    )
    return response


@router.get("/alerts/recent", response_model=RecentAlertsResponse)
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=200),
    alert_service: AlertService = Depends(get_alert_service),
) -> RecentAlertsResponse:
    return RecentAlertsResponse(alerts=alert_service.get_recent_alerts(limit=limit))
