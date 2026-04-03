import json
from functools import lru_cache

import joblib

from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import ModelNotLoadedError


class ModelRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings

    def load_model(self):
        if not self.settings.model_artifact_path.exists():
            raise ModelNotLoadedError(
                f"Model artifact not found at {self.settings.model_artifact_path}. Run training script first."
            )
        return joblib.load(self.settings.model_artifact_path)

    def load_metrics(self) -> dict:
        if not self.settings.metrics_path.exists():
            raise ModelNotLoadedError(
                f"Metrics file not found at {self.settings.metrics_path}. Run training script first."
            )
        return json.loads(self.settings.metrics_path.read_text())


@lru_cache(maxsize=1)
def get_model_registry() -> ModelRegistry:
    return ModelRegistry(get_settings())
