import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { AnalyticsResponse } from '../../types/api'
import { AnalyticsPanel } from '../AnalyticsPanel'

const makeAnalytics = (overrides: Partial<AnalyticsResponse> = {}): AnalyticsResponse => ({
  days: 14,
  total_alerts: 100,
  malicious_count: 40,
  benign_count: 60,
  open_count: 25,
  malicious_rate: 0.4,
  avg_resolution_hours: 3.5,
  by_risk_level: { low: 30, medium: 40, high: 20, critical: 10 },
  by_status: { new: 15, acknowledged: 10, escalated: 5, resolved: 70 },
  alert_volume_by_day: [
    { date: '2024-01-14', count: 8, malicious: 3 },
    { date: '2024-01-15', count: 12, malicious: 5 },
  ],
  ...overrides,
})

describe('AnalyticsPanel', () => {
  it('shows loading state when analytics is null', () => {
    render(<AnalyticsPanel analytics={null} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText(/Analytics loading/i)).toBeInTheDocument()
  })

  it('renders the section heading', () => {
    render(<AnalyticsPanel analytics={makeAnalytics()} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByRole('heading', { name: /analytics/i })).toBeInTheDocument()
  })

  it('renders total alerts KPI card', () => {
    render(<AnalyticsPanel analytics={makeAnalytics({ total_alerts: 42 })} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('Total Alerts')).toBeInTheDocument()
  })

  it('renders malicious rate as percentage', () => {
    render(<AnalyticsPanel analytics={makeAnalytics({ malicious_rate: 0.4 })} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText('40.0%')).toBeInTheDocument()
  })

  it('renders open alerts count', () => {
    render(<AnalyticsPanel analytics={makeAnalytics({ open_count: 7 })} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('renders avg resolution in hours', () => {
    render(<AnalyticsPanel analytics={makeAnalytics({ avg_resolution_hours: 2.75 })} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText('2.8h')).toBeInTheDocument()
  })

  it('renders em dash when avg_resolution_hours is null', () => {
    render(<AnalyticsPanel analytics={makeAnalytics({ avg_resolution_hours: null })} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('shows empty state when no volume data', () => {
    render(
      <AnalyticsPanel
        analytics={makeAnalytics({ alert_volume_by_day: [] })}
        days={14}
        onDaysChange={vi.fn()}
      />,
    )
    expect(screen.getByText(/No alerts in this window/i)).toBeInTheDocument()
  })

  it('renders day window buttons', () => {
    render(<AnalyticsPanel analytics={makeAnalytics()} days={14} onDaysChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: '7d' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '14d' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '30d' })).toBeInTheDocument()
  })

  it('calls onDaysChange when window button is clicked', async () => {
    const onDaysChange = vi.fn()
    render(<AnalyticsPanel analytics={makeAnalytics()} days={14} onDaysChange={onDaysChange} />)
    await userEvent.click(screen.getByRole('button', { name: '30d' }))
    expect(onDaysChange).toHaveBeenCalledWith(30)
  })

  it('highlights the active days button', () => {
    render(<AnalyticsPanel analytics={makeAnalytics()} days={14} onDaysChange={vi.fn()} />)
    const activeButton = screen.getByRole('button', { name: '14d' })
    expect(activeButton.className).toContain('bg-cyan-600')
  })
})
