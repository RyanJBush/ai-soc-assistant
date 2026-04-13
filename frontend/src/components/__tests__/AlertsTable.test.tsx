import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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
  exportUrl: 'http://localhost:8000/alerts/export',
  onPageChange: vi.fn(),
  onStatusFilterChange: vi.fn(),
  onAssignedToFilterChange: vi.fn(),
  onSortChange: vi.fn(),
  onSelectAlert: vi.fn(),
  onBulkUpdate: vi.fn().mockResolvedValue(undefined),
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
    // header row + 3 data rows = 4
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

  // ------------------------------------------------------------------
  // Export CSV
  // ------------------------------------------------------------------

  it('renders Export CSV link', () => {
    render(<AlertsTable {...defaultProps} />)
    expect(screen.getByRole('link', { name: /Export alerts as CSV/i })).toBeInTheDocument()
  })

  it('Export CSV link has correct href', () => {
    render(<AlertsTable {...defaultProps} exportUrl="http://localhost:8000/alerts/export?status=new" />)
    const link = screen.getByRole('link', { name: /Export alerts as CSV/i })
    expect(link).toHaveAttribute('href', 'http://localhost:8000/alerts/export?status=new')
  })

  // ------------------------------------------------------------------
  // Checkboxes and selection
  // ------------------------------------------------------------------

  it('renders a checkbox for each alert row', () => {
    const alerts = [makeAlert({ id: 1 }), makeAlert({ id: 2 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={2} />)
    // 1 select-all + 2 row checkboxes
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(3)
  })

  it('select-all checkbox selects all rows', async () => {
    const alerts = [makeAlert({ id: 1 }), makeAlert({ id: 2 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={2} />)
    const selectAll = screen.getByLabelText('Select all on page')
    await userEvent.click(selectAll)
    // Bulk action bar should appear
    expect(screen.getByText(/2 selected/i)).toBeInTheDocument()
  })

  it('selecting individual rows shows bulk bar', async () => {
    const alerts = [makeAlert({ id: 1 }), makeAlert({ id: 2 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={2} />)
    const rowCheckbox = screen.getByLabelText('Select alert 1')
    await userEvent.click(rowCheckbox)
    expect(screen.getByText(/1 selected/i)).toBeInTheDocument()
  })

  it('Clear button hides the bulk bar', async () => {
    const alerts = [makeAlert({ id: 1 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={1} />)
    await userEvent.click(screen.getByLabelText('Select alert 1'))
    expect(screen.getByText(/1 selected/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Clear' }))
    expect(screen.queryByText(/selected/i)).not.toBeInTheDocument()
  })

  it('Apply bulk button calls onBulkUpdate with selected ids', async () => {
    const onBulkUpdate = vi.fn().mockResolvedValue(undefined)
    const alerts = [makeAlert({ id: 3 }), makeAlert({ id: 7 })]
    render(<AlertsTable {...defaultProps} alerts={alerts} total={2} onBulkUpdate={onBulkUpdate} />)
    await userEvent.click(screen.getByLabelText('Select all on page'))
    await userEvent.click(screen.getByRole('button', { name: /Apply to 2/i }))
    expect(onBulkUpdate).toHaveBeenCalledWith(expect.arrayContaining([3, 7]), expect.any(String))
  })
})
