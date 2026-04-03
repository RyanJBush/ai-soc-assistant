# Phase 1 — Planning: AI Intrusion Detection System

## 1) Concise Project Overview
Build a production-oriented, local-first **AI Intrusion Detection System (AI-IDS)** that classifies network-flow records as **benign** or **malicious**, serves predictions via **FastAPI**, and visualizes alerts and model performance in a **React + TypeScript SOC-style dashboard**.

The MVP emphasizes:
- Practical cyber + ML workflow
- Clean backend service architecture
- Interview-friendly tradeoff explanations (false positives vs false negatives)
- End-to-end demo readiness in 3–7 days

## 2) Target User / Use Case
### Primary persona
- **SOC Analyst (Tier 1/Tier 2)** or junior security engineer monitoring suspicious traffic behavior.

### Core use case
- Analyst inputs (or selects) network-flow-like features from observed traffic.
- System returns:
  - benign/malicious verdict
  - confidence score
  - lightweight rationale (top influential features from model coefficients/feature importance)
- Analyst reviews recent alerts and aggregate model metrics in one dashboard.

## 3) Core Features (MVP Scope)
1. **Reproducible training pipeline** for tabular intrusion dataset.
2. **Binary classification model** (benign vs malicious).
3. **Baseline + stronger model** comparison with saved best artifact.
4. **FastAPI endpoints**:
   - `/health`
   - `/predict`
   - `/model-info` (or `/metrics`)
5. **Frontend dashboard**:
   - traffic-feature form
   - prediction result card
   - model performance panel
   - optional recent alerts table
6. **Optional lightweight SQLite logging** for recent predictions/alerts.
7. **Developer quality tooling**: pytest, ruff, eslint, prettier, Makefile, .env.example.

## 4) Non-Goals (Explicitly Out of Scope for MVP)
- Live packet capture (pcap sniffing in real time).
- High-throughput streaming architecture (Kafka/Spark/Flink).
- Complex deep learning pipelines.
- Enterprise IAM, RBAC, multi-tenant auth.
- Production SIEM integrations (Splunk/ELK/Sentinel connectors).
- Full SOAR/automated response actions.

These are ideal post-MVP extension talking points.

## 5) MVP Success Criteria
Project is considered successful if all are true:
1. End-to-end local demo runs in <10 minutes setup from README.
2. Training script produces model artifact + persisted evaluation metrics.
3. API serves valid predictions with strong schema validation.
4. Dashboard clearly communicates prediction outcome + confidence + key metrics.
5. Evaluation includes precision, recall, F1, ROC-AUC (where applicable), confusion matrix, and false positive rate.
6. Codebase is modular, linted, tested, and interview-explainable.

## 6) Chosen Dataset and Why It Is Practical
### Dataset choice: **NSL-KDD**

### Why NSL-KDD for this MVP
- Widely used benchmark for intrusion-detection education and prototyping.
- Tabular and manageable size for laptop training.
- Includes mixed numeric/categorical features suitable for realistic preprocessing discussion.
- Faster end-to-end iteration than large CICIDS raw captures.
- Easier to complete in 3–7 days while preserving strong recruiter signal.

### Practical handling decision
- Use standard train/test split files (KDDTrain+, KDDTest+).
- Map labels to binary target:
  - `normal` -> benign (0)
  - all attack labels -> malicious (1)

## 7) Binary vs Multiclass Decision
### MVP decision: **Binary classification only**

### Justification
- Directly aligns with SOC triage question: “Is this suspicious?”
- Reduces complexity and risk for one-week delivery.
- Enables stronger polishing of architecture, evaluation, and UX.
- Keeps room for phase-2 extension: multiclass attack family classification using same pipeline.

## 8) Proposed Final Folder Structure
```text
ai-intrusion-detection-system/
  README.md
  .gitignore
  .editorconfig
  .env.example
  Makefile
  backend/
    app/
      api/
        routes_health.py
        routes_predict.py
        routes_model.py
      core/
        config.py
        logging.py
        exceptions.py
      schemas/
        inference.py
        model_info.py
        alert.py
      services/
        prediction_service.py
        model_registry.py
        alert_service.py
      ml/
        preprocessing.py
        trainer.py
        evaluator.py
        feature_map.py
      db/
        base.py
        models.py
        sqlite.py
      main.py
    scripts/
      download_nsl_kdd.py
      train_model.py
    tests/
      test_health.py
      test_predict.py
      test_schemas.py
      test_model_service.py
    data/
      raw/
      processed/
      artifacts/
    pyproject.toml
  frontend/
    src/
      components/
        TrafficInputForm.tsx
        PredictionCard.tsx
        MetricsPanel.tsx
        AlertsTable.tsx
        StatusBanner.tsx
      pages/
        DashboardPage.tsx
      lib/
        api.ts
        format.ts
      types/
        api.ts
      App.tsx
      main.tsx
      index.css
    package.json
    vite.config.ts
    tsconfig.json
    tailwind.config.ts
    postcss.config.js
```

## 9) Implementation Plan for Later Phases
### Phase 2 — Architecture
- Define service boundaries and module responsibilities.
- Finalize inference/request schema contract.
- Lock ML flow and configuration patterns.
- Decide whether SQLite alert logging is in MVP (recommended: yes, lightweight).

### Phase 3 — Setup
- Scaffold backend/frontend directories.
- Initialize Python tooling (pyproject, ruff, pytest).
- Initialize Vite React TypeScript + Tailwind + ESLint + Prettier.
- Add .env.example, Makefile, starter README, data directories.

### Phase 4 — Backend
- Implement FastAPI app + routes.
- Add strict Pydantic validation.
- Build training pipeline:
  - preprocessing pipeline (numeric scaling + categorical encoding)
  - baseline model: Logistic Regression
  - stronger model: Random Forest (or XGBoost only if easily available)
  - model comparison + best artifact save
- Add `/predict` and `/model-info` endpoints.
- Add optional SQLite alert logging and recent alerts endpoint.

### Phase 5 — Frontend
- Build SOC-style dashboard and reusable components.
- Integrate prediction form with API.
- Visualize metrics (Recharts), confusion matrix summary, and recent alerts.
- Handle loading, errors, and empty states cleanly.

### Phase 6 — Testing
- Backend tests for health, predict, schemas, and model service.
- Lint/format scripts for backend/frontend.
- Optional frontend smoke tests (basic render + API mock).

### Phase 7 — Deployment
- Finalize README deployment sections.
- Provide student-friendly hosting guidance:
  - Backend: Render/Railway/Fly.io
  - Frontend: Vercel/Netlify
- Add demo checklist, sample inputs, and interview talking points.

## 10) Why This Project Is High-Signal for Recruiters
- Demonstrates **cross-functional capability**: cybersecurity + ML + backend + frontend.
- Shows realistic SOC thinking (precision/recall tradeoffs, false positives).
- Uses production-like engineering practices (modular services, configs, tests, linting, artifacts).
- Easy to demo live and easy to explain architecture decisions in interviews.
- Naturally extensible (multiclass attacks, streaming ingestion, SIEM integration), showing product-minded roadmap thinking.
