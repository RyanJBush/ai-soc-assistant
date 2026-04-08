class ModelNotLoadedError(RuntimeError):
    """Raised when model artifacts are unavailable."""

    error_code: str = "MODEL_NOT_LOADED"


class PredictionError(RuntimeError):
    """Raised when prediction inference fails."""

    error_code: str = "PREDICTION_FAILED"


class AlertPersistenceError(RuntimeError):
    """Raised when alert persistence operations fail."""

    error_code: str = "ALERT_PERSISTENCE_FAILED"
