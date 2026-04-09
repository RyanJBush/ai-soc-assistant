from datetime import datetime, timezone

from backend.app.core.config import Settings
from backend.app.db.session import Database
from backend.app.db.sqlite import dump_json, load_json
from backend.app.schemas.audit import AuditRecord


class AuditService:
    def __init__(self, settings: Settings):
        self.db = Database(settings)
        self.db.run_migrations()

    def log_event(
        self,
        *,
        actor: str,
        action: str,
        resource_type: str,
        outcome: str,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        payload = details or {}
        with self.db.connection() as connection:
            if self.db.driver == "sqlite":
                connection.execute(
                    """
                    INSERT INTO audit_logs (created_at, actor, action, resource_type, resource_id, outcome, details_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        datetime.now(tz=timezone.utc).isoformat(),
                        actor,
                        action,
                        resource_type,
                        resource_id,
                        outcome,
                        dump_json(payload),
                    ),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO audit_logs (created_at, actor, action, resource_type, resource_id, outcome, details_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        datetime.now(tz=timezone.utc),
                        actor,
                        action,
                        resource_type,
                        resource_id,
                        outcome,
                        dump_json(payload),
                    ),
                )
            connection.commit()

    def get_recent(self, limit: int = 50) -> list[AuditRecord]:
        with self.db.connection() as connection:
            query = """
                SELECT id, created_at, actor, action, resource_type, resource_id, outcome, details_json
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
            """
            if self.db.driver != "sqlite":
                query = query.replace("LIMIT ?", "LIMIT %s")

            rows = connection.execute(query, (limit,)).fetchall()

        return [
            AuditRecord(
                id=row["id"],
                created_at=row["created_at"],
                actor=row["actor"],
                action=row["action"],
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
                outcome=row["outcome"],
                details=load_json(row["details_json"]),
            )
            for row in rows
        ]
