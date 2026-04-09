from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend.app.core.config import Settings
from backend.app.core.exceptions import AlertPersistenceError
from backend.app.db.migrations import load_migrations

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None
    dict_row = None


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.database_url = settings.database_url
        self.sqlite_path = settings.sqlite_db_path
        self.driver = self._detect_driver()

    def _detect_driver(self) -> str:
        if not self.database_url:
            return "sqlite"
        parsed = urlparse(self.database_url)
        if parsed.scheme.startswith("postgres"):
            return "postgres"
        if parsed.scheme.startswith("sqlite"):
            return "sqlite"
        raise AlertPersistenceError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    @contextmanager
    def connection(self):
        if self.driver == "postgres":
            if psycopg is None:
                raise AlertPersistenceError("psycopg is required for PostgreSQL connections")
            assert self.database_url is not None
            with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
                yield conn
            return

        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            yield conn

    def run_migrations(self) -> None:
        sql_dir = Path(__file__).resolve().parent / "sql"
        migrations = load_migrations(sql_dir, self.driver)
        if not migrations:
            return

        with self.connection() as conn:
            self._ensure_migrations_table(conn)
            applied = self._applied_versions(conn)
            for migration in migrations:
                if migration.version in applied:
                    continue
                if self.driver == "sqlite":
                    conn.executescript(migration.sql)
                    conn.execute(
                        """
                        INSERT INTO schema_migrations (version, description, checksum, applied_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            migration.version,
                            migration.description,
                            migration.checksum,
                            datetime.now(tz=timezone.utc).isoformat(),
                        ),
                    )
                else:
                    conn.execute(migration.sql)
                    conn.execute(
                        """
                        INSERT INTO schema_migrations (version, description, checksum, applied_at)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            migration.version,
                            migration.description,
                            migration.checksum,
                            datetime.now(tz=timezone.utc),
                        ),
                    )
            conn.commit()

    def _ensure_migrations_table(self, conn: Any) -> None:
        if self.driver == "sqlite":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version TEXT PRIMARY KEY,
                  description TEXT NOT NULL,
                  checksum TEXT NOT NULL,
                  applied_at TEXT NOT NULL
                )
                """
            )
            return

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              description TEXT NOT NULL,
              checksum TEXT NOT NULL,
              applied_at TIMESTAMPTZ NOT NULL
            )
            """
        )

    def _applied_versions(self, conn: Any) -> set[str]:
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        return {row["version"] for row in rows}
