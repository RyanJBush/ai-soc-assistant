from datetime import datetime, timezone

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    role: str


class UserPrincipal(BaseModel):
    username: str
    role: str


class AuthEvent(BaseModel):
    action: str
    username: str
    outcome: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
