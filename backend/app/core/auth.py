import logging

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key_header: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Dependency that enforces API-key authentication when ``API_KEY`` is set.

    If ``settings.api_key`` is *None* (the default), the check is skipped so
    deployments without authentication continue to work unchanged.
    """
    if settings.api_key is None:
        return
    if api_key_header != settings.api_key:
        logger.warning("Rejected request: invalid or missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
