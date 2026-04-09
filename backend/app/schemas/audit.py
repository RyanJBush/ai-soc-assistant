from datetime import datetime

from pydantic import BaseModel


class AuditRecord(BaseModel):
    id: int
    created_at: datetime | str
    actor: str
    action: str
    resource_type: str
    resource_id: str | None = None
    outcome: str
    details: dict


class RecentAuditResponse(BaseModel):
    records: list[AuditRecord]
