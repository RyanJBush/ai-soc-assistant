# Phase 2 — Architecture: AI Intrusion Detection System

## 1) Architecture Summary
The MVP uses a **local-first, modular monorepo architecture** with clear boundaries between:
- **ML training pipeline** (offline scripts)
- **Inference API** (FastAPI service layer)
- **SOC dashboard UI** (React + TypeScript)
- **Optional persistence** (SQLite for recent alerts)

High-level design:
1. Train model artifact offline from NSL-KDD.
2. Save artifact + metrics JSON in backend artifacts directory.
3. FastAPI loads artifact on startup and exposes inference/metrics endpoints.
4. Frontend calls API and renders prediction + model analytics + recent alerts.

This keeps deployment and explanation simple while preserving production-style separation of concerns.

## 2) Backend Module Responsibilities
### `backend/app/main.py`
- FastAPI app initialization
- Router registration
- Startup checks (model artifact availability)
- Global exception handlers

### `backend/app/api/`
- `routes_health.py`: liveness/readiness endpoints (`/health`)
- `routes_predict.py`: prediction and optional alert logging flow
- `routes_model.py`: model metadata and evaluation metrics endpoint

### `backend/app/schemas/`
- Pydantic request/response contracts:
  - inference input
  - prediction output
  - model metrics payload
  - alert record shape

### `backend/app/services/`
- `prediction_service.py`:
  - feature normalization into model input schema
  - call model registry for inference
  - derive verdict, confidence, risk level, explanation fields
- `model_registry.py`:
  - singleton-like lazy model loader
  - model version + artifact metadata exposure
- `alert_service.py`:
  - insert recent predictions (if `ALERT_LOGGING_ENABLED=true`)
  - fetch latest N alerts

### `backend/app/ml/`
- `preprocessing.py`: deterministic preprocessing pipeline definitions
- `trainer.py`: baseline + stronger model training loop
- `evaluator.py`: metrics calculation + confusion matrix + FPR
- `feature_map.py`: feature order contract used by both training and inference

### `backend/app/core/`
- `config.py`: env-driven settings (paths, thresholds, logging flags)
- `logging.py`: structured logger setup
- `exceptions.py`: custom domain exceptions + API mapping

### `backend/app/db/` (optional but recommended)
- SQLite engine/session setup
- ORM models for alert events
- simple migration-by-create strategy for MVP

## 3) Frontend Component/Page Responsibilities
### `frontend/src/pages/DashboardPage.tsx`
- Top-level orchestration for data fetch and prediction flow
- Composes form, prediction card, metrics panel, and alerts table

### `frontend/src/components/TrafficInputForm.tsx`
- Controlled form for selected IDS features
- Input validation hints and default demo values
- Submits to `/predict`

### `frontend/src/components/PredictionCard.tsx`
- Shows verdict (benign/malicious), confidence, risk badge, and explanation snippets

### `frontend/src/components/MetricsPanel.tsx`
- Displays precision, recall, F1, ROC-AUC, FPR, confusion matrix summary
- Recharts-based visualization for quick analyst interpretation

### `frontend/src/components/AlertsTable.tsx` (if logging enabled)
- Renders recent alerts with timestamp, verdict, confidence, and top features

### `frontend/src/lib/api.ts`
- Typed API client wrappers
- Centralized error mapping

### `frontend/src/types/api.ts`
- Shared TypeScript interfaces for request/response payloads

## 4) ML Flow (Dataset -> Inference)
1. **Dataset ingestion**: load NSL-KDD train/test files.
2. **Label mapping**: `normal` -> 0, attack labels -> 1.
3. **Preprocessing**:
   - categorical features: one-hot encoding
   - numeric features: standard scaling (model-dependent)
4. **Training**:
   - baseline: Logistic Regression
   - stronger: Random Forest
5. **Evaluation** on held-out set:
   - precision, recall, F1, ROC-AUC, confusion matrix, FPR
6. **Selection + persistence**:
   - choose best model by F1 (tie-break on recall)
   - save `model.joblib`, `metrics.json`, `feature_schema.json`
7. **API inference path**:
   - load artifacts once
   - validate incoming payload
   - transform to feature vector using persisted schema
   - generate prediction + probability + explanation fields

## 5) App Flow (User -> API -> UI)
1. User fills `TrafficInputForm` and submits.
2. Frontend sends typed request to `POST /predict`.
3. API validates with Pydantic schema.
4. `prediction_service` transforms input and calls model.
5. API returns structured response:
   - label, confidence, risk_level, top_contributors, timestamp
6. UI renders `PredictionCard` and refreshes recent alerts (if enabled).

## 6) Feature Engineering Strategy
For MVP, use a **curated feature subset** from NSL-KDD that balances realism and form usability:
- `duration`
- `protocol_type`
- `service`
- `flag`
- `src_bytes`
- `dst_bytes`
- `count`
- `srv_count`
- `serror_rate`
- `same_srv_rate`
- `dst_host_count`
- `dst_host_srv_count`

Why this strategy:
- Includes traffic volume, connection behavior, and error-rate signals used in intrusion analytics.
- Keeps frontend form manageable for demo.
- Easy to extend to full feature set later.

## 7) Configuration Strategy
Use environment-based config via `pydantic-settings` (or Pydantic BaseSettings equivalent):
- `APP_ENV`
- `API_HOST`, `API_PORT`
- `MODEL_ARTIFACT_PATH`
- `METRICS_PATH`
- `FEATURE_SCHEMA_PATH`
- `ALERT_LOGGING_ENABLED`
- `SQLITE_DB_PATH`
- `RISK_THRESHOLD_HIGH` (e.g., >=0.80 malicious probability)

Principles:
- No hardcoded paths in business logic.
- Single config object injected/loaded in app startup.
- `.env.example` documents all required variables.

## 8) Error Handling Strategy
- Input validation failures -> 422 with field-specific details.
- Missing model artifact -> 503 with actionable message.
- Prediction runtime failure -> 500 with request-id-safe generic response.
- DB/logging failures should not block core prediction (best-effort logging).
- Unified exception handler returns consistent envelope:
  - `error_code`
  - `message`
  - `details` (optional)
  - `timestamp`

## 9) Optional Alert Logging Strategy (Recommended in MVP)
Use lightweight SQLite table `alerts`:
- `id` (pk)
- `created_at`
- `prediction_label`
- `confidence`
- `risk_level`
- `input_snapshot_json`
- `top_contributors_json`

Endpoint behavior:
- `POST /predict` writes alert event asynchronously/best effort when enabled.
- `GET /alerts/recent?limit=20` returns newest records for dashboard table.

Reason to include:
- Strong product realism with minimal complexity.
- Enables “recent detections” SOC narrative in demo.

## 10) Why This Architecture Is Scalable + Recruiter-Friendly
- **Scalable enough for next steps**: clear seams for queueing, model versioning, and SIEM ingestion later.
- **Maintainable now**: strict module responsibilities + shared schemas.
- **Interview strength**: easy to whiteboard and discuss tradeoffs (latency, false positives, reliability).
- **Portfolio signal**: demonstrates real system thinking beyond just notebook training.
