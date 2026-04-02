class ModelNotLoadedError(RuntimeError):
    """Raised when model artifacts are unavailable."""

    error_code: str = "MODEL_NOT_LOADED"


class PredictionError(RuntimeError):
    """Raised when prediction fails."""

    error_code: str = "PREDICTION_FAILED"
