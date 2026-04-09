import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { AlertRecord } from '../../types/api'
import { AlertsTable } from '../AlertsTable'

const makeAlert = (overrides: Partial<AlertRecord> = {}): AlertRecord => ({
  id: 1,
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-01-15T10:30:00Z',
  prediction_label: 'benign',
  confidence: 0.92,
  risk_level: 'low',
  status: 'new',
  assigned_to: null,
  top_contributors: [],
  input_snapshot: { protocol_type: 'tcp' },
  ...overrides,
})

const defaultProps = {
  alerts: [] as AlertRecord[],
  total: 0,
  page: 1,
  pageSize: 10,
  statusFilter: '',
  assignedToFilter: '',
  sortBy: 'created_at',
  sortOrder: 'desc' as const,
  onPageChange: vi.fn(),
  onStatusFilterChange: vi.fn(),
  onAssignedToFilterChange: vi.fn(),
  onSortChange: vi.fn(),
  onSelectAlert: vi.fn(),
}

describe('AlertsTable', () => {
  it('renders empty state message when alerts is empty', () => {
    render(<AlertsTable {...defaultProps} />)
    expect(screen.getByText('No alerts found for this filter.')).toBeInTheDocument()
  })

  it('renders the section heading', () => {
    render(<AlertsTable {...defaultProps} />)
    expect(screen.getByRole('heading', { name: 'Recent Alerts' })).toBeInTheDocument()
  })

  it('renders a table row for each alert', () => {
    const alerts = [makeAlert({ id: 1 }), makeAlert({ id: 2 }), makeAlert({ id: 3 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={3} />)
    const rows = screen.getAllByRole('row')
    expect(rows).toHaveLength(4)
  })

  it('shows risk and status badges with text', () => {
    render(<AlertsTable {...defaultProps} alerts={[makeAlert({ risk_level: 'high', status: 'escalated' })]} total={1} />)
    expect(screen.getByText('high')).toBeInTheDocument()
    expect(screen.getByText('escalated')).toBeInTheDocument()
  })

  it('renders assigned_to filter input', () => {
    render(<AlertsTable {...defaultProps} />)
    expect(screen.getByPlaceholderText('assigned to…')).toBeInTheDocument()
  })
})
