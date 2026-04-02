import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { AlertRecord } from '../../types/api'
import { AlertsTable } from '../AlertsTable'

const makeAlert = (overrides: Partial<AlertRecord> = {}): AlertRecord => ({
  id: 1,
  created_at: '2024-01-15T10:30:00Z',
  prediction_label: 'benign',
  confidence: 0.92,
  risk_level: 'low',
  input_snapshot: { protocol_type: 'tcp' },
  ...overrides,
})

describe('AlertsTable', () => {
  it('renders empty state message when alerts is empty', () => {
    render(<AlertsTable alerts={[]} />)
    expect(screen.getByText('No alerts yet.')).toBeInTheDocument()
  })

  it('renders the section heading', () => {
    render(<AlertsTable alerts={[]} />)
    expect(screen.getByRole('heading', { name: 'Recent Alerts' })).toBeInTheDocument()
  })

  it('does not render a table when alerts is empty', () => {
    render(<AlertsTable alerts={[]} />)
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('renders a table row for each alert', () => {
    const alerts = [makeAlert({ id: 1 }), makeAlert({ id: 2 }), makeAlert({ id: 3 })]
    render(<AlertsTable alerts={alerts} />)
    const rows = screen.getAllByRole('row')
    // header row + 3 data rows
    expect(rows).toHaveLength(4)
  })

  it('shows the prediction label (CSS uppercase class applied)', () => {
    render(<AlertsTable alerts={[makeAlert({ prediction_label: 'malicious' })]} />)
    // DOM text is lowercase; CSS class "uppercase" handles the visual transform
    expect(screen.getByText('malicious')).toBeInTheDocument()
    const el = screen.getByText('malicious')
    expect(el.className).toMatch(/uppercase/)
  })

  it('shows confidence as a percentage', () => {
    render(<AlertsTable alerts={[makeAlert({ confidence: 0.876 })]} />)
    expect(screen.getByText('87.60%')).toBeInTheDocument()
  })

  it('shows risk level (CSS uppercase class applied)', () => {
    render(<AlertsTable alerts={[makeAlert({ risk_level: 'high' })]} />)
    // DOM text is lowercase; CSS class "uppercase" handles the visual transform
    expect(screen.getByText('high')).toBeInTheDocument()
    const el = screen.getByText('high')
    expect(el.className).toMatch(/uppercase/)
  })

  it('renders table column headers', () => {
    render(<AlertsTable alerts={[makeAlert()]} />)
    expect(screen.getByText('Time')).toBeInTheDocument()
    expect(screen.getByText('Label')).toBeInTheDocument()
    expect(screen.getByText('Confidence')).toBeInTheDocument()
    expect(screen.getByText('Risk')).toBeInTheDocument()
  })
})
