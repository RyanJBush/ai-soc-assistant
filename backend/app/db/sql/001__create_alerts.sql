CREATE TABLE IF NOT EXISTS alerts (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL,
  prediction_label TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  risk_level TEXT NOT NULL,
  input_snapshot_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
