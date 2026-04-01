# Phase 7 — Deployment Guide

## 1) Recommended Hosting Split (Student-Friendly)
- **Frontend:** Vercel (fast React/Vite deploys)
- **Backend:** Render or Railway (easy Python web service deploy)
- **Data/artifacts:** keep model artifact in backend repo for MVP, then move to object storage later if needed.

## 2) Backend Deployment (Render Example)
1. Push repo to GitHub.
2. Create a new **Web Service** in Render.
3. Set root directory to repository root.
4. Build command:
   ```bash
   pip install -r backend/requirements.txt
   ```
5. Start command:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
6. Add environment variables:
   - `APP_ENV=production`
   - `API_HOST=0.0.0.0`
   - `API_PORT=10000` (or service default)
   - `MODEL_ARTIFACT_PATH=backend/data/artifacts/model.joblib`
   - `METRICS_PATH=backend/data/artifacts/metrics.json`
   - `FEATURE_SCHEMA_PATH=backend/data/artifacts/feature_schema.json`
   - `ALERT_LOGGING_ENABLED=true`
   - `SQLITE_DB_PATH=backend/data/artifacts/alerts.db`

## 3) Frontend Deployment (Vercel Example)
1. Import GitHub repo in Vercel.
2. Set project root to `frontend`.
3. Build command:
   ```bash
   npm install && npm run build
   ```
4. Output directory: `dist`
5. Set env var:
   - `VITE_API_BASE_URL=https://<your-backend-domain>`

## 4) Environment Variable Guidance
Use `.env.example` as the source of truth.

Minimal local `.env`:
```env
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
MODEL_ARTIFACT_PATH=backend/data/artifacts/model.joblib
METRICS_PATH=backend/data/artifacts/metrics.json
FEATURE_SCHEMA_PATH=backend/data/artifacts/feature_schema.json
ALERT_LOGGING_ENABLED=true
SQLITE_DB_PATH=backend/data/artifacts/alerts.db
VITE_API_BASE_URL=http://localhost:8000
```

## 5) Demo Checklist
Before demo/interview:
1. Train model artifacts present in `backend/data/artifacts/`.
2. Backend `/health` and `/model-info` respond successfully.
3. Frontend can submit a sample payload to `/predict`.
4. Recent alerts table updates after inference requests.
5. Metrics panel displays precision/recall/F1/ROC-AUC/FPR.

## 6) Sample Demo Inputs
Use two prepared requests during demo:
- **Likely benign profile:** `service=http`, low `serror_rate`, moderate bytes.
- **Likely suspicious profile:** unusual service/flag, higher error-rate/counter values.

## 7) Portfolio Talking Points
- Built a full-stack AI IDS with reproducible model training and artifact-based inference.
- Designed modular FastAPI service layer (schema validation, prediction service, model registry, optional alert persistence).
- Implemented SOC-style dashboard that surfaces risk, confidence, model metrics, and recent alerts.
- Balanced detection quality and operations tradeoffs (false positives vs false negatives).

## 8) Resume Bullet Suggestions
- Built and deployed an end-to-end AI Intrusion Detection System (FastAPI, scikit-learn, React/TypeScript) that classifies network traffic as benign/malicious and exposes inference + model metrics APIs.
- Implemented a reproducible ML training pipeline (NSL-KDD) with baseline/strong model comparison, artifact persistence (`joblib`), and evaluation reporting (precision, recall, F1, ROC-AUC, FPR).
- Developed a SOC-style security analytics dashboard with real-time inference UX, risk scoring, and recent alert history backed by SQLite.
- Added automated backend tests for API contracts, schema validation, and service-layer behavior to improve reliability and maintainability.
