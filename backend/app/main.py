import logging
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api.routes_admin import router as admin_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_model import router as model_router
from backend.app.api.routes_monitoring import router as monitoring_router
from backend.app.api.routes_predict import router as predict_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import AlertPersistenceError, ModelNotLoadedError, PredictionError
from backend.app.core.logging import configure_logging, get_request_id, set_request_id
from backend.app.core.rate_limit import build_rate_limiter
from backend.app.schemas.errors import ErrorResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
rate_limiter = build_rate_limiter(settings)

app = FastAPI(title="AI SOC Assistant API", version="0.5.0")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(model_router)
app.include_router(predict_router)
app.include_router(admin_router)
app.include_router(monitoring_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:12]}")
    set_request_id(request_id)
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    if not rate_limiter.allow(key):
        return error_response(
            request,
            status_code=429,
            error_code="RATE_LIMITED",
            message="Too many requests",
        )
    return await call_next(request)


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = settings.cors_allowed_origins
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Request-ID, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


def error_response(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    message: str,
) -> JSONResponse:
    body = ErrorResponse(
        error_code=error_code,
        message=message,
        request_id=getattr(request.state, "request_id", get_request_id()),
        path=request.url.path,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError) -> JSONResponse:
    logger.warning("model_not_loaded", extra={"request_id": get_request_id()})
    return error_response(
        request,
        status_code=503,
        error_code=ModelNotLoadedError.error_code,
        message=str(exc),
    )


@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    logger.exception("prediction_failed")
    return error_response(
        request,
        status_code=500,
        error_code=PredictionError.error_code,
        message=str(exc),
    )


@app.exception_handler(AlertPersistenceError)
async def alert_persistence_error_handler(request: Request, exc: AlertPersistenceError) -> JSONResponse:
    logger.exception("alert_persistence_failed")
    return error_response(
        request,
        status_code=500,
        error_code=AlertPersistenceError.error_code,
        message=str(exc),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_code = f"HTTP_{exc.status_code}"
    return error_response(
        request,
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return error_response(
        request,
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
        message="Unexpected server error",
    )
