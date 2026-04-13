import csv
import io
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.app.core.auth import require_roles
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.alert import (
    AddAlertNoteRequest,
    AlertDetailResponse,
    AlertTriageHistoryResponse,
    AssignAlertRequest,
    BulkUpdateRequest,
    BulkUpdateResponse,
    RecentAlertsResponse,
    UpdateAlertStatusRequest,
)
from backend.app.schemas.auth import UserPrincipal
from backend.app.schemas.inference import InferenceRequest, InferenceResponse
from backend.app.services.alert_service import AlertService
from backend.app.services.model_registry import get_model_registry
from backend.app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inference"])


def get_prediction_service(settings: Settings = Depends(get_settings)) -> PredictionService:
    return PredictionService(settings=settings, model_registry=get_model_registry())


def get_alert_service(settings: Settings = Depends(get_settings)) -> AlertService:
    return AlertService(settings=settings)


@router.post("/predict", response_model=InferenceResponse)
def predict(
    request: InferenceRequest,
    background_tasks: BackgroundTasks,
    prediction_service: PredictionService = Depends(get_prediction_service),
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("analyst", "admin")),
) -> InferenceResponse:
    logger.info("Predict request received")
    response = prediction_service.predict(request)
    background_tasks.add_task(alert_service.create_alert, request=request, response=response, actor=user.username)
    return response


@router.get("/alerts/recent", response_model=RecentAlertsResponse)
def get_recent_alerts(
    page_size: int = Query(default=20, ge=1, le=200),
    limit: int | None = Query(default=None, ge=1, le=200),
    page: int = Query(default=1, ge=1, le=1000),
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("viewer", "analyst", "admin")),
) -> RecentAlertsResponse:
    del user
    effective_page_size = limit or page_size
    try:
        alerts, total = alert_service.query_alerts(
            limit=effective_page_size,
            page=page,
            status=status,
            assigned_to=assigned_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except (TypeError, AttributeError):
        alerts = alert_service.get_recent_alerts(limit=effective_page_size)
        total = len(alerts)

    return RecentAlertsResponse(alerts=alerts, total=total, page=page, page_size=effective_page_size)


@router.patch("/alerts/bulk", response_model=BulkUpdateResponse)
def bulk_update_alerts(
    request: BulkUpdateRequest,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("analyst", "admin")),
) -> BulkUpdateResponse:
    updated, not_found = alert_service.bulk_update_status(
        alert_ids=request.alert_ids,
        status=request.status,
        actor=user.username,
    )
    return BulkUpdateResponse(updated=updated, not_found=not_found)


_CSV_COLUMNS = [
    "id",
    "created_at",
    "prediction_label",
    "confidence",
    "risk_level",
    "malicious_probability",
    "model_version",
    "status",
    "assigned_to",
    "updated_at",
]


@router.get("/alerts/export")
def export_alerts_csv(
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("viewer", "analyst", "admin")),
) -> StreamingResponse:
    del user
    records = alert_service.export_alerts_csv(
        status=status,
        assigned_to=assigned_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(_CSV_COLUMNS)
        yield buf.getvalue()
        for record in records:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([getattr(record, col, "") for col in _CSV_COLUMNS])
            yield buf.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts.csv"},
    )


@router.get("/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert_detail(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("viewer", "analyst", "admin")),
) -> AlertDetailResponse:
    del user
    alert = alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    notes = alert_service.get_notes(alert_id)
    return AlertDetailResponse(alert=alert, notes=notes)


@router.patch("/alerts/{alert_id}/status", response_model=AlertDetailResponse)
def update_alert_status(
    alert_id: int,
    request: UpdateAlertStatusRequest,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("analyst", "admin")),
) -> AlertDetailResponse:
    alert = alert_service.update_status(alert_id, request.status, actor=user.username)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    notes = alert_service.get_notes(alert_id)
    return AlertDetailResponse(alert=alert, notes=notes)


@router.patch("/alerts/{alert_id}/assignment", response_model=AlertDetailResponse)
def assign_alert(
    alert_id: int,
    request: AssignAlertRequest,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("analyst", "admin")),
) -> AlertDetailResponse:
    alert = alert_service.assign_alert(alert_id, request.assigned_to, actor=user.username)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    notes = alert_service.get_notes(alert_id)
    return AlertDetailResponse(alert=alert, notes=notes)


@router.get("/alerts/{alert_id}/history", response_model=AlertTriageHistoryResponse)
def get_alert_history(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("viewer", "analyst", "admin")),
) -> AlertTriageHistoryResponse:
    del user
    alert = alert_service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    events = alert_service.get_triage_history(alert_id)
    return AlertTriageHistoryResponse(alert_id=alert_id, events=events)


@router.post("/alerts/{alert_id}/notes", response_model=AlertDetailResponse)
def add_alert_note(
    alert_id: int,
    request: AddAlertNoteRequest,
    alert_service: AlertService = Depends(get_alert_service),
    user: UserPrincipal = Depends(require_roles("analyst", "admin")),
) -> AlertDetailResponse:
    note = alert_service.add_note(alert_id=alert_id, author=user.username, note=request.note)
    if note is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = alert_service.get_alert(alert_id)
    assert alert is not None
    notes = alert_service.get_notes(alert_id)
    return AlertDetailResponse(alert=alert, notes=notes)

