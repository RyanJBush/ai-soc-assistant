from datetime import datetime, timezone

from backend.app.core.config import Settings
from backend.app.db.sqlite import dump_json, load_json
from backend.app.db.session import Database
from backend.app.schemas.alert import AlertNote, AlertRecord, AlertStatus, AlertTriageEvent
from backend.app.schemas.inference import InferenceRequest, InferenceResponse
from backend.app.services.audit_service import AuditService


class AlertService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = Database(settings)
        self.db.run_migrations()
        self.audit_service = AuditService(settings)

    def create_alert(
        self,
        request: InferenceRequest,
        response: InferenceResponse,
        actor: str = "system",
    ) -> None:
        if not self.settings.alert_logging_enabled:
            return

        payload = (
            datetime.now(tz=timezone.utc),
            response.prediction_label,
            response.confidence,
            response.risk_level,
            dump_json(request.model_dump()),
            response.model_version,
            response.malicious_probability,
            dump_json([item.model_dump() for item in response.top_contributors]),
        )

        with self.db.connection() as connection:
            if self.db.driver == "sqlite":
                cursor = connection.execute(
                    """
                    INSERT INTO alerts (
                        created_at, prediction_label, confidence, risk_level, input_snapshot_json,
                        model_version, malicious_probability, contributors_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload[0].isoformat(),
                        payload[1],
                        payload[2],
                        payload[3],
                        payload[4],
                        payload[5],
                        payload[6],
                        payload[7],
                    ),
                )
                alert_id = str(cursor.lastrowid)
            else:
                result = connection.execute(
                    """
                    INSERT INTO alerts (
                        created_at, prediction_label, confidence, risk_level, input_snapshot_json,
                        model_version, malicious_probability, contributors_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    payload,
                )
                alert_id = str(result.fetchone()["id"])
            connection.commit()

        self.audit_service.log_event(
            actor=actor,
            action="alert.create",
            resource_type="alert",
            resource_id=alert_id,
            outcome="success",
            details={"risk_level": response.risk_level, "prediction_label": response.prediction_label},
        )

    def query_alerts(
        self,
        *,
        limit: int,
        page: int = 1,
        status: AlertStatus | None = None,
        assigned_to: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AlertRecord], int]:
        offset = (page - 1) * limit
        allowed_sort = {"created_at", "confidence", "risk_level", "status", "updated_at"}
        sort_key = sort_by if sort_by in allowed_sort else "created_at"
        order = "ASC" if sort_order.lower() == "asc" else "DESC"

        filters: list[str] = []
        params: list[object] = []
        placeholder = "%s" if self.db.driver != "sqlite" else "?"

        if status:
            filters.append(f"status = {placeholder}")
            params.append(status)
        if assigned_to:
            filters.append(f"assigned_to = {placeholder}")
            params.append(assigned_to)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        with self.db.connection() as connection:
            count_query = f"SELECT COUNT(*) as total FROM alerts {where_clause}"
            total_row = connection.execute(count_query, tuple(params)).fetchone()
            total = int(total_row["total"])

            query = f"""
                SELECT id, created_at, updated_at, prediction_label, confidence, risk_level,
                       malicious_probability, model_version, status, assigned_to,
                       input_snapshot_json, contributors_json
                FROM alerts
                {where_clause}
                ORDER BY {sort_key} {order}
                LIMIT {placeholder}
                OFFSET {placeholder}
            """
            rows = connection.execute(query, tuple([*params, limit, offset])).fetchall()

        records = [
            AlertRecord(
                id=row["id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                prediction_label=row["prediction_label"],
                confidence=row["confidence"],
                risk_level=row["risk_level"],
                malicious_probability=row["malicious_probability"],
                model_version=row["model_version"],
                status=row["status"],
                assigned_to=row["assigned_to"],
                top_contributors=load_json(row["contributors_json"]) if row["contributors_json"] else [],
                input_snapshot=load_json(row["input_snapshot_json"]),
            )
            for row in rows
        ]
        return records, total


    def get_recent_alerts(self, limit: int) -> list[AlertRecord]:
        records, _ = self.query_alerts(limit=limit)
        return records

    def get_alert(self, alert_id: int) -> AlertRecord | None:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        with self.db.connection() as connection:
            row = connection.execute(
                f"""
                SELECT id, created_at, updated_at, prediction_label, confidence, risk_level,
                       malicious_probability, model_version, status, assigned_to,
                       input_snapshot_json, contributors_json
                FROM alerts
                WHERE id = {placeholder}
                """,
                (alert_id,),
            ).fetchone()
        if row is None:
            return None
        return AlertRecord(
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            prediction_label=row["prediction_label"],
            confidence=row["confidence"],
            risk_level=row["risk_level"],
            malicious_probability=row["malicious_probability"],
            model_version=row["model_version"],
            status=row["status"],
            assigned_to=row["assigned_to"],
            top_contributors=load_json(row["contributors_json"]) if row["contributors_json"] else [],
            input_snapshot=load_json(row["input_snapshot_json"]),
        )

    def update_status(self, alert_id: int, status: AlertStatus, actor: str) -> AlertRecord | None:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        now_value = datetime.now(tz=timezone.utc)
        old_record = self.get_alert(alert_id)
        old_status = old_record.status if old_record else None
        with self.db.connection() as connection:
            connection.execute(
                f"UPDATE alerts SET status = {placeholder}, updated_at = {placeholder} WHERE id = {placeholder}",
                (status, now_value.isoformat() if self.db.driver == "sqlite" else now_value, alert_id),
            )
            connection.commit()
        record = self.get_alert(alert_id)
        if record:
            self.audit_service.log_event(
                actor=actor,
                action="alert.status_update",
                resource_type="alert",
                resource_id=str(alert_id),
                outcome="success",
                details={"status": status},
            )
            self.record_triage_event(
                alert_id=alert_id,
                actor=actor,
                event_type="status_change",
                new_value=status,
                old_value=old_status,
            )
        return record

    def assign_alert(self, alert_id: int, assigned_to: str, actor: str) -> AlertRecord | None:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        now_value = datetime.now(tz=timezone.utc)
        old_record = self.get_alert(alert_id)
        old_assignee = old_record.assigned_to if old_record else None
        with self.db.connection() as connection:
            connection.execute(
                f"UPDATE alerts SET assigned_to = {placeholder}, updated_at = {placeholder} WHERE id = {placeholder}",
                (assigned_to, now_value.isoformat() if self.db.driver == "sqlite" else now_value, alert_id),
            )
            connection.commit()
        record = self.get_alert(alert_id)
        if record:
            self.audit_service.log_event(
                actor=actor,
                action="alert.assignment_update",
                resource_type="alert",
                resource_id=str(alert_id),
                outcome="success",
                details={"assigned_to": assigned_to},
            )
            self.record_triage_event(
                alert_id=alert_id,
                actor=actor,
                event_type="assignment_change",
                new_value=assigned_to,
                old_value=old_assignee,
            )
        return record

    def add_note(self, alert_id: int, author: str, note: str) -> AlertNote | None:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        with self.db.connection() as connection:
            exists = connection.execute(
                f"SELECT id FROM alerts WHERE id = {placeholder}",
                (alert_id,),
            ).fetchone()
            if not exists:
                return None

            if self.db.driver == "sqlite":
                cursor = connection.execute(
                    f"INSERT INTO alert_notes (alert_id, author, note, created_at) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                    (alert_id, author, note, datetime.now(tz=timezone.utc).isoformat()),
                )
                note_id = cursor.lastrowid
            else:
                row = connection.execute(
                    f"INSERT INTO alert_notes (alert_id, author, note, created_at) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}) RETURNING id",
                    (alert_id, author, note, datetime.now(tz=timezone.utc)),
                ).fetchone()
                note_id = row["id"]
            connection.commit()

            note_row = connection.execute(
                f"SELECT id, alert_id, author, note, created_at FROM alert_notes WHERE id = {placeholder}",
                (note_id,),
            ).fetchone()

        self.audit_service.log_event(
            actor=author,
            action="alert.note_add",
            resource_type="alert",
            resource_id=str(alert_id),
            outcome="success",
            details={"note_id": note_id},
        )

        return AlertNote(
            id=note_row["id"],
            alert_id=note_row["alert_id"],
            author=note_row["author"],
            note=note_row["note"],
            created_at=note_row["created_at"],
        )

    def record_triage_event(
        self,
        alert_id: int,
        actor: str,
        event_type: str,
        new_value: str,
        old_value: str | None = None,
        note: str | None = None,
    ) -> None:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        now_value = datetime.now(tz=timezone.utc)
        with self.db.connection() as connection:
            connection.execute(
                f"""
                INSERT INTO alert_triage_events (alert_id, actor, event_type, old_value, new_value, note, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                """,
                (
                    alert_id,
                    actor,
                    event_type,
                    old_value,
                    new_value,
                    note,
                    now_value.isoformat() if self.db.driver == "sqlite" else now_value,
                ),
            )
            connection.commit()

    def get_triage_history(self, alert_id: int) -> list[AlertTriageEvent]:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        with self.db.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, alert_id, actor, event_type, old_value, new_value, note, created_at
                FROM alert_triage_events
                WHERE alert_id = {placeholder}
                ORDER BY created_at ASC
                """,
                (alert_id,),
            ).fetchall()
        return [
            AlertTriageEvent(
                id=row["id"],
                alert_id=row["alert_id"],
                actor=row["actor"],
                event_type=row["event_type"],
                old_value=row["old_value"],
                new_value=row["new_value"],
                note=row["note"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_notes(self, alert_id: int) -> list[AlertNote]:
        placeholder = "%s" if self.db.driver != "sqlite" else "?"
        with self.db.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT id, alert_id, author, note, created_at
                FROM alert_notes
                WHERE alert_id = {placeholder}
                ORDER BY id DESC
                """,
                (alert_id,),
            ).fetchall()
        return [
            AlertNote(
                id=row["id"],
                alert_id=row["alert_id"],
                author=row["author"],
                note=row["note"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def bulk_update_status(
        self,
        alert_ids: list[int],
        status: AlertStatus,
        actor: str,
    ) -> tuple[int, list[int]]:
        """Update status for multiple alerts atomically.

        Returns (updated_count, not_found_ids).
        """
        updated = 0
        not_found: list[int] = []
        for alert_id in alert_ids:
            result = self.update_status(alert_id, status, actor=actor)
            if result is None:
                not_found.append(alert_id)
            else:
                updated += 1
        return updated, not_found

    def export_alerts_csv(
        self,
        *,
        status: AlertStatus | None = None,
        assigned_to: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[AlertRecord]:
        """Return all matching alerts (no pagination) for CSV export."""
        allowed_sort = {"created_at", "confidence", "risk_level", "status", "updated_at"}
        sort_key = sort_by if sort_by in allowed_sort else "created_at"
        order = "ASC" if sort_order.lower() == "asc" else "DESC"

        filters: list[str] = []
        params: list[object] = []
        placeholder = "%s" if self.db.driver != "sqlite" else "?"

        if status:
            filters.append(f"status = {placeholder}")
            params.append(status)
        if assigned_to:
            filters.append(f"assigned_to = {placeholder}")
            params.append(assigned_to)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"""
            SELECT id, created_at, updated_at, prediction_label, confidence, risk_level,
                   malicious_probability, model_version, status, assigned_to,
                   input_snapshot_json, contributors_json
            FROM alerts
            {where_clause}
            ORDER BY {sort_key} {order}
        """
        with self.db.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [
            AlertRecord(
                id=row["id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                prediction_label=row["prediction_label"],
                confidence=row["confidence"],
                risk_level=row["risk_level"],
                malicious_probability=row["malicious_probability"],
                model_version=row["model_version"],
                status=row["status"],
                assigned_to=row["assigned_to"],
                top_contributors=load_json(row["contributors_json"]) if row["contributors_json"] else [],
                input_snapshot=load_json(row["input_snapshot_json"]),
            )
            for row in rows
        ]
