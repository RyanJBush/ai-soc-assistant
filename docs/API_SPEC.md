# AI SOC Assistant — API Specification (Phase 2)

Base URL (local): `http://localhost:8000`

## 1) `GET /health`

### Purpose
Returns service readiness for API, model, and database dependencies.

### 200 Response
```json
{
  "status": "ok",
  "service": "ai-soc-assistant-backend",
  "timestamp": "2026-04-07T12:00:00Z",
  "checks": {
    "api": "ok",
    "model": "ok",
    "database": "ok"
  },
  "request_id": "req_123"
}
```

---

## 2) `GET /model-info`

### Purpose
Exposes model metadata for analyst/engineer observability.

### 200 Response
```json
{
  "model_name": "baseline_intrusion_classifier",
  "model_version": "2026.04.0",
  "algorithm": "RandomForestClassifier",
  "trained_at": "2026-04-07T00:00:00Z",
  "feature_count": 12,
  "risk_thresholds": {
    "medium": 0.55,
    "high": 0.80
  },
  "metrics": {
    "precision": 0.91,
    "recall": 0.88,
    "f1": 0.89,
    "roc_auc": 0.93
  }
}
```

---

## 3) `POST /predict`

### Purpose
Scores a security event and returns risk/confidence with alert decision.

### Request Body
```json
{
  "event_id": "evt-001",
  "timestamp": "2026-04-07T12:00:00Z",
  "duration": 12,
  "protocol_type": "tcp",
  "service": "http",
  "flag": "SF",
  "src_bytes": 242,
  "dst_bytes": 1024,
  "count": 7,
  "srv_count": 5,
  "serror_rate": 0.0,
  "same_srv_rate": 0.71,
  "dst_host_count": 33,
  "dst_host_srv_count": 21
}
```

### 200 Response
```json
{
  "event_id": "evt-001",
  "prediction": "suspicious",
  "probability": 0.87,
  "confidence": 0.87,
  "risk_level": "high",
  "alert": true,
  "recommended_action": "escalate",
  "model_version": "2026.04.0",
  "request_id": "req_456",
  "scored_at": "2026-04-07T12:00:01Z"
}
```

### 422 Response (Validation Error)
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid payload",
  "details": [
    {
      "field": "protocol_type",
      "issue": "Unsupported value"
    }
  ],
  "request_id": "req_456"
}
```

---

## 4) `GET /alerts/recent`

### Purpose
Returns recently generated suspicious alerts for SOC dashboard visibility.

### Query Params
- `limit` (optional, integer, default `20`, max `100`)
- `risk_level` (optional enum: `low|medium|high`)
- `status` (optional enum for future extension)

### 200 Response
```json
{
  "items": [
    {
      "alert_id": 101,
      "event_id": "evt-001",
      "created_at": "2026-04-07T12:00:01Z",
      "risk_level": "high",
      "confidence": 0.87,
      "prediction": "suspicious",
      "status": "new"
    }
  ],
  "count": 1,
  "request_id": "req_789"
}
```

---

## 5) `GET /events` (Optional)

### Purpose
Returns recent scored events (including benign) to support investigation filtering/search.

### Notes
- Optional in MVP if alerts-only persistence is chosen.
- Strong candidate for stretch-goal implementation.

---

## Error Envelope (All Endpoints)

```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "Unexpected service failure",
  "details": null,
  "request_id": "req_xyz",
  "timestamp": "2026-04-07T12:00:01Z"
}
```
