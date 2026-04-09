# AI SOC Assistant

Production-style SOC platform for ML-assisted alert scoring, analyst triage workflows, and security operations visibility.

## Quick recruiter snapshot

- ✅ FastAPI backend with typed APIs, RBAC, audit logging, migration-backed persistence
- ✅ React/Vite SOC dashboard with login, triage, status transitions, assignment, and notes
- ✅ PostgreSQL-first architecture with SQLite local fallback
- ✅ Model observability: lineage (hashes), thresholds, monitoring hooks
- ✅ CI checks, coverage gates, and smoke script

---

## Architecture

![Architecture](docs/assets/architecture/ai-soc-assistant-architecture.png)

> Add architecture image files under `docs/assets/architecture/`.

Core docs:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API_SPEC.md](docs/API_SPEC.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [RUNBOOK.md](RUNBOOK.md)

---

## Demo assets

- Dashboard screenshots: `docs/screenshots/`
- Demo GIFs: `docs/assets/demo/`

Example embeds (once assets are added):

![Triage Flow](docs/assets/demo/triage-flow.gif)
![Model Observability](docs/assets/demo/model-observability.gif)

---

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/scripts/train_model.py
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Demo credentials:
- `admin / admin123!`
- `analyst / analyst123!`
- `viewer / viewer123!`

---

## Deployment manifests and env templates

- Render backend: `deploy/render.yaml`
- Vercel frontend: `frontend/vercel.json`
- Env templates:
  - `.env.example`
  - `.env.staging.example`
  - `.env.production.example`

---

## Quality gates

Backend:
```bash
make backend-test-coverage
```

Frontend:
```bash
cd frontend
npm run lint
npm run test:coverage
npm run build
```

Smoke test:
```bash
make smoke-test
```

CI workflow: `.github/workflows/ci.yml`

---

## Why this is production-ready (for portfolio/recruiter review)

1. **Security controls in place**
   - Authenticated endpoints, RBAC, auditability, rate limiting.
2. **Operational realism**
   - DB migrations, structured logs with request IDs, smoke checks, runbook.
3. **Analyst workflow depth**
   - Stateful alert lifecycle, ownership, comments, and triage-focused UI.
4. **ML transparency**
   - Explanations, configurable thresholding, model lineage, monitoring hooks.
5. **Engineering quality**
   - Automated tests, CI checks, coverage gates, clear deployment templates.

---

## Tradeoffs and remaining gaps

- Uses demo/local auth user source (not full enterprise IdP/SSO integration yet).
- Drift/performance monitoring hooks exist, but automated retraining/remediation orchestration is still manual.
- Frontend E2E browser automation can be expanded further (currently integration-level coverage).
- Advanced incident response playbooks and SOAR actions are out of scope for this repo phase.
