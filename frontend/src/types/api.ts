export type RiskLevel = 'low' | 'medium' | 'high'

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

export interface ModelInfoResponse {
  model_name: string
  model_version: string
  selected_features: string[]
  training_rows: number
  test_rows: number
  metrics: Record<string, number>
}

export interface AlertRecord {
  id: number
  created_at: string
  prediction_label: string
  confidence: number
  risk_level: string
  input_snapshot: Record<string, unknown>
}

export interface RecentAlertsResponse {
  alerts: AlertRecord[]
}
