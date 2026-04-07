# AI SOC Assistant — Phase 1 Planning

## 1) Target Users

### Primary User: SOC Analyst (Tier 1 / Tier 2)
- **Goal:** Triage suspicious events quickly and consistently.
- **Pain points:** Alert fatigue, noisy detections, context switching across tools, and unclear model outputs.
- **What this product must deliver:**
  - Fast risk scoring for incoming events.
  - Clear confidence + risk-level labeling (not just binary outputs).
  - Recent alert history in an analyst-friendly dashboard.
  - Explainable, compact context to support escalation decisions.

### Secondary User: Security Engineer / Detection Engineer
- **Goal:** Validate detection quality and tune operational thresholds.
- **Pain points:** Weak observability into model behavior, brittle pipelines, and unclear false-positive patterns.
- **What this product must deliver:**
  - Model metadata endpoint and health visibility.
  - Reproducible local/dev environment and testable APIs.
  - Modular architecture for adding features (status updates, notes, explainability).

### Portfolio/Business User: Hiring Manager / Recruiter Viewer
- **Goal:** Assess technical depth, product thinking, and production readiness quickly.
- **Pain points:** Many projects are toy demos without architecture, testing, or deployment rigor.
- **What this product must deliver:**
  - Clear SOC-oriented narrative (not a generic chatbot).
  - Modern full-stack implementation with ATS-relevant tooling.
  - Clean documentation, CI/CD, Docker workflow, and security-minded design.

---

## 2) MVP Definition (Phase 1 Scope Contract)

The MVP focuses on **core SOC triage support** with end-to-end flow from event input to alert visibility.

### MVP Capabilities
1. **Load or ingest sample security events** (IDS-style network/security telemetry records).
2. **Classify/score events** using a baseline ML model.
3. **Surface suspicious alerts** using configurable threshold logic.
4. **Display risk level and model confidence** for analyst trust and prioritization.
5. **Provide recent alert history** for quick situational awareness.
6. **Expose model metadata and service health** to support operational confidence.

### MVP Success Criteria
- Analyst can submit or review an event and receive a score + risk classification in seconds.
- High-risk/suspicious events are persisted and visible in recent alerts.
- Dashboard presents status and context clearly enough for non-technical reviewers.
- API contracts are stable and typed for backend/frontend integration.

---

## 3) MVP Features List (Implementation-Oriented)

### Backend MVP Features
- `POST /predict` for event scoring.
- `GET /alerts/recent` for latest suspicious alerts.
- `GET /model-info` for model artifact metadata.
- `GET /health` for service/database/model readiness.
- Basic persistence for alerts (PostgreSQL-ready with SQLite fallback).

### Frontend MVP Features
- SOC dashboard with:
  - Alert/risk summary cards.
  - Recent alerts table.
  - Event scoring input form.
  - Prediction output panel (score, confidence, risk label, decision).
  - Health/model status panel.

### Product/Engineering MVP Features
- Strong request/response validation.
- Structured logging and request IDs.
- Reproducible local setup via Docker Compose.
- Baseline CI checks (lint + test + build).

---

## 4) Stretch Goals (Post-MVP)

1. **Analyst notes** attached to alert records for handoff and collaboration.
2. **Alert lifecycle/status changes** (new, investigating, escalated, resolved).
3. **Event filtering/search** by risk, protocol, source/destination, or time range.
4. **Explainability panel** (top feature contributions / interpretable reason codes).
5. **Incident summary generation** for shift handoff and reporting.

These are intentionally staged after MVP to protect delivery quality and timeline.

---

## 5) Non-Goals (For Realistic Portfolio Scope)

- Building a full SIEM replacement.
- Real-time packet capture/stream processing at enterprise scale.
- Multi-tenant RBAC with enterprise IAM integrations in v1.
- Autonomous response actions (e.g., auto-blocking firewall rules).
- Advanced MLOps platform (drift monitoring, auto-retraining pipelines) in initial release.

Keeping these out of scope preserves focus on a strong, deployable, recruiter-friendly MVP.

---

## 6) Assumptions

1. **Data assumption:** Initial dataset is synthetic/sample IDS-like data and may not represent all production traffic distributions.
2. **Model assumption:** Baseline classifier is suitable for demonstration quality, not production SOC decision automation.
3. **Environment assumption:** Local development primarily uses Docker Compose; deployment targets managed PaaS.
4. **Database assumption:** SQLite is acceptable for local demo/testing; PostgreSQL is target for staged/production use.
5. **User assumption:** Primary workflow is analyst-assisted triage, not fully autonomous SOC operations.

---

## 7) Risks and Tradeoffs

### Key Risks
- **False positives/negatives risk:** Baseline models can over/under-alert and impact credibility.
- **Data quality risk:** Limited or synthetic training data may reduce realism.
- **Explainability gap risk:** Without interpretability cues, model trust may be lower for analysts.
- **Scope creep risk:** Adding too many security features early may reduce overall quality.
- **Demo-vs-production risk:** Portfolio system can appear production-ready but still lack enterprise controls.

### Planned Mitigations
- Start with transparent thresholds and confidence bands.
- Document model limitations clearly in API and README.
- Add deterministic tests around scoring/alert persistence.
- Keep modular boundaries so stretch goals can be added incrementally.
- Explicitly separate MVP from future enterprise enhancements.

### Tradeoffs Chosen for MVP
- **Speed over sophistication:** Baseline model first, explainability later.
- **Clarity over feature volume:** Strong UX/API fundamentals before advanced workflows.
- **Local reproducibility over cloud complexity:** Docker-first to improve reviewer experience.

---

## 8) Phase 1 Exit Criteria

Phase 1 is complete when:
- Target users and user-value mapping are defined.
- MVP and stretch goals are explicitly scoped.
- Non-goals, assumptions, and risks are documented.
- The plan can be directly used to begin Phase 2 architecture design.
