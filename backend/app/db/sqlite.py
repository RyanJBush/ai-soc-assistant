import json
import sqlite3
from pathlib import Path

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  prediction_label TEXT NOT NULL,
  confidence REAL NOT NULL,
  risk_level TEXT NOT NULL,
  input_snapshot_json TEXT NOT NULL
);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute(DB_SCHEMA)
    return connection


def dump_json(data: dict) -> str:
    return json.dumps(data, separators=(",", ":"))


def load_json(payload: str) -> dict:
    return json.loads(payload)
