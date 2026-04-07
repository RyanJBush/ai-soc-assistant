from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_model import router as model_router
from backend.app.api.routes_predict import router as predict_router
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.core.logging import configure_logging
from backend.app.schemas.errors import ErrorResponse

configure_logging()

app = FastAPI(title="AI Intrusion Detection System API", version="0.2.0")
app.include_router(health_router)
app.include_router(model_router)
app.include_router(predict_router)


@app.exception_handler(ModelNotLoadedError)
async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error_code=ModelNotLoadedError.error_code,
            message=str(exc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(PredictionError)
async def prediction_error_handler(request: Request, exc: PredictionError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code=PredictionError.error_code,
            message=str(exc),
        ).model_dump(mode="json"),
    )
