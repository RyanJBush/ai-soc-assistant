import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.core.config import Settings
from backend.app.db.session import Database
from backend.app.db.sqlite import dump_json, load_json


def _sha256_file(path: Path) -> str:
    if not path.exists():
        return "unavailable"
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelObservabilityService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = Database(settings)
        self.db.run_migrations()

    def register_active_model(self, metrics: dict[str, Any]) -> dict[str, Any]:
        model_name = str(metrics.get("model_name", "unknown"))
        model_version = str(metrics.get("model_version", model_name))
        artifact_path = str(self.settings.model_artifact_path)
        metrics_path = str(self.settings.metrics_path)
        artifact_sha = _sha256_file(self.settings.model_artifact_path)
        metrics_sha = _sha256_file(self.settings.metrics_path)

        with self.db.connection() as connection:
            if self.db.driver == "sqlite":
                connection.execute("UPDATE model_registry SET is_active = 0")
                connection.execute(
                    """
                    INSERT INTO model_registry (
                      model_name, model_version, artifact_path, artifact_sha256,
                      metrics_path, metrics_sha256, registered_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        model_name,
                        model_version,
                        artifact_path,
                        artifact_sha,
                        metrics_path,
                        metrics_sha,
                        datetime.now(tz=timezone.utc).isoformat(),
                        1,
                    ),
                )
            else:
                connection.execute("UPDATE model_registry SET is_active = FALSE")
                connection.execute(
                    """
                    INSERT INTO model_registry (
                      model_name, model_version, artifact_path, artifact_sha256,
                      metrics_path, metrics_sha256, registered_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        model_name,
                        model_version,
                        artifact_path,
                        artifact_sha,
                        metrics_path,
                        metrics_sha,
                        datetime.now(tz=timezone.utc),
                        True,
                    ),
                )
            connection.commit()

        return {
            "artifact_path": artifact_path,
            "artifact_sha256": artifact_sha,
            "metrics_path": metrics_path,
            "metrics_sha256": metrics_sha,
        }

    def get_active_model_lineage(self) -> dict[str, Any] | None:
        with self.db.connection() as connection:
            row = connection.execute(
                "SELECT artifact_path, artifact_sha256, metrics_path, metrics_sha256, registered_at "
                "FROM model_registry WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
                if self.db.driver == "sqlite"
                else "SELECT artifact_path, artifact_sha256, metrics_path, metrics_sha256, registered_at "
                "FROM model_registry WHERE is_active = TRUE ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return {
            "artifact_path": row["artifact_path"],
            "artifact_sha256": row["artifact_sha256"],
            "metrics_path": row["metrics_path"],
            "metrics_sha256": row["metrics_sha256"],
            "registered_at": row["registered_at"],
        }

    def record_monitoring_event(self, *, event_type: str, model_version: str, payload: dict) -> None:
        with self.db.connection() as connection:
            if self.db.driver == "sqlite":
                connection.execute(
                    "INSERT INTO monitoring_events (event_type, model_version, payload_json, created_at) VALUES (?, ?, ?, ?)",
                    (event_type, model_version, dump_json(payload), datetime.now(tz=timezone.utc).isoformat()),
                )
            else:
                connection.execute(
                    "INSERT INTO monitoring_events (event_type, model_version, payload_json, created_at) VALUES (%s, %s, %s, %s)",
                    (event_type, model_version, dump_json(payload), datetime.now(tz=timezone.utc)),
                )
            connection.commit()

    def recent_monitoring_events(self, limit: int = 20) -> list[dict[str, Any]]:
        query = """
            SELECT id, event_type, model_version, payload_json, created_at
            FROM monitoring_events
            ORDER BY id DESC
            LIMIT ?
        """
        if self.db.driver != "sqlite":
            query = query.replace("LIMIT ?", "LIMIT %s")
        with self.db.connection() as connection:
            rows = connection.execute(query, (limit,)).fetchall()
        return [
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "model_version": row["model_version"],
                "payload": load_json(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
