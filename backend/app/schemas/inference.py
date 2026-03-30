from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    duration: int = Field(ge=0)
    protocol_type: Literal["tcp", "udp", "icmp"]
    service: str = Field(min_length=1, max_length=32)
    flag: str = Field(min_length=1, max_length=16)
    src_bytes: int = Field(ge=0)
    dst_bytes: int = Field(ge=0)
    count: int = Field(ge=0)
    srv_count: int = Field(ge=0)
    serror_rate: float = Field(ge=0.0, le=1.0)
    same_srv_rate: float = Field(ge=0.0, le=1.0)
    dst_host_count: int = Field(ge=0)
    dst_host_srv_count: int = Field(ge=0)


class TopContributor(BaseModel):
    feature: str
    impact: float


class InferenceResponse(BaseModel):
    prediction_label: Literal["benign", "malicious"]
    malicious_probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high"]
    top_contributors: list[TopContributor]
    model_version: str
    timestamp: datetime
