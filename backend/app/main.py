import logging
from contextvars import ContextVar
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_model import router as model_router
from backend.app.api.routes_predict import router as predict_router
from backend.app.core.config import get_settings
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.core.logging import configure_logging
from backend.app.schemas.errors import ErrorResponse

configure_logging()
logger = logging.getLogger(__name__)

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

app = FastAPI(title="AI SOC Assistant API", version="0.3.0")
app.include_router(health_router)
app.include_router(model_router)
app.include_router(predict_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:12]}")
    request_id_ctx.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    settings = get_settings()
    response.headers["Access-Control-Allow-Origin"] = settings.cors_allowed_origins
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, X-Request-ID"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError) -> JSONResponse:
    logger.warning("Model not loaded: %s", exc)
    body = ErrorResponse(error_code=ModelNotLoadedError.error_code, message=str(exc))
    return JSONResponse(status_code=503, content=body.model_dump(mode="json"))


@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    logger.exception("Prediction error: %s", exc)
    body = ErrorResponse(error_code=PredictionError.error_code, message=str(exc))
    return JSONResponse(status_code=500, content=body.model_dump(mode="json"))
