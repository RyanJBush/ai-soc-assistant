from fastapi import APIRouter, HTTPException, status

from backend.app.core.exceptions import ModelNotLoadedError
from backend.app.schemas.model_info import ModelInfoResponse
from backend.app.services.model_registry import get_model_registry

router = APIRouter(tags=["model"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    registry = get_model_registry()
    try:
        metadata = registry.load_metrics()
    except ModelNotLoadedError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return ModelInfoResponse(
        model_name=metadata["model_name"],
        model_version=metadata["model_name"],
        selected_features=metadata["selected_features"],
        training_rows=metadata["training_rows"],
        test_rows=metadata["test_rows"],
        metrics=metadata["metrics"],
    )
