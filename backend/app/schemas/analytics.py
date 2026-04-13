from pydantic import BaseModel, Field


class DailyVolume(BaseModel):
    date: str
    count: int
    malicious: int


class AnalyticsResponse(BaseModel):
    days: int = Field(ge=1)
    total_alerts: int = Field(ge=0)
    malicious_count: int = Field(ge=0)
    benign_count: int = Field(ge=0)
    open_count: int = Field(ge=0)
    malicious_rate: float = Field(ge=0.0, le=1.0)
    avg_resolution_hours: float | None = Field(default=None)
    by_risk_level: dict[str, int]
    by_status: dict[str, int]
    alert_volume_by_day: list[DailyVolume]
