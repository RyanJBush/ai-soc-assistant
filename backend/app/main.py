from fastapi import FastAPI

from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_model import router as model_router
from backend.app.api.routes_predict import router as predict_router
from backend.app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="AI Intrusion Detection System API", version="0.2.0")
app.include_router(health_router)
app.include_router(model_router)
app.include_router(predict_router)
