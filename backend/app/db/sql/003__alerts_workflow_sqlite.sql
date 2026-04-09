ALTER TABLE alerts ADD COLUMN status TEXT NOT NULL DEFAULT 'new';
ALTER TABLE alerts ADD COLUMN assigned_to TEXT NULL;
ALTER TABLE alerts ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE alerts ADD COLUMN model_version TEXT NULL;
ALTER TABLE alerts ADD COLUMN malicious_probability REAL NULL;
ALTER TABLE alerts ADD COLUMN contributors_json TEXT NULL;

CREATE TABLE IF NOT EXISTS alert_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  alert_id INTEGER NOT NULL,
  author TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alert_notes_alert_id ON alert_notes(alert_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
