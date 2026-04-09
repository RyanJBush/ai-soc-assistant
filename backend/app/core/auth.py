import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.auth import UserPrincipal

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def _users_from_settings(demo_users_json: str) -> dict[str, dict[str, str]]:
    data = json.loads(demo_users_json)
    users: dict[str, dict[str, str]] = {}
    for entry in data:
        users[entry["username"]] = {
            "password": entry["password"],
            "role": entry["role"],
        }
    return users


def _urlsafe_b64_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def _urlsafe_b64_decode(payload: str) -> bytes:
    padding = "=" * ((4 - len(payload) % 4) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def _sign(data: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    return _urlsafe_b64_encode(signature)


def authenticate_user(username: str, password: str, settings: Settings) -> UserPrincipal | None:
    users = _users_from_settings(settings.demo_users_json)
    user = users.get(username)
    if not user or user["password"] != password:
        return None
    return UserPrincipal(username=username, role=user["role"])


def create_access_token(user: UserPrincipal, settings: Settings) -> tuple[str, datetime]:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(tz=timezone.utc).timestamp()),
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    encoded_payload = _urlsafe_b64_encode(payload_json.encode("utf-8"))
    signature = _sign(encoded_payload, settings.jwt_secret_key)
    return f"{encoded_payload}.{signature}", expires_at


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: Settings = Depends(get_settings),
) -> UserPrincipal:
    if not settings.auth_enabled:
        return UserPrincipal(username="local-dev", role="admin")

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials.credentials
    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = _sign(encoded_payload, settings.jwt_secret_key)
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        payload = json.loads(_urlsafe_b64_decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(datetime.now(tz=timezone.utc).timestamp()):
            raise ValueError("Token expired")
    except Exception as exc:
        logger.warning("Rejected request: invalid auth token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return UserPrincipal(username=str(username), role=str(role))


def require_roles(*allowed_roles: str):
    def dependency(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return dependency
