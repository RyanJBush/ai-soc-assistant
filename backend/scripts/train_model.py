"""Train binary intrusion detection model from NSL-KDD files.

Expected files:
- backend/data/raw/KDDTrain+.txt
- backend/data/raw/KDDTest+.txt
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from backend.app.ml.evaluator import evaluate_binary_model
from backend.app.ml.feature_map import FEATURE_COLUMNS
from backend.app.ml.trainer import build_candidate_models

RAW_TRAIN_PATH = Path("backend/data/raw/KDDTrain+.txt")
RAW_TEST_PATH = Path("backend/data/raw/KDDTest+.txt")
ARTIFACT_DIR = Path("backend/data/artifacts")

ALL_COLUMNS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]


def load_dataset(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, header=None, names=ALL_COLUMNS)


def map_binary_labels(frame: pd.DataFrame) -> pd.Series:
    return frame["label"].apply(lambda value: 0 if value == "normal" else 1)


def run() -> None:
    if not RAW_TRAIN_PATH.exists() or not RAW_TEST_PATH.exists():
        raise FileNotFoundError(
            "NSL-KDD files missing. Place KDDTrain+.txt and KDDTest+.txt in backend/data/raw/."
        )

    train_df = load_dataset(RAW_TRAIN_PATH)
    test_df = load_dataset(RAW_TEST_PATH)

    x_train = train_df[FEATURE_COLUMNS].copy()
    y_train = map_binary_labels(train_df)
    x_test = test_df[FEATURE_COLUMNS].copy()
    y_test = map_binary_labels(test_df)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    best_name = ""
    best_pipeline = None
    best_metrics: dict[str, float] | None = None

    models = build_candidate_models(random_state=42)
    for model_name, pipeline in models.items():
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]

        metrics = evaluate_binary_model(y_test, predictions, probabilities)

        if best_metrics is None:
            best_name, best_pipeline, best_metrics = model_name, pipeline, metrics
            continue

        if metrics["f1_score"] > best_metrics["f1_score"] or (
            metrics["f1_score"] == best_metrics["f1_score"]
            and metrics["recall"] > best_metrics["recall"]
        ):
            best_name, best_pipeline, best_metrics = model_name, pipeline, metrics

    assert best_pipeline is not None
    assert best_metrics is not None

    model_bundle = {"model_name": best_name, "pipeline": best_pipeline}
    joblib.dump(model_bundle, ARTIFACT_DIR / "model.joblib")

    payload = {
        "model_name": best_name,
        "selected_features": FEATURE_COLUMNS,
        "training_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "metrics": best_metrics,
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(payload, indent=2))
    (ARTIFACT_DIR / "feature_schema.json").write_text(json.dumps(FEATURE_COLUMNS, indent=2))

    print(f"Saved model: {ARTIFACT_DIR / 'model.joblib'}")
    print(f"Best model: {best_name}")
    print(json.dumps(best_metrics, indent=2))


if __name__ == "__main__":
    run()
