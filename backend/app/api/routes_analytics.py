from fastapi import APIRouter, Depends, Query

from backend.app.core.auth import require_roles
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.analytics import AnalyticsResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(settings: Settings = Depends(get_settings)) -> AnalyticsService:
    return AnalyticsService(settings)


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    days: int = Query(default=14, ge=1, le=90, description="Rolling window in days"),
    service: AnalyticsService = Depends(get_analytics_service),
    user=Depends(require_roles("viewer", "analyst", "admin")),
) -> AnalyticsResponse:
    del user
    return service.get_analytics(days=days)
