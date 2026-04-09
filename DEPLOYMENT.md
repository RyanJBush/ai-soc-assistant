# Deployment Guide (Phase 6)

## 1) Recommended hosting split

- **Backend**: Render/Railway/Fly.io (Python web service)
- **Database**: Managed PostgreSQL
- **Frontend**: Vercel/Netlify (Vite static build)

Provided manifests/templates:
- `deploy/render.yaml`
- `frontend/vercel.json`
- `.env.staging.example`
- `.env.production.example`

## 2) Required backend environment variables

- `APP_ENV=production`
- `DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<db_name>`
- `AUTH_ENABLED=true`
- `JWT_SECRET_KEY=<32+ char random secret>`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `RATE_LIMIT_PER_MINUTE=120`
- `RATE_LIMIT_BACKEND=redis`
- `REDIS_URL=redis://<redis-host>:6379/0`
- `REDIS_RATE_LIMIT_PREFIX=ai_soc:ratelimit`
- `CORS_ALLOWED_ORIGINS=https://<frontend-domain>`

## 3) ML scoring configuration

- `MALICIOUS_DECISION_THRESHOLD` (default `0.5`)
- `RISK_THRESHOLD_MEDIUM` (default `0.5`)
- `RISK_THRESHOLD_HIGH` (default `0.8`)
- `RISK_THRESHOLD_CRITICAL` (default `0.93`)

## 4) Release/deploy flow

1. Run pre-release checks from [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
2. Deploy backend + DB
3. Deploy frontend with `VITE_API_BASE_URL` pointing to backend
4. Run smoke validation:

```bash
make smoke-test
```

## 5) Post-deploy verification

- `GET /health` returns `{"status":"ok"}`
- `POST /auth/login` succeeds for known test account
- `GET /model-info` returns thresholds + lineage
- `POST /predict` creates alert
- `GET /alerts/recent` shows created alert
- `GET /monitoring/events` returns recent events

## 6) Operational references

- [RUNBOOK.md](RUNBOOK.md)
- [CHANGELOG.md](CHANGELOG.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
