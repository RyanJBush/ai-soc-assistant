from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_artifact_path: Path = Path("backend/data/artifacts/model.joblib")
    metrics_path: Path = Path("backend/data/artifacts/metrics.json")
    feature_schema_path: Path = Path("backend/data/artifacts/feature_schema.json")

    alert_logging_enabled: bool = True
    sqlite_db_path: Path = Path("backend/data/artifacts/alerts.db")
    database_url: str | None = None
    recent_alerts_limit: int = Field(default=20, ge=1, le=200)

    malicious_decision_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_threshold_medium: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_threshold_high: float = Field(default=0.8, ge=0.0, le=1.0)
    risk_threshold_critical: float = Field(default=0.93, ge=0.0, le=1.0)

    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173"

    auth_enabled: bool = True
    jwt_secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    demo_users_json: str = (
        '[{"username":"admin","password":"admin123!","role":"admin"},'
        '{"username":"analyst","password":"analyst123!","role":"analyst"},'
        '{"username":"viewer","password":"viewer123!","role":"viewer"}]'
    )

    rate_limit_per_minute: int = Field(default=120, ge=10, le=5000)
    rate_limit_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    redis_rate_limit_prefix: str = "ai_soc:ratelimit"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":

        if not (self.risk_threshold_medium <= self.risk_threshold_high <= self.risk_threshold_critical):
            raise ValueError("Risk thresholds must satisfy medium <= high <= critical")

        if self.app_env.lower() == "production":
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in production")
            if self.auth_enabled and len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")

        if self.rate_limit_backend not in {"memory", "redis"}:
            raise ValueError("RATE_LIMIT_BACKEND must be one of: memory, redis")

        if self.rate_limit_backend == "redis" and not self.redis_url:
            raise ValueError("REDIS_URL is required when RATE_LIMIT_BACKEND=redis")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
