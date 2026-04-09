#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH=.
export SQLITE_DB_PATH="/tmp/ai_soc_smoke.db"
export AUTH_ENABLED=true
export APP_ENV=development

uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 >/tmp/ai_soc_smoke.log 2>&1 &
PID=$!
trap 'kill $PID >/dev/null 2>&1 || true' EXIT

for _ in {1..30}; do
  if curl -sf http://127.0.0.1:8001/health >/dev/null; then
    break
  fi
  sleep 1
done

curl -sf http://127.0.0.1:8001/health >/dev/null
TOKEN=$(curl -s -X POST http://127.0.0.1:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst123!"}' | python -c 'import json,sys;print(json.load(sys.stdin)["access_token"])')

curl -sf http://127.0.0.1:8001/model-info -H "Authorization: Bearer ${TOKEN}" >/dev/null || true
curl -sf -X POST http://127.0.0.1:8001/monitoring/events \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"prediction.volume","model_version":"smoke","payload":{"count":1}}' >/dev/null

echo "Smoke test completed successfully."
