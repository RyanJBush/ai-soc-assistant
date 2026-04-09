CREATE TABLE IF NOT EXISTS alert_triage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  alert_id INTEGER NOT NULL,
  actor TEXT NOT NULL,
  event_type TEXT NOT NULL,
  old_value TEXT NULL,
  new_value TEXT NOT NULL,
  note TEXT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_triage_events_alert_id ON alert_triage_events(alert_id, created_at ASC);
