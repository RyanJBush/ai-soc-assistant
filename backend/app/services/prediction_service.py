from datetime import datetime, timezone

import logging

import pandas as pd

from backend.app.core.config import Settings
from backend.app.core.exceptions import ModelNotLoadedError, PredictionError
from backend.app.ml.feature_map import FEATURE_COLUMNS, NUMERIC_COLUMNS
from backend.app.schemas.inference import InferenceRequest, InferenceResponse, TopContributor
from backend.app.services.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


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
            benign_probability = float(probabilities[0])
            malicious_probability = float(probabilities[1])

            prediction_label = (
                "malicious"
                if malicious_probability >= self.settings.malicious_decision_threshold
                else "benign"
            )
            confidence = max(malicious_probability, benign_probability)
            risk_level = self._risk_level(malicious_probability)

            contributors, explain_method = self._explain_contributors(pipeline, payload, malicious_probability)
            return InferenceResponse(
                prediction_label=prediction_label,
                malicious_probability=round(malicious_probability, 4),
                confidence=round(confidence, 4),
                risk_level=risk_level,
                top_contributors=contributors,
                explain_method=explain_method,
                model_version=str(model_name),
                timestamp=datetime.now(tz=timezone.utc),
            )
        except ModelNotLoadedError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PredictionError("Failed to generate prediction") from exc

    def _risk_level(self, malicious_probability: float) -> str:
        if malicious_probability >= self.settings.risk_threshold_critical:
            return "critical"
        if malicious_probability >= self.settings.risk_threshold_high:
            return "high"
        if malicious_probability >= self.settings.risk_threshold_medium:
            return "medium"
        return "low"

    def _explain_contributors(
        self,
        pipeline,
        payload: dict,
        baseline_probability: float,
    ) -> tuple[list[TopContributor], str]:
        global_contrib = self._global_feature_contributors(pipeline)
        local_contrib = self._local_sensitivity_contributors(pipeline, payload, baseline_probability)

        if not local_contrib and not global_contrib:
            return self._heuristic_contributors(payload), "heuristic"

        merged: dict[str, float] = {}
        explain_method: str
        if global_contrib and local_contrib:
            explain_method = "feature_importance+sensitivity"
            for feature, score in global_contrib.items():
                merged[feature] = merged.get(feature, 0.0) + score * 0.4
            for feature, score in local_contrib.items():
                merged[feature] = merged.get(feature, 0.0) + score * 0.6
        elif global_contrib:
            explain_method = "feature_importance"
            merged = dict(global_contrib)
        else:
            explain_method = "sensitivity"
            merged = dict(local_contrib)

        ranked = sorted(merged.items(), key=lambda item: item[1], reverse=True)[:3]
        if not ranked or ranked[0][1] <= 0:
            return self._heuristic_contributors(payload), "heuristic"
        max_score = ranked[0][1]
        return [
            TopContributor(feature=feature, impact=round(score / max_score, 3))
            for feature, score in ranked
        ], explain_method

    @staticmethod
    def _global_feature_contributors(pipeline) -> dict[str, float]:
        named = getattr(pipeline, "named_steps", {})
        model = named.get("model")
        preprocessor = named.get("preprocessor")

        raw_importances: list[float] | None = None
        if model is not None and hasattr(model, "feature_importances_"):
            raw_importances = list(model.feature_importances_)
        elif model is not None and hasattr(model, "coef_"):
            raw_importances = [abs(float(c)) for c in model.coef_[0]]

        if raw_importances is None or preprocessor is None:
            return {}

        try:
            feature_names_out = list(preprocessor.get_feature_names_out())
            original_importances: dict[str, float] = {}
            for expanded_name, importance in zip(feature_names_out, raw_importances):
                _, rest = expanded_name.split("__", 1)
                original = next(
                    (col for col in FEATURE_COLUMNS if rest == col or rest.startswith(col + "_")),
                    rest,
                )
                original_importances[original] = original_importances.get(original, 0.0) + importance
            return original_importances
        except Exception as exc:  # noqa: BLE001
            logger.debug("Global contributor extraction failed: %s", exc)
            return {}

    @staticmethod
    def _local_sensitivity_contributors(
        pipeline,
        payload: dict,
        baseline_probability: float,
    ) -> dict[str, float]:
        sensitivity: dict[str, float] = {}
        for feature in NUMERIC_COLUMNS:
            original_value = float(payload[feature])
            delta = max(abs(original_value) * 0.1, 1.0 if original_value == 0 else 0.01)
            modified = dict(payload)
            modified[feature] = original_value + delta
            frame = pd.DataFrame([modified], columns=FEATURE_COLUMNS)
            try:
                new_probability = float(pipeline.predict_proba(frame)[0][1])
            except Exception:  # noqa: BLE001
                continue
            sensitivity[feature] = abs(new_probability - baseline_probability)
        return sensitivity

    @staticmethod
    def _heuristic_contributors(payload: dict) -> list[TopContributor]:
        heuristic_scores = {
            "src_bytes": float(payload["src_bytes"]),
            "dst_bytes": float(payload["dst_bytes"]),
            "serror_rate": float(payload["serror_rate"]) * 1000,
            "count": float(payload["count"]),
            "srv_count": float(payload["srv_count"]),
        }
        ranked = sorted(heuristic_scores.items(), key=lambda item: item[1], reverse=True)[:3]
        max_score = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
        return [
            TopContributor(feature=feature, impact=round((score / max_score), 3))
            for feature, score in ranked
        ]
