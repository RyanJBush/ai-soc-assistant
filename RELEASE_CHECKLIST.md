# Release Checklist

## Pre-release
- [ ] `ruff check backend/app backend/tests`
- [ ] `pytest backend/tests -q`
- [ ] `make smoke-test`
- [ ] Frontend checks (`npm run lint`, `npm run test:coverage`, `npm run build`)
- [ ] Verify `.env.production.example` values are set in target platform secrets

## Deployment
- [ ] Apply deployment manifest (`deploy/render.yaml`) or equivalent platform config
- [ ] Confirm DB migrations succeed on startup logs
- [ ] Validate `/health`, `/model-info`, `/auth/login`
- [ ] Validate analyst flow: login -> predict -> alert status update

## Post-release
- [ ] Review monitoring events (`/monitoring/events`) for first 30 minutes
- [ ] Confirm audit log ingestion and request-id traceability in logs
- [ ] Record release notes in `CHANGELOG.md`
