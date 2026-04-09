# Deployment Guide

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

## 4) Database migrations

Migrations are managed by a lightweight built-in runner located in
`backend/app/db/migrations.py`.  There are two migration paths:

| Path | When used |
|------|-----------|
| SQLite (`*_sqlite.sql`) | Local development – no configuration required |
| PostgreSQL (`*.sql`, excluding `*_sqlite.sql`) | Staging / production via `DATABASE_URL` |

### How migrations run

Migrations are applied automatically when the backend process starts.
The runner records each applied version in a `schema_migrations` table, so
re-starts are safe and idempotent.

### Running migrations manually

Before deploying a new release (or after a DB restore) you can run
migrations without starting the full API server:

```bash
# Apply all pending migrations
make db-migrate

# Check for pending migrations (exits 1 if any are found – useful in CI)
make db-migrate-check

# Equivalent without make
python -m backend.scripts.migrate
python -m backend.scripts.migrate --check
```

Pass `DATABASE_URL` to target a non-default database:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/mydb python -m backend.scripts.migrate
```

### Migration naming convention

Migration files live in `backend/app/db/sql/` and follow the pattern:

```
<version>__<description>.sql          # PostgreSQL (and SQLite fallback for simple DDL)
<version>__<description>_sqlite.sql   # SQLite-specific syntax
```

Versions are zero-padded three-digit strings (`001`, `002`, …).
Add new migration files by incrementing the version number; the runner
automatically picks them up in sorted order.

## 5) Release/deploy flow

1. Run pre-release checks from [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
2. Provision the database and set `DATABASE_URL`
3. Run `make db-migrate-check` in CI to assert the schema is current
4. Deploy backend
5. Deploy frontend with `VITE_API_BASE_URL` pointing to the backend
6. Run smoke validation:

```bash
make smoke-test
```

## 6) Post-deploy verification

- `GET /health` returns `{"status":"ok"}`
- `POST /auth/login` succeeds for known test account
- `GET /model-info` returns thresholds + lineage
- `POST /predict` creates alert
- `GET /alerts/recent` shows created alert
- `GET /monitoring/events` returns recent events

## 7) Operational references

- [RUNBOOK.md](RUNBOOK.md)
- [CHANGELOG.md](CHANGELOG.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
