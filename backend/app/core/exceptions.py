class ModelNotLoadedError(RuntimeError):
    """Raised when model artifacts are unavailable."""


class PredictionError(RuntimeError):
    """Raised when prediction fails."""
