import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { AlertDetailResponse, AlertTriageEvent } from '../../types/api'
import { AlertDetailPanel } from '../AlertDetailPanel'

const makeDetail = (overrides: Partial<AlertDetailResponse['alert']> = {}): AlertDetailResponse => ({
  alert: {
    id: 42,
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T11:00:00Z',
    prediction_label: 'malicious',
    confidence: 0.9,
    risk_level: 'high',
    malicious_probability: 0.9,
    model_version: 'v1.0',
    status: 'new',
    assigned_to: null,
    top_contributors: [{ feature: 'src_bytes', impact: 0.8 }],
    input_snapshot: { protocol_type: 'tcp', src_bytes: 100 },
    ...overrides,
  },
  notes: [],
})

const noopProps = {
  onUpdateStatus: vi.fn(),
  onAssign: vi.fn(),
  onAddNote: vi.fn(),
}

describe('AlertDetailPanel', () => {
  it('shows placeholder when no detail is provided', () => {
    render(<AlertDetailPanel detail={null} triageHistory={[]} role="analyst" {...noopProps} />)
    expect(screen.getByText('Select an alert row to view triage details.')).toBeInTheDocument()
  })

  it('renders alert id and status badge', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="viewer" {...noopProps} />)
    expect(screen.getByText('Alert #42')).toBeInTheDocument()
    expect(screen.getByText('new')).toBeInTheDocument()
  })

  it('renders top contributors', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="viewer" {...noopProps} />)
    expect(screen.getByText('src_bytes: 80.0%')).toBeInTheDocument()
  })

  it('shows triage actions for analyst role', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="analyst" {...noopProps} />)
    expect(screen.getByText('Status transition')).toBeInTheDocument()
    expect(screen.getByText('acknowledged')).toBeInTheDocument()
  })

  it('hides triage actions for viewer role', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="viewer" {...noopProps} />)
    expect(screen.queryByText('Status transition')).not.toBeInTheDocument()
  })

  it('renders triage history events', () => {
    const events: AlertTriageEvent[] = [
      {
        id: 1,
        alert_id: 42,
        actor: 'analyst-bob',
        event_type: 'status_change',
        old_value: 'new',
        new_value: 'acknowledged',
        note: null,
        created_at: '2024-01-15T11:00:00Z',
      },
    ]
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={events} role="viewer" {...noopProps} />)
    expect(screen.getByText('Triage history')).toBeInTheDocument()
    expect(screen.getByText('analyst-bob')).toBeInTheDocument()
  })

  it('does not render triage history section when events are empty', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="viewer" {...noopProps} />)
    expect(screen.queryByText('Triage history')).not.toBeInTheDocument()
  })

  it('shows input snapshot toggle button', () => {
    render(<AlertDetailPanel detail={makeDetail()} triageHistory={[]} role="viewer" {...noopProps} />)
    expect(screen.getByText('Show input snapshot')).toBeInTheDocument()
  })
})
