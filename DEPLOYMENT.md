# Deployment Guide

This guide covers **backend deployment (Render or Railway)** and **frontend deployment (Vercel or Netlify)**.

---

## 1) Prerequisites

- GitHub repository with this project
- Model artifacts available in `backend/data/artifacts/` (or custom artifact storage strategy)
- Environment variables configured per platform

---

## 2) Docker Smoke Test (Before Cloud Deploy)

Run locally:
```bash
docker compose up --build
```

Smoke checks:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/model-info
```

Prediction check:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 0,
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 181,
    "dst_bytes": 5450,
    "count": 8,
    "srv_count": 8,
    "serror_rate": 0.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 20,
    "dst_host_srv_count": 20
  }'
```

Stop:
```bash
docker compose down
```

---

## 3) Backend Deployment — Render

1. Create a new **Web Service** from your GitHub repo.
2. Set build command:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set start command:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Set environment variables:
   - `APP_ENV=production`
   - `API_HOST=0.0.0.0`
   - `API_PORT=8000`
   - `MODEL_ARTIFACT_PATH=backend/data/artifacts/model.joblib`
   - `METRICS_PATH=backend/data/artifacts/metrics.json`
   - `FEATURE_SCHEMA_PATH=backend/data/artifacts/feature_schema.json`
   - `ALERT_LOGGING_ENABLED=true`
   - `SQLITE_DB_PATH=backend/data/artifacts/alerts.db`
   - `CORS_ALLOWED_ORIGINS=https://<your-frontend-domain>`

---

## 4) Backend Deployment — Railway

1. Create a new project and connect the repository.
2. Configure service with the same build/start commands:
   - Build: `pip install -r backend/requirements.txt`
   - Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables listed in the Render section.
4. Confirm health endpoint:
   - `https://<railway-backend-domain>/health`

---

## 5) Frontend Deployment — Vercel

1. Import the repository into Vercel.
2. Set root directory to `frontend`.
3. Build command: `npm run build`
4. Output directory: `dist`
5. Set env var:
   - `VITE_API_BASE_URL=https://<backend-domain>`

---

## 6) Frontend Deployment — Netlify

1. Create new site from Git provider.
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Set environment variable:
   - `VITE_API_BASE_URL=https://<backend-domain>`

---

## 7) Production Readiness Checklist

- [ ] Backend `/health` returns `{"status":"ok"}`
- [ ] `/model-info` returns model metadata
- [ ] `/predict` works from deployed frontend
- [ ] `/alerts/recent` updates after prediction
- [ ] CORS allows only deployed frontend domain
- [ ] API key enabled for protected routes if required

---

## 8) Notes and Tradeoffs

- SQLite is suitable for portfolio demos and low-volume workloads.
- For production-like usage, migrate alert storage to managed PostgreSQL.
- Keep model artifacts versioned and immutable per release.
