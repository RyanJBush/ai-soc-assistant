# AI SOC Assistant Runbook

## Service health checks
- API health: `GET /health`
- Model metadata: `GET /model-info` (requires auth)
- Monitoring events: `GET /monitoring/events?limit=20` (analyst/admin)

## Common incidents

### 1) Model artifact missing
Symptoms:
- `/model-info` returns `MODEL_NOT_LOADED`

Actions:
1. Verify `MODEL_ARTIFACT_PATH` and `METRICS_PATH` environment values.
2. Confirm artifact files exist and are readable.
3. Redeploy with corrected artifact volume/storage mapping.

### 2) DB migration failure on startup
Symptoms:
- API starts failing with persistence errors

Actions:
1. Check startup logs for migration SQL error.
2. Verify DB user has `CREATE/ALTER/INSERT` on schema.
3. Roll forward with corrected migration; do not manually edit migration history rows without backup.

### 3) Elevated authentication failures
Symptoms:
- Increased 401/403 responses

Actions:
1. Validate JWT secret and auth env vars are consistent across instances.
2. Verify demo users / credential source configuration.
3. Check rate-limit settings to avoid accidental lockout patterns.

## Operational commands

```bash
# backend tests
PYTHONPATH=. pytest backend/tests -q

# smoke test
bash scripts/smoke_test.sh
```
