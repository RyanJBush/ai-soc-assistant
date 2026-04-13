from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.db.session import Database
from backend.app.schemas.analytics import AnalyticsResponse, DailyVolume

_RISK_LEVELS = ("low", "medium", "high", "critical")
_STATUSES = ("new", "acknowledged", "escalated", "resolved")


class AnalyticsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = Database(settings)
        self.db.run_migrations()

    def get_analytics(self, days: int = 14) -> AnalyticsResponse:
        if self.db.driver == "sqlite":
            return self._get_analytics_sqlite(days)
        return self._get_analytics_pg(days)

    # ------------------------------------------------------------------
    # SQLite implementation
    # ------------------------------------------------------------------

    def _get_analytics_sqlite(self, days: int) -> AnalyticsResponse:
        with self.db.connection() as conn:
            # Totals
            row = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()
            total = int(row[0]) if row else 0

            row = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE prediction_label = 'malicious'"
            ).fetchone()
            malicious_count = int(row[0]) if row else 0

            row = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status != 'resolved'"
            ).fetchone()
            open_count = int(row[0]) if row else 0

            # By risk level
            rows = conn.execute(
                "SELECT risk_level, COUNT(*) FROM alerts GROUP BY risk_level"
            ).fetchall()
            by_risk: dict[str, int] = {k: 0 for k in _RISK_LEVELS}
            for risk_level, count in rows:
                if risk_level in by_risk:
                    by_risk[risk_level] = int(count)

            # By status
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM alerts GROUP BY status"
            ).fetchall()
            by_status: dict[str, int] = {k: 0 for k in _STATUSES}
            for status, count in rows:
                if status in by_status:
                    by_status[status] = int(count)

            # Volume by day
            rows = conn.execute(
                """
                SELECT
                    DATE(created_at) AS day,
                    COUNT(*) AS total,
                    SUM(CASE WHEN prediction_label = 'malicious' THEN 1 ELSE 0 END) AS mal
                FROM alerts
                WHERE DATE(created_at) >= DATE('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY day ASC
                """,
                (f"-{days} days",),
            ).fetchall()
            volume = [
                DailyVolume(date=str(day), count=int(total_d), malicious=int(mal))
                for day, total_d, mal in rows
            ]

            # MTTR — average hours from alert creation to first 'resolved' triage event
            row = conn.execute(
                """
                SELECT AVG((julianday(e.created_at) - julianday(a.created_at)) * 24)
                FROM alerts a
                JOIN alert_triage_events e ON a.id = e.alert_id
                WHERE e.event_type = 'status_change' AND e.new_value = 'resolved'
                """
            ).fetchone()
            avg_hours = float(row[0]) if row and row[0] is not None else None

        return _build_response(
            days=days,
            total=total,
            malicious_count=malicious_count,
            open_count=open_count,
            by_risk=by_risk,
            by_status=by_status,
            volume=volume,
            avg_hours=avg_hours,
        )

    # ------------------------------------------------------------------
    # PostgreSQL implementation
    # ------------------------------------------------------------------

    def _get_analytics_pg(self, days: int) -> AnalyticsResponse:
        with self.db.connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()
            total = int(row[0]) if row else 0

            row = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE prediction_label = 'malicious'"
            ).fetchone()
            malicious_count = int(row[0]) if row else 0

            row = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status != 'resolved'"
            ).fetchone()
            open_count = int(row[0]) if row else 0

            rows = conn.execute(
                "SELECT risk_level, COUNT(*) FROM alerts GROUP BY risk_level"
            ).fetchall()
            by_risk: dict[str, int] = {k: 0 for k in _RISK_LEVELS}
            for risk_level, count in rows:
                if risk_level in by_risk:
                    by_risk[risk_level] = int(count)

            rows = conn.execute(
                "SELECT status, COUNT(*) FROM alerts GROUP BY status"
            ).fetchall()
            by_status: dict[str, int] = {k: 0 for k in _STATUSES}
            for status, count in rows:
                if status in by_status:
                    by_status[status] = int(count)

            rows = conn.execute(
                """
                SELECT
                    DATE(created_at) AS day,
                    COUNT(*) AS total,
                    SUM(CASE WHEN prediction_label = 'malicious' THEN 1 ELSE 0 END) AS mal
                FROM alerts
                WHERE DATE(created_at) >= CURRENT_DATE - INTERVAL %s
                GROUP BY DATE(created_at)
                ORDER BY day ASC
                """,
                (f"{days} days",),
            ).fetchall()
            volume = [
                DailyVolume(date=str(day), count=int(total_d), malicious=int(mal))
                for day, total_d, mal in rows
            ]

            row = conn.execute(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (e.created_at::timestamptz - a.created_at::timestamptz)) / 3600)
                FROM alerts a
                JOIN alert_triage_events e ON a.id = e.alert_id
                WHERE e.event_type = 'status_change' AND e.new_value = 'resolved'
                """
            ).fetchone()
            avg_hours = float(row[0]) if row and row[0] is not None else None

        return _build_response(
            days=days,
            total=total,
            malicious_count=malicious_count,
            open_count=open_count,
            by_risk=by_risk,
            by_status=by_status,
            volume=volume,
            avg_hours=avg_hours,
        )


def _build_response(
    *,
    days: int,
    total: int,
    malicious_count: int,
    open_count: int,
    by_risk: dict[str, int],
    by_status: dict[str, int],
    volume: list[DailyVolume],
    avg_hours: float | None,
) -> AnalyticsResponse:
    benign_count = total - malicious_count
    malicious_rate = malicious_count / total if total > 0 else 0.0
    return AnalyticsResponse(
        days=days,
        total_alerts=total,
        malicious_count=malicious_count,
        benign_count=benign_count,
        open_count=open_count,
        malicious_rate=round(malicious_rate, 4),
        avg_resolution_hours=round(avg_hours, 2) if avg_hours is not None else None,
        by_risk_level=by_risk,
        by_status=by_status,
        alert_volume_by_day=volume,
    )
