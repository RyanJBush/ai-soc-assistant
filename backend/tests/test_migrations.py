"""Tests for the database migration runner (Database class and load_migrations)."""
from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.db.migrations import load_migrations, parse_migration_file
from backend.app.db.session import Database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(tmp_path: Path) -> Settings:
    return Settings(sqlite_db_path=tmp_path / "test.db")


def _db(tmp_path: Path) -> Database:
    return Database(_settings(tmp_path))


# ---------------------------------------------------------------------------
# load_migrations / parse_migration_file
# ---------------------------------------------------------------------------


def test_parse_migration_file_extracts_version_and_description(tmp_path: Path) -> None:
    sql = "CREATE TABLE foo (id INTEGER PRIMARY KEY);"
    f = tmp_path / "001__create_foo_sqlite.sql"
    f.write_text(sql)
    m = parse_migration_file(f)
    assert m.version == "001"
    assert m.description == "create foo sqlite"
    assert m.sql == sql


def test_parse_migration_file_computes_stable_checksum(tmp_path: Path) -> None:
    sql = "SELECT 1;"
    f = tmp_path / "002__select_one.sql"
    f.write_text(sql)
    m1 = parse_migration_file(f)
    m2 = parse_migration_file(f)
    assert m1.checksum == m2.checksum


def test_parse_migration_file_checksum_changes_with_content(tmp_path: Path) -> None:
    f = tmp_path / "003__check.sql"
    f.write_text("SELECT 1;")
    m1 = parse_migration_file(f)
    f.write_text("SELECT 2;")
    m2 = parse_migration_file(f)
    assert m1.checksum != m2.checksum


def test_load_migrations_sqlite_returns_sqlite_files(tmp_path: Path) -> None:
    (tmp_path / "001__a_sqlite.sql").write_text("-- sqlite only")
    (tmp_path / "001__a.sql").write_text("-- postgres only")
    (tmp_path / "002__b.sql").write_text("-- both")
    migrations = load_migrations(tmp_path, "sqlite")
    versions = [m.version for m in migrations]
    assert "001" in versions
    # The postgres-only file for version 001 should be excluded
    assert all(not m.sql.startswith("-- postgres only") for m in migrations)


def test_load_migrations_postgres_excludes_sqlite_files(tmp_path: Path) -> None:
    (tmp_path / "001__a_sqlite.sql").write_text("-- sqlite only")
    (tmp_path / "001__a.sql").write_text("-- postgres only")
    migrations = load_migrations(tmp_path, "postgres")
    assert all("sqlite" not in m.description for m in migrations)
    assert any(m.sql == "-- postgres only" for m in migrations)


def test_load_migrations_returns_sorted_by_version(tmp_path: Path) -> None:
    (tmp_path / "003__c_sqlite.sql").write_text("-- c")
    (tmp_path / "001__a_sqlite.sql").write_text("-- a")
    (tmp_path / "002__b_sqlite.sql").write_text("-- b")
    migrations = load_migrations(tmp_path, "sqlite")
    assert [m.version for m in migrations] == ["001", "002", "003"]


def test_load_migrations_empty_directory(tmp_path: Path) -> None:
    assert load_migrations(tmp_path, "sqlite") == []


# ---------------------------------------------------------------------------
# Database.run_migrations – schema creation
# ---------------------------------------------------------------------------


def test_run_migrations_creates_schema_migrations_table(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchall()
    assert len(rows) == 1


def test_run_migrations_creates_alerts_table(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
        ).fetchall()
    assert len(rows) == 1


def test_run_migrations_creates_audit_logs_table(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        ).fetchall()
    assert len(rows) == 1


def test_run_migrations_creates_alert_notes_table(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alert_notes'"
        ).fetchall()
    assert len(rows) == 1


def test_run_migrations_creates_model_registry_table(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='model_registry'"
        ).fetchall()
    assert len(rows) == 1


def test_run_migrations_records_applied_versions(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    versions = [row["version"] for row in rows]
    assert "001" in versions
    assert "002" in versions
    assert "003" in versions
    assert "004" in versions


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_run_migrations_is_idempotent(tmp_path: Path) -> None:
    db = _db(tmp_path)
    db.run_migrations()
    # Second call must not raise and must not duplicate rows.
    db.run_migrations()
    with db.connection() as conn:
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    versions = [row["version"] for row in rows]
    assert len(versions) == len(set(versions)), "Duplicate migration entries detected"


def test_multiple_database_instances_share_same_applied_state(tmp_path: Path) -> None:
    db1 = _db(tmp_path)
    db1.run_migrations()

    # Second instance pointing at the same file must see all migrations as applied.
    db2 = _db(tmp_path)
    with db2.connection() as conn:
        db2._ensure_migrations_table(conn)
        applied = db2._applied_versions(conn)
    assert "001" in applied
    assert "002" in applied


# ---------------------------------------------------------------------------
# _applied_versions
# ---------------------------------------------------------------------------


def test_applied_versions_returns_empty_set_for_fresh_db(tmp_path: Path) -> None:
    db = _db(tmp_path)
    with db.connection() as conn:
        db._ensure_migrations_table(conn)
        applied = db._applied_versions(conn)
    assert applied == set()


def test_applied_versions_reflects_inserted_rows(tmp_path: Path) -> None:
    db = _db(tmp_path)
    with db.connection() as conn:
        db._ensure_migrations_table(conn)
        conn.execute(
            "INSERT INTO schema_migrations (version, description, checksum, applied_at) VALUES (?,?,?,?)",
            ("099", "test", "abc", "2024-01-01T00:00:00+00:00"),
        )
        conn.commit()
        applied = db._applied_versions(conn)
    assert "099" in applied


# ---------------------------------------------------------------------------
# Migration CLI script
# ---------------------------------------------------------------------------


def test_migrate_cli_exits_zero_when_up_to_date(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess
    import sys

    env = {
        "SQLITE_DB_PATH": str(tmp_path / "cli.db"),
        "PATH": "/usr/bin:/bin",
    }
    # First run – applies migrations
    result1 = subprocess.run(
        [sys.executable, "-m", "backend.scripts.migrate"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result1.returncode == 0, result1.stderr

    # Second run – all up to date
    result2 = subprocess.run(
        [sys.executable, "-m", "backend.scripts.migrate"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result2.returncode == 0
    assert "up to date" in result2.stdout.lower()


def test_migrate_cli_check_exits_one_when_pending(tmp_path: Path) -> None:
    import subprocess
    import sys

    env = {
        "SQLITE_DB_PATH": str(tmp_path / "fresh.db"),
        "PATH": "/usr/bin:/bin",
    }
    result = subprocess.run(
        [sys.executable, "-m", "backend.scripts.migrate", "--check"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result.returncode == 1
    assert "pending" in result.stdout.lower()


def test_migrate_cli_check_exits_zero_when_up_to_date(tmp_path: Path) -> None:
    import subprocess
    import sys

    env = {
        "SQLITE_DB_PATH": str(tmp_path / "check.db"),
        "PATH": "/usr/bin:/bin",
    }
    # Apply first
    subprocess.run(
        [sys.executable, "-m", "backend.scripts.migrate"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    # Check should now exit 0
    result = subprocess.run(
        [sys.executable, "-m", "backend.scripts.migrate", "--check"],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **env},
    )
    assert result.returncode == 0
