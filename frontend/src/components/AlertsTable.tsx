import type { AlertRecord, AlertStatus } from '../types/api'
import { RiskBadge, StatusBadge } from './AlertBadges'

interface AlertsTableProps {
  alerts: AlertRecord[]
  total: number
  page: number
  pageSize: number
  statusFilter: string
  assignedToFilter: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
  onPageChange: (nextPage: number) => void
  onStatusFilterChange: (status: string) => void
  onAssignedToFilterChange: (assignedTo: string) => void
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void
  onSelectAlert: (alertId: number) => void
}

const STATUS_OPTIONS: Array<AlertStatus | 'all'> = ['all', 'new', 'acknowledged', 'escalated', 'resolved']

export function AlertsTable({
  alerts,
  total,
  page,
  pageSize,
  statusFilter,
  assignedToFilter,
  sortBy,
  sortOrder,
  onPageChange,
  onStatusFilterChange,
  onAssignedToFilterChange,
  onSortChange,
  onSelectAlert,
}: AlertsTableProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Recent Alerts</h2>
        <div className="flex flex-wrap gap-2 text-xs">
          <select
            value={statusFilter}
            onChange={(event) => {
              onStatusFilterChange(event.target.value)
              onPageChange(1)
            }}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1"
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status === 'all' ? '' : status}>
                status: {status}
              </option>
            ))}
          </select>

          <input
            value={assignedToFilter}
            onChange={(event) => {
              onAssignedToFilterChange(event.target.value)
              onPageChange(1)
            }}
            placeholder="assigned to…"
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs"
          />

          <select
            value={sortBy}
            onChange={(event) => onSortChange(event.target.value, sortOrder)}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1"
          >
            <option value="created_at">sort: created_at</option>
            <option value="updated_at">sort: updated_at</option>
            <option value="confidence">sort: confidence</option>
            <option value="risk_level">sort: risk_level</option>
            <option value="status">sort: status</option>
          </select>

          <button
            type="button"
            onClick={() => onSortChange(sortBy, sortOrder === 'asc' ? 'desc' : 'asc')}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1"
          >
            order: {sortOrder}
          </button>
        </div>
      </div>

      {alerts.length === 0 ? (
        <p className="text-sm text-slate-300">No alerts found for this filter.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="pb-2">Time</th>
                <th className="pb-2">Label</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Owner</th>
                <th className="pb-2">Confidence</th>
                <th className="pb-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr
                  key={alert.id}
                  className="cursor-pointer border-t border-slate-800 hover:bg-slate-800/40"
                  onClick={() => onSelectAlert(alert.id)}
                >
                  <td className="py-2">{new Date(alert.created_at).toLocaleString()}</td>
                  <td className="py-2 uppercase">{alert.prediction_label}</td>
                  <td className="py-2">
                    <StatusBadge status={alert.status} />
                  </td>
                  <td className="py-2">{alert.assigned_to ?? 'Unassigned'}</td>
                  <td className="py-2">{(alert.confidence * 100).toFixed(2)}%</td>
                  <td className="py-2">
                    <RiskBadge risk={alert.risk_level} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-xs text-slate-300">
        <span>
          page {page} / {totalPages} • total alerts: {total}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="rounded border border-slate-700 px-2 py-1 disabled:opacity-40"
          >
            Prev
          </button>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="rounded border border-slate-700 px-2 py-1 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  )
}
