import sqlite3
from pathlib import Path

from backend.app.db.sqlite import dump_json, get_connection, load_json


def test_get_connection_creates_parent_dirs(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "nested" / "test.db"
    assert not db_path.parent.exists()
    conn = get_connection(db_path)
    assert db_path.exists()
    conn.close()


def test_get_connection_returns_sqlite_connection(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "test.db")
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_get_connection_sets_row_factory(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "test.db")
    assert conn.row_factory is sqlite3.Row
    conn.close()


def test_get_connection_creates_alerts_table(tmp_path: Path) -> None:
    conn = get_connection(tmp_path / "test.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts'"
    ).fetchall()
    assert len(rows) == 1
    conn.close()


def test_get_connection_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn1 = get_connection(db_path)
    conn1.close()
    conn2 = get_connection(db_path)
    conn2.close()


def test_dump_json_produces_compact_output() -> None:
    result = dump_json({"key": "value", "num": 42})
    assert result == '{"key":"value","num":42}'


def test_dump_json_empty_dict() -> None:
    assert dump_json({}) == "{}"


def test_dump_json_nested_structure() -> None:
    data = {"a": {"b": 1}}
    result = dump_json(data)
    assert '"a"' in result
    assert '"b"' in result


def test_load_json_parses_string() -> None:
    result = load_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_load_json_empty_object() -> None:
    assert load_json("{}") == {}


def test_dump_and_load_roundtrip() -> None:
    original = {"duration": 0, "protocol_type": "tcp", "serror_rate": 0.12}
    assert load_json(dump_json(original)) == original
