# Changelog

All notable changes to this project are documented in this file.

## [0.8.0] - 2026-04-13
### Added
- Bulk Alert Operations + CSV Export phase:
  - `PATCH /alerts/bulk` endpoint — mass-update status for up to 100 alerts in one request; records individual triage events for each; returns `{updated, not_found}`.
  - `GET /alerts/export` streaming CSV endpoint with the same filter/sort parameters as the list view; `Content-Disposition: attachment` for direct download.
  - `AlertService.bulk_update_status` and `export_alerts_csv` service methods.
  - `BulkUpdateRequest` / `BulkUpdateResponse` Pydantic schemas.
  - Correct route ordering so `/alerts/bulk` and `/alerts/export` are matched before `/{alert_id}`.
  - Frontend `AlertsTable` now has per-row checkboxes, select-all, bulk action bar (status picker + Apply / Clear), and Export CSV link.
  - 19 new backend tests (153 total) and 7 new frontend tests (78 total).

## [0.7.0] - 2026-04-13
### Added
- Analytics & Reporting phase:
  - `GET /analytics` endpoint with rolling-window SOC KPIs: total alerts, malicious rate, open count, MTTR, risk-level breakdown, status distribution, and per-day volume timeline.
  - `AnalyticsService` with dual SQLite/PostgreSQL aggregation queries.
  - `AnalyticsPanel` React component with recharts area chart (volume trend), bar chart (risk breakdown), and pie chart (status distribution) plus configurable day-window selector.
  - 14 new backend tests and 11 new frontend tests.

## [0.6.0] - 2026-04-09
### Added
- Phase 6 deployment/recruiter polish artifacts:
  - `deploy/render.yaml`
  - `frontend/vercel.json`
  - `.env.staging.example`, `.env.production.example`
  - release checklist and operator runbook
  - architecture/demo asset placeholders.

### Changed
- README and deployment docs rewritten for production-evaluation clarity.
- Added explicit production readiness and tradeoff sections.

## [0.5.0] - 2026-04-09
### Added
- CI coverage gates, integration test, E2E workflow test, smoke test script.

## [0.4.0] - 2026-04-09
### Added
- JWT auth, RBAC, audit logs, alert lifecycle workflows, model observability hooks.
