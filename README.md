# AI Intrusion Detection System (MVP)

A production-oriented, portfolio-ready AI IDS that combines:
- **ML detection pipeline** (NSL-KDD, binary classification)
- **FastAPI backend** (`/health`, `/predict`, `/model-info`, `/alerts/recent`)
- **React + TypeScript dashboard** for SOC-style analytics

## Tech Stack
- Backend: FastAPI, Pydantic, scikit-learn, pandas, numpy, joblib, uvicorn
- Frontend: React, Vite, TypeScript, Tailwind CSS, Recharts
- Quality: pytest, ruff, eslint, prettier

## Project Structure
```text
backend/
  app/
  scripts/
  tests/
  data/
frontend/
  src/
```

## Local Setup
### 1) Backend
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2) Prepare Dataset + Train
Place these files in `backend/data/raw`:
- `KDDTrain+.txt`
- `KDDTest+.txt`

Then run:
```bash
python backend/scripts/train_model.py
```

### 3) Run Backend
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Run Frontend
```bash
cd frontend
npm install
npm run dev
```

## Quick API Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/model-info
```

Prediction example:
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

## Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- backend/frontend hosting steps
- environment variable guidance
- demo checklist
- portfolio talking points
- resume bullets
