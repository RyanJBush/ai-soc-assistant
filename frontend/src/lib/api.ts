import type {
  AlertDetailResponse,
  AlertStatus,
  AlertTriageHistoryResponse,
  AnalyticsResponse,
  HealthResponse,
  InferenceRequest,
  InferenceResponse,
  LoginResponse,
  ModelInfoResponse,
  RecentAlertsResponse,
  MonitoringEventsResponse,
  UserPrincipal,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

let bearerToken: string | null = null

export function setAuthToken(token: string | null) {
  bearerToken = token
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(bearerToken ? { Authorization: `Bearer ${bearerToken}` } : {}),
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

export function login(username: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function fetchMe(): Promise<UserPrincipal> {
  return request<UserPrincipal>('/auth/me')
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

export interface AlertsQuery {
  pageSize?: number
  page?: number
  status?: string
  assignedTo?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

export function fetchRecentAlerts(query: AlertsQuery = {}): Promise<RecentAlertsResponse> {
  const params = new URLSearchParams()
  params.set('page_size', String(query.pageSize ?? 10))
  params.set('page', String(query.page ?? 1))
  if (query.status) params.set('status', query.status)
  if (query.assignedTo) params.set('assigned_to', query.assignedTo)
  params.set('sort_by', query.sortBy ?? 'created_at')
  params.set('sort_order', query.sortOrder ?? 'desc')
  return request<RecentAlertsResponse>(`/alerts/recent?${params.toString()}`)
}

export function fetchAlertDetail(alertId: number): Promise<AlertDetailResponse> {
  return request<AlertDetailResponse>(`/alerts/${alertId}`)
}

export function updateAlertStatus(alertId: number, status: AlertStatus): Promise<AlertDetailResponse> {
  return request<AlertDetailResponse>(`/alerts/${alertId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function assignAlert(alertId: number, assignedTo: string): Promise<AlertDetailResponse> {
  return request<AlertDetailResponse>(`/alerts/${alertId}/assignment`, {
    method: 'PATCH',
    body: JSON.stringify({ assigned_to: assignedTo }),
  })
}

export function addAlertNote(alertId: number, note: string): Promise<AlertDetailResponse> {
  return request<AlertDetailResponse>(`/alerts/${alertId}/notes`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  })
}

export function fetchAlertHistory(alertId: number): Promise<AlertTriageHistoryResponse> {
  return request<AlertTriageHistoryResponse>(`/alerts/${alertId}/history`)
}


export function fetchMonitoringEvents(limit = 20): Promise<MonitoringEventsResponse> {
  return request<MonitoringEventsResponse>(`/monitoring/events?limit=${limit}`)
}

export function sendMonitoringEvent(
  eventType: string,
  modelVersion: string,
  payload: Record<string, unknown>,
): Promise<{ status: string }> {
  return request<{ status: string }>(`/monitoring/events`, {
    method: 'POST',
    body: JSON.stringify({ event_type: eventType, model_version: modelVersion, payload }),
  })
}

export function fetchAnalytics(days = 14): Promise<AnalyticsResponse> {
  return request<AnalyticsResponse>(`/analytics?days=${days}`)
}
