from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from backend.app.ml.preprocessing import build_preprocessor


def build_candidate_models(random_state: int = 42) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [
                ("preprocessor", build_preprocessor(scale_numeric=True)),
                ("model", LogisticRegression(max_iter=200, random_state=random_state)),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("preprocessor", build_preprocessor(scale_numeric=False)),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        max_depth=18,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }
