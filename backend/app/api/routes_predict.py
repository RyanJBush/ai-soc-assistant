from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.schemas.alert import RecentAlertsResponse
from backend.app.schemas.inference import InferenceRequest, InferenceResponse
from backend.app.services.alert_service import AlertService
from backend.app.services.model_registry import get_model_registry
from backend.app.services.prediction_service import PredictionService

router = APIRouter(tags=["inference"])


def get_prediction_service(
    settings: Settings = Depends(get_settings),
) -> PredictionService:
    return PredictionService(settings=settings, model_registry=get_model_registry())


def get_alert_service(settings: Settings = Depends(get_settings)) -> AlertService:
    return AlertService(settings=settings)


@router.post("/predict", response_model=InferenceResponse)
def predict(
    request: InferenceRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    alert_service: AlertService = Depends(get_alert_service),
) -> InferenceResponse:
    try:
        response = prediction_service.predict(request)
        alert_service.create_alert(request=request, response=response)
        return response
    except ModelNotLoadedError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except PredictionError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/alerts/recent", response_model=RecentAlertsResponse)
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=200),
    alert_service: AlertService = Depends(get_alert_service),
) -> RecentAlertsResponse:
    return RecentAlertsResponse(alerts=alert_service.get_recent_alerts(limit=limit))
