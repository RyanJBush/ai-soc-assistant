import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DashboardPage } from './DashboardPage'

const mockApi = vi.hoisted(() => ({
  login: vi.fn(),
  setAuthToken: vi.fn(),
  fetchMe: vi.fn(),
  fetchHealth: vi.fn(),
  fetchModelInfo: vi.fn(),
  fetchRecentAlerts: vi.fn(),
  predict: vi.fn(),
  fetchAlertDetail: vi.fn(),
  fetchAlertHistory: vi.fn(),
  updateAlertStatus: vi.fn(),
  assignAlert: vi.fn(),
  addAlertNote: vi.fn(),
  fetchAnalytics: vi.fn().mockResolvedValue({
    days: 14,
    total_alerts: 0,
    malicious_count: 0,
    benign_count: 0,
    open_count: 0,
    malicious_rate: 0,
    avg_resolution_hours: null,
    by_risk_level: { low: 0, medium: 0, high: 0, critical: 0 },
    by_status: { new: 0, acknowledged: 0, escalated: 0, resolved: 0 },
    alert_volume_by_day: [],
  }),
  bulkUpdateAlerts: vi.fn().mockResolvedValue({ updated: 0, not_found: [] }),
  exportAlertsUrl: vi.fn().mockReturnValue('http://localhost:8000/alerts/export'),
}))

vi.mock('../lib/api', () => ({
  ...mockApi,
}))

describe('DashboardPage integration', () => {
  it('supports login and alert status triage flow', async () => {
    mockApi.login.mockResolvedValue({ access_token: 'token', role: 'analyst', token_type: 'bearer', expires_at: 'x' })
    mockApi.fetchMe.mockResolvedValue({ username: 'analyst', role: 'analyst' })
    mockApi.fetchHealth.mockResolvedValue({ status: 'ok' })
    mockApi.fetchModelInfo.mockResolvedValue({
      model_name: 'rf',
      model_version: 'rf-v2',
      selected_features: ['src_bytes'],
      training_rows: 1,
      test_rows: 1,
      metrics: { precision: 1 },
      thresholds: {
        malicious_decision_threshold: 0.5,
        risk_threshold_medium: 0.5,
        risk_threshold_high: 0.8,
        risk_threshold_critical: 0.93,
      },
      lineage: { artifact_path: 'a', artifact_sha256: 'abc', metrics_path: 'm', metrics_sha256: 'def' },
      monitoring: { monitoring_endpoint: '/monitoring/events', supported_event_types: ['drift.feature_shift'] },
      explainability: {
        supported_methods: ['feature_importance', 'heuristic'],
        primary_method: 'feature_importance+sensitivity',
        description: 'Blended feature importance and sensitivity analysis.',
      },
    })
    mockApi.fetchRecentAlerts.mockResolvedValue({
      alerts: [
        {
          id: 1,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
          prediction_label: 'malicious',
          confidence: 0.9,
          risk_level: 'high',
          status: 'new',
          assigned_to: null,
          top_contributors: [{ feature: 'src_bytes', impact: 1 }],
          input_snapshot: {},
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
    })
    mockApi.fetchAlertDetail.mockResolvedValue({
      alert: {
        id: 1,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        prediction_label: 'malicious',
        confidence: 0.9,
        risk_level: 'high',
        status: 'new',
        assigned_to: null,
        top_contributors: [{ feature: 'src_bytes', impact: 1 }],
        input_snapshot: {},
      },
      notes: [],
    })
    mockApi.fetchAlertHistory.mockResolvedValue({ alert_id: 1, events: [] })
    mockApi.updateAlertStatus.mockResolvedValue({})

    render(<DashboardPage />)

    fireEvent.click(screen.getByText('Sign in'))

    await waitFor(() => expect(screen.getByText(/Logged in as analyst/)).toBeInTheDocument())

    // Wait for the alert table row to render then click it to open the detail panel
    await waitFor(() => expect(screen.getByText('malicious')).toBeInTheDocument())
    fireEvent.click(screen.getByText('malicious'))

    // Detail panel heading should now be visible
    await waitFor(() => expect(screen.getByText('Alert #1')).toBeInTheDocument())

    // Click the "acknowledged" transition button
    fireEvent.click(screen.getByRole('button', { name: 'acknowledged' }))

    await waitFor(() => expect(mockApi.updateAlertStatus).toHaveBeenCalledWith(1, 'acknowledged'))
  })
})
