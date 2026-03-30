from datetime import datetime, timezone

import pandas as pd

from backend.app.core.config import Settings
from backend.app.core.exceptions import PredictionError
from backend.app.ml.feature_map import FEATURE_COLUMNS
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.model_registry import ModelRegistry


class PredictionService:
    def __init__(self, settings: Settings, model_registry: ModelRegistry):
        self.settings = settings
        self.model_registry = model_registry

    def predict(self, request: InferenceRequest) -> InferenceResponse:
        try:
            model_bundle = self.model_registry.load_model()
            pipeline = model_bundle["pipeline"]
            model_name = model_bundle["model_name"]

            payload = request.model_dump()
            frame = pd.DataFrame([payload], columns=FEATURE_COLUMNS)

            probabilities = pipeline.predict_proba(frame)[0]
            malicious_probability = float(probabilities[1])
            benign_probability = float(probabilities[0])
            prediction_label = "malicious" if malicious_probability >= 0.5 else "benign"
            confidence = max(malicious_probability, benign_probability)
            risk_level = self._risk_level(malicious_probability)

            contributors = self._simple_contributors(payload)
            return InferenceResponse(
                prediction_label=prediction_label,
                malicious_probability=round(malicious_probability, 4),
                confidence=round(confidence, 4),
                risk_level=risk_level,
                top_contributors=contributors,
                model_version=model_name,
                timestamp=datetime.now(tz=timezone.utc),
            )
        except Exception as exc:  # noqa: BLE001
            raise PredictionError("Failed to generate prediction") from exc

    def _risk_level(self, malicious_probability: float) -> str:
        if malicious_probability >= self.settings.risk_threshold_high:
            return "high"
        if malicious_probability >= 0.5:
            return "medium"
        return "low"

    @staticmethod
    def _simple_contributors(payload: dict) -> list[TopContributor]:
        heuristic_scores = {
            "src_bytes": float(payload["src_bytes"]),
            "dst_bytes": float(payload["dst_bytes"]),
            "serror_rate": float(payload["serror_rate"]) * 1000,
            "count": float(payload["count"]),
            "srv_count": float(payload["srv_count"]),
        }
        ranked = sorted(heuristic_scores.items(), key=lambda item: item[1], reverse=True)[:3]
        max_score = ranked[0][1] if ranked else 1.0
        return [
            TopContributor(feature=feature, impact=round((score / max_score), 3))
            for feature, score in ranked
        ]
