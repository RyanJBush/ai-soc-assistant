from datetime import datetime, timezone

from backend.app.core.config import Settings
from backend.app.db.sqlite import dump_json, get_connection, load_json
from backend.app.schemas.alert import AlertRecord
from backend.app.schemas.inference import InferenceRequest, InferenceResponse


class AlertService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_alert(self, request: InferenceRequest, response: InferenceResponse) -> None:
        if not self.settings.alert_logging_enabled:
            return

        with get_connection(self.settings.sqlite_db_path) as connection:
            connection.execute(
                """
                INSERT INTO alerts (created_at, prediction_label, confidence, risk_level, input_snapshot_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(tz=timezone.utc).isoformat(),
                    response.prediction_label,
                    response.confidence,
                    response.risk_level,
                    dump_json(request.model_dump()),
                ),
            )
            connection.commit()

    def get_recent_alerts(self, limit: int) -> list[AlertRecord]:
        with get_connection(self.settings.sqlite_db_path) as connection:
            rows = connection.execute(
                """
                SELECT id, created_at, prediction_label, confidence, risk_level, input_snapshot_json
                FROM alerts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            AlertRecord(
                id=row["id"],
                created_at=row["created_at"],
                prediction_label=row["prediction_label"],
                confidence=row["confidence"],
                risk_level=row["risk_level"],
                input_snapshot=load_json(row["input_snapshot_json"]),
            )
            for row in rows
        ]
