# Changelog

All notable changes to this project are documented in this file.

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
