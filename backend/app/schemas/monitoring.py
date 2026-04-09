from datetime import datetime

from pydantic import BaseModel, Field


class MonitoringEventRequest(BaseModel):
    event_type: str = Field(pattern=r"^[a-zA-Z0-9_.-]{3,64}$")
    model_version: str
    payload: dict


class MonitoringEventRecord(BaseModel):
    id: int
    event_type: str
    model_version: str
    payload: dict
    created_at: datetime | str


class MonitoringEventsResponse(BaseModel):
    events: list[MonitoringEventRecord]
