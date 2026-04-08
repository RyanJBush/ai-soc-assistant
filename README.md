# AI SOC Assistant

A production-oriented, portfolio-ready **AI SOC Assistant** for security operations workflows.

It helps analysts:
- score suspicious network/security events,
- triage risk quickly,
- inspect model confidence,
- review recent alert activity in a SOC-style dashboard.

---

## Overview

This project is intentionally positioned as a **SOC analyst support application**, not a generic chatbot.
It combines ML-assisted detection, typed APIs, alert persistence, and an analyst-friendly frontend.

---

## Features

- **ML-assisted scoring** for IDS-style events via `/predict`
- **Risk + confidence outputs** (`low` / `medium` / `high`)
- **Recent alert history** via `/alerts/recent`
- **Model metadata endpoint** via `/model-info`
- **Health visibility** via `/health`
- **SOC dashboard UI** with:
  - summary cards,
  - event scoring form,
  - prediction panel,
  - recent alerts table,
  - model metrics,
  - health + activity panels

---

## Architecture

- **Backend:** FastAPI + Pydantic + service modules
- **ML/Data:** scikit-learn + pandas + numpy + joblib
- **DB:** SQLite local fallback, PostgreSQL-ready architecture
- **Frontend:** React + Vite + TypeScript + Tailwind + Recharts
- **Tooling:** pytest, ruff, eslint, prettier, GitHub Actions

Architecture docs:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API_SPEC.md](docs/API_SPEC.md)
- [docs/PORTS.md](docs/PORTS.md)

---

## Screenshots (Placeholders)

> Add screenshots after deployment demo capture.

- `docs/screenshots/dashboard-overview.png`
- `docs/screenshots/prediction-result.png`
- `docs/screenshots/recent-alerts.png`

---

## Quick Start

### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2) Train model artifacts
```bash
python backend/scripts/train_model.py
```

### 3) Run backend
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Run frontend
```bash
cd frontend
npm ci
npm run dev
```

---

## Docker

Build and run full stack:
```bash
docker compose up --build
```

Stop services:
```bash
docker compose down
```

---

## API

Base URL (local): `http://localhost:8000`

- `GET /health`
- `GET /model-info`
- `POST /predict`
- `GET /alerts/recent`

See full examples in [docs/API_SPEC.md](docs/API_SPEC.md).

---

## Testing

Backend:
```bash
PYTHONPATH=. pytest backend/tests -q
ruff check backend/app
```

Frontend:
```bash
cd frontend
npm run lint
npm run test
npm run build
```

---

## Deployment

Deployment playbook for Render/Railway + Vercel/Netlify:
- [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Limitations

- Baseline model is portfolio-grade, not enterprise production SOC automation.
- SQLite is used by default for local simplicity; PostgreSQL should be used in production.
- Explainability is currently heuristic contributor scoring.
- No enterprise IAM/RBAC or automated response orchestration in MVP.

---

## Resume Highlights

- Built an end-to-end AI SOC Assistant (FastAPI, scikit-learn, React/TypeScript) for event triage and alert visibility.
- Designed typed API contracts and modular service architecture for scoring, metadata, and recent alerts.
- Implemented a SOC-style dashboard surfacing model confidence, risk levels, and recent suspicious activity.
- Added deterministic backend API tests and CI-ready lint/test/build workflow.
