# AI SOC Assistant — Phase 2 Architecture

## 1) Monorepo Layout

```text
ai-soc-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── schemas/
│   │   └── services/
│   ├── data/
│   ├── scripts/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── types/
│   └── public/
├── docs/
│   ├── PHASE_1_PLANNING.md
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   └── PORTS.md
└── .github/
    └── workflows/
```

---

## 2) Backend Module Architecture

### `app/api`
- FastAPI route handlers and router registration.
- Owns endpoint orchestration only (no business logic in routes).
- Targets endpoints: `/health`, `/model-info`, `/predict`, `/alerts/recent`, optional `/events`.

### `app/core`
- Application settings (env-driven), logging, request-ID middleware, error envelopes.
- Centralized exception handling and shared constants.
- Security-relevant defaults (CORS allowlist, safe config parsing, strict validation toggles).

### `app/db`
- Database engine/session management.
- ORM models and repository helpers.
- PostgreSQL-ready connection handling with SQLite fallback for local/dev.

### `app/ml`
- Data preprocessing and feature mapping.
- Training/serialization/loading of baseline model artifacts.
- Inference helper utilities for confidence and threshold-based risk mapping.

### `app/services`
- Business workflows: prediction scoring, alert creation, retrieval, status handling (future).
- Decouples domain logic from transport layer.

### `app/schemas`
- Pydantic request/response contracts.
- Input validation, typed responses, and version-stable API DTOs.

---

## 3) Frontend Module Architecture

### `src/components`
Reusable UI units: summary cards, alerts table, risk badges, model info panel, health indicators.

### `src/pages`
Route-level composition (e.g., `DashboardPage`) that assembles analyst workflows.

### `src/lib`
Typed API client, fetch wrappers, request ID propagation, and common utilities.

### `src/hooks`
React hooks for data fetching, polling, and mutation state (`usePredict`, `useRecentAlerts`, `useHealth`).

### `src/types`
TypeScript contracts mirroring backend schemas for strongly typed integration.

---

## 4) Core Domain Entities

1. **SecurityEvent**
   - Inbound telemetry record for scoring.
   - Fields: timestamp, src/dst metadata, protocol/service stats, behavioral features.

2. **PredictionResult**
   - ML scoring output.
   - Fields: class label, probability, confidence, risk_level, alert_decision, model_version.

3. **AlertRecord**
   - Persisted suspicious event summary.
   - Fields: id, created_at, severity/risk_level, confidence, status, event snapshot, analyst_note (future).

4. **AnalystSummary**
   - Aggregated data for SOC dashboard.
   - Fields: counts by risk/status, recent alert list, model health metadata, service health.

---

## 5) Backend Processing Flow

```text
event input
  -> request validation (Pydantic)
  -> preprocessing + feature mapping
  -> model scoring (probability + class)
  -> risk/confidence derivation
  -> alert decision
  -> persistence (alerts/events)
  -> API response (typed payload)
```

### Flow Notes
- Validation happens before ML execution to protect model/service stability.
- Risk levels derive from configurable thresholds (e.g., low/medium/high).
- Persistence should be non-blocking where possible for UX latency control.

---

## 6) System Cross-Cutting Concerns

### Security/Validation
- Strict schema validation with bounded numeric ranges and enums.
- Configurable CORS (`CORS_ALLOWED_ORIGINS`) with deny-by-default mindset.
- Environment variables loaded from `.env` + runtime environment; no secrets hardcoded.

### Observability
- Structured JSON logs with request IDs.
- Health checks split by service/model/database readiness.
- Predict endpoint logs model version and latency metadata.

### Reliability
- Graceful startup checks for model artifacts and DB connectivity.
- Clear exception mapping and stable error response envelope.
- Local SQLite for reproducibility; PostgreSQL for production deployments.

---

## 7) Phase 2 Decision Rationale

- **SOC-first UX:** Design prioritizes triage workflows, not chatbot conversation.
- **Portfolio realism:** Includes APIs, persistence, logging, and deployment-friendly layout.
- **ATS relevance:** Stack explicitly matches AI/ML + backend + security engineering expectations.
- **Extensibility:** Entity and module boundaries support stretch goals (notes, status transitions, explainability).
