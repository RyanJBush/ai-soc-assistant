import type {
  HealthResponse,
  InferenceRequest,
  InferenceResponse,
  ModelInfoResponse,
  RecentAlertsResponse,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`API ${response.status}: ${detail}`)
  }

  return (await response.json()) as T
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function fetchModelInfo(): Promise<ModelInfoResponse> {
  return request<ModelInfoResponse>('/model-info')
}

export function predict(payload: InferenceRequest): Promise<InferenceResponse> {
  return request<InferenceResponse>('/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchRecentAlerts(limit = 20): Promise<RecentAlertsResponse> {
  return request<RecentAlertsResponse>(`/alerts/recent?limit=${limit}`)
}
