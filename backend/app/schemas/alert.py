from datetime import datetime

from pydantic import BaseModel


class AlertRecord(BaseModel):
    id: int
    created_at: datetime
    prediction_label: str
    confidence: float
    risk_level: str
    input_snapshot: dict


class RecentAlertsResponse(BaseModel):
    alerts: list[AlertRecord]
