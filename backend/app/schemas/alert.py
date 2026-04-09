from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AlertStatus = Literal["new", "acknowledged", "escalated", "resolved"]


class AlertNote(BaseModel):
    id: int
    alert_id: int
    author: str
    note: str
    created_at: datetime


class AlertRecord(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime | str
    prediction_label: str
    confidence: float
    risk_level: str
    malicious_probability: float | None = None
    model_version: str | None = None
    status: AlertStatus = "new"
    assigned_to: str | None = None
    top_contributors: list[dict] = Field(default_factory=list)
    input_snapshot: dict


class AlertDetailResponse(BaseModel):
    alert: AlertRecord
    notes: list[AlertNote]


class RecentAlertsResponse(BaseModel):
    alerts: list[AlertRecord]
    total: int = 0
    page: int = 1
    page_size: int = 20


class UpdateAlertStatusRequest(BaseModel):
    status: AlertStatus


class AssignAlertRequest(BaseModel):
    assigned_to: str


class AddAlertNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)
