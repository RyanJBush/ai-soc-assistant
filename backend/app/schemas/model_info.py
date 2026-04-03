from pydantic import BaseModel


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    selected_features: list[str]
    training_rows: int
    test_rows: int
    metrics: dict[str, float]
