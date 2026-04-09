from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.auth import authenticate_user, create_access_token, get_current_user
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserPrincipal
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_audit_service(settings: Settings = Depends(get_settings)) -> AuditService:
    return AuditService(settings)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    settings: Settings = Depends(get_settings),
    audit_service: AuditService = Depends(get_audit_service),
) -> TokenResponse:
    user = authenticate_user(request.username, request.password, settings)
    if user is None:
        audit_service.log_event(
            actor=request.username,
            action="auth.login",
            resource_type="auth",
            outcome="failure",
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_at = create_access_token(user, settings)
    audit_service.log_event(
        actor=user.username,
        action="auth.login",
        resource_type="auth",
        outcome="success",
        details={"role": user.role},
    )
    return TokenResponse(access_token=token, expires_at=expires_at, role=user.role)


@router.get("/me", response_model=UserPrincipal)
def me(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
    return user
