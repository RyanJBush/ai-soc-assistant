"""Standalone migration runner.

Usage
-----
Run pending migrations against the configured database::

    python -m backend.scripts.migrate

Check which migrations are pending (dry-run, non-zero exit if any)::

    python -m backend.scripts.migrate --check

Override the database URL::

    DATABASE_URL=postgresql://... python -m backend.scripts.migrate

Environment
-----------
All settings are read from the standard application config (`.env` file or
environment variables).  The most relevant variable for this script is
``DATABASE_URL``; when absent the runner falls back to the SQLite path
configured by ``SQLITE_DB_PATH``.
"""
from __future__ import annotations

import argparse
import logging
import sys

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.db.migrations import load_migrations
from backend.app.db.session import Database


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply pending database migrations for the AI SOC Assistant."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if there are pending migrations (do not apply them).",
    )
    return parser.parse_args()


def _pending_versions(db: Database) -> list[str]:
    """Return the versions of migrations that have not yet been applied."""
    from pathlib import Path as _Path

    sql_dir = _Path(__file__).resolve().parents[1] / "app" / "db" / "sql"
    migrations = load_migrations(sql_dir, db.driver)
    with db.connection() as conn:
        db._ensure_migrations_table(conn)
        applied = db._applied_versions(conn)
    return [m.version for m in migrations if m.version not in applied]


def main() -> None:
    args = _parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    db = Database(settings)
    driver_label = db.driver.upper()
    db_label = str(settings.database_url or settings.sqlite_db_path)

    logger.info("migration_runner_start", extra={"driver": driver_label, "target": db_label})

    pending = _pending_versions(db)

    if not pending:
        logger.info("migrations_up_to_date", extra={"driver": driver_label})
        print("All migrations are up to date.")
        sys.exit(0)

    if args.check:
        print(f"Pending migrations: {', '.join(pending)}")
        logger.warning(
            "pending_migrations_detected",
            extra={"pending": pending, "driver": driver_label},
        )
        sys.exit(1)

    logger.info("applying_migrations", extra={"pending": pending, "driver": driver_label})
    db.run_migrations()
    print(f"Applied {len(pending)} migration(s): {', '.join(pending)}")
    logger.info("migrations_applied", extra={"versions": pending, "driver": driver_label})


if __name__ == "__main__":
    main()
