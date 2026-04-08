from functools import lru_cache
from pathlib import Path

from pydantic import Field
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
    recent_alerts_limit: int = Field(default=20, ge=1, le=200)

    risk_threshold_high: float = Field(default=0.8, ge=0.5, le=1.0)

    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:5173"

    api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
