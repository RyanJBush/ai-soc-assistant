from fastapi import APIRouter, Depends

from backend.app.core.auth import verify_api_key
from backend.app.schemas.model_info import ModelInfoResponse
from backend.app.services.model_registry import get_model_registry

router = APIRouter(tags=["model"], dependencies=[Depends(verify_api_key)])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    registry = get_model_registry()
    metadata = registry.load_metrics()

    return ModelInfoResponse(
        model_name=str(metadata.get("model_name", "unknown")),
        model_version=str(metadata.get("model_name", "unknown")),
        selected_features=list(metadata.get("selected_features", [])),
        training_rows=int(metadata.get("training_rows", 0)),
        test_rows=int(metadata.get("test_rows", 0)),
        metrics=dict(metadata.get("metrics", {})),
    )
