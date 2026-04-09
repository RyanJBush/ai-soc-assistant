from fastapi import APIRouter, Depends, Query

from backend.app.api.routes_auth import get_audit_service
from backend.app.core.auth import require_roles
from backend.app.schemas.audit import RecentAuditResponse
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/audit/recent",
    response_model=RecentAuditResponse,
    dependencies=[Depends(require_roles("admin"))],
)
def recent_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    audit_service: AuditService = Depends(get_audit_service),
) -> RecentAuditResponse:
    return RecentAuditResponse(records=audit_service.get_recent(limit=limit))
