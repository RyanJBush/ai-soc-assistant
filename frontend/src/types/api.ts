export type RiskLevel = 'low' | 'medium' | 'high'
export type AlertStatus = 'new' | 'acknowledged' | 'escalated' | 'resolved'

export interface InferenceRequest {
  duration: number
  protocol_type: 'tcp' | 'udp' | 'icmp'
  service: string
  flag: string
  src_bytes: number
  dst_bytes: number
  count: number
  srv_count: number
  serror_rate: number
  same_srv_rate: number
  dst_host_count: number
  dst_host_srv_count: number
}

export interface TopContributor {
  feature: string
  impact: number
}

export interface InferenceResponse {
  prediction_label: 'benign' | 'malicious'
  malicious_probability: number
  confidence: number
  risk_level: RiskLevel
  top_contributors: TopContributor[]
  model_version: string
  timestamp: string
}

export interface ModelThresholds {
  malicious_decision_threshold: number
  risk_threshold_medium: number
  risk_threshold_high: number
  risk_threshold_critical: number
}

export interface ModelLineage {
  artifact_path: string
  artifact_sha256: string
  metrics_path: string
  metrics_sha256: string
  registered_at?: string
}

export interface MonitoringHookInfo {
  monitoring_endpoint: string
  supported_event_types: string[]
}

export interface ModelInfoResponse {
  model_name: string
  model_version: string
  selected_features: string[]
  training_rows: number
  test_rows: number
  metrics: Record<string, number>
  thresholds: ModelThresholds
  lineage: ModelLineage
  monitoring: MonitoringHookInfo
}

export interface AlertNote {
  id: number
  alert_id: number
  author: string
  note: string
  created_at: string
}

export type TriageEventType = 'status_change' | 'assignment_change'

export interface AlertTriageEvent {
  id: number
  alert_id: number
  actor: string
  event_type: TriageEventType
  old_value: string | null
  new_value: string
  note: string | null
  created_at: string
}

export interface AlertTriageHistoryResponse {
  alert_id: number
  events: AlertTriageEvent[]
}

export interface AlertRecord {
  id: number
  created_at: string
  updated_at: string
  prediction_label: string
  confidence: number
  risk_level: string
  malicious_probability?: number
  model_version?: string
  status: AlertStatus
  assigned_to?: string | null
  top_contributors: TopContributor[]
  input_snapshot: Record<string, unknown>
}

export interface AlertDetailResponse {
  alert: AlertRecord
  notes: AlertNote[]
}

export interface RecentAlertsResponse {
  alerts: AlertRecord[]
  total: number
  page: number
  page_size: number
}

export interface MonitoringEventRecord {
  id: number
  event_type: string
  model_version: string
  payload: Record<string, unknown>
  created_at: string
}

export interface MonitoringEventsResponse {
  events: MonitoringEventRecord[]
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error' | string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_at: string
  role: 'admin' | 'analyst' | 'viewer'
}

export interface UserPrincipal {
  username: string
  role: 'admin' | 'analyst' | 'viewer'
}
