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
        model_name=metadata["model_name"],
        model_version=metadata["model_name"],
        selected_features=metadata["selected_features"],
        training_rows=metadata["training_rows"],
        test_rows=metadata["test_rows"],
        metrics=metadata["metrics"],
    )
