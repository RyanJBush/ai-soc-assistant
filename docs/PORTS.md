# AI SOC Assistant — Ports and Runtime Map

## Local Development Ports

| Service | Port | Protocol | Purpose |
|---|---:|---|---|
| Frontend (Vite dev server) | 5173 | HTTP | SOC dashboard UI in development |
| Backend (FastAPI/Uvicorn) | 8000 | HTTP | API server for health, model-info, predict, alerts |
| PostgreSQL (optional local) | 5432 | TCP | Production-parity local database |

---

## Docker Compose Port Mapping (Proposed)

| Container | Internal Port | Host Port | Notes |
|---|---:|---:|---|
| `frontend` | 5173 | 5173 | Vite or static server |
| `backend` | 8000 | 8000 | FastAPI app |
| `db` | 5432 | 5432 | Postgres service (optional in local quick-start) |

---

## Environment Variables (Port Related)

- `FRONTEND_PORT=5173`
- `BACKEND_PORT=8000`
- `DATABASE_URL=postgresql+psycopg://...` (or SQLite URL fallback)
- `API_BASE_URL=http://localhost:8000`

---

## Connectivity Expectations

- Frontend calls backend via `API_BASE_URL`.
- Backend talks to SQLite by default in local mode.
- Backend talks to PostgreSQL when `DATABASE_URL` is provided.
- CORS should allow frontend origin(s) only (e.g., `http://localhost:5173`).

---

## Deployment Notes

- If deployed separately:
  - Frontend uses public backend URL via environment configuration.
  - Backend should sit behind TLS termination and reverse proxy.
- Health endpoint (`/health`) should be used for platform probes.
