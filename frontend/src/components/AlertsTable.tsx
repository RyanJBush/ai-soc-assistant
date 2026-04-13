import { useState } from 'react'

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
  exportUrl: string
  onPageChange: (nextPage: number) => void
  onStatusFilterChange: (status: string) => void
  onAssignedToFilterChange: (assignedTo: string) => void
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void
  onSelectAlert: (alertId: number) => void
  onBulkUpdate: (alertIds: number[], status: AlertStatus) => Promise<void>
}

const STATUS_OPTIONS: Array<AlertStatus | 'all'> = ['all', 'new', 'acknowledged', 'escalated', 'resolved']
const BULK_STATUS_OPTIONS: AlertStatus[] = ['acknowledged', 'escalated', 'resolved', 'new']

export function AlertsTable({
  alerts,
  total,
  page,
  pageSize,
  statusFilter,
  assignedToFilter,
  sortBy,
  sortOrder,
  exportUrl,
  onPageChange,
  onStatusFilterChange,
  onAssignedToFilterChange,
  onSortChange,
  onSelectAlert,
  onBulkUpdate,
}: AlertsTableProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [bulkStatus, setBulkStatus] = useState<AlertStatus>('acknowledged')
  const [bulkLoading, setBulkLoading] = useState(false)

  const allOnPageSelected = alerts.length > 0 && alerts.every((a) => selected.has(a.id))

  function toggleAll() {
    if (allOnPageSelected) {
      setSelected((prev) => {
        const next = new Set(prev)
        alerts.forEach((a) => next.delete(a.id))
        return next
      })
    } else {
      setSelected((prev) => {
        const next = new Set(prev)
        alerts.forEach((a) => next.add(a.id))
        return next
      })
    }
  }

  function toggleOne(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function applyBulk() {
    if (selected.size === 0) return
    setBulkLoading(true)
    try {
      await onBulkUpdate(Array.from(selected), bulkStatus)
      setSelected(new Set())
    } finally {
      setBulkLoading(false)
    }
  }

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      {/* Toolbar */}
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

          <a
            href={exportUrl}
            download="alerts.csv"
            className="rounded border border-slate-600 bg-slate-800 px-2 py-1 text-cyan-300 hover:bg-slate-700"
            aria-label="Export alerts as CSV"
          >
            Export CSV
          </a>
        </div>
      </div>

      {/* Bulk action bar — shown when rows are selected */}
      {selected.size > 0 && (
        <div className="mb-3 flex flex-wrap items-center gap-2 rounded border border-cyan-700 bg-cyan-950/40 px-3 py-2 text-sm">
          <span className="text-cyan-300">{selected.size} selected</span>
          <select
            value={bulkStatus}
            onChange={(e) => setBulkStatus(e.target.value as AlertStatus)}
            className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs"
            aria-label="Bulk status"
          >
            {BULK_STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void applyBulk()}
            disabled={bulkLoading}
            className="rounded bg-cyan-700 px-3 py-1 text-xs font-medium text-white hover:bg-cyan-600 disabled:opacity-50"
          >
            {bulkLoading ? 'Applying…' : `Apply to ${selected.size}`}
          </button>
          <button
            type="button"
            onClick={() => setSelected(new Set())}
            className="rounded border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
          >
            Clear
          </button>
        </div>
      )}

      {alerts.length === 0 ? (
        <p className="text-sm text-slate-300">No alerts found for this filter.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="pb-2 pr-3">
                  <input
                    type="checkbox"
                    checked={allOnPageSelected}
                    onChange={toggleAll}
                    aria-label="Select all on page"
                    className="cursor-pointer accent-cyan-500"
                  />
                </th>
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
                  className={`border-t border-slate-800 hover:bg-slate-800/40 ${selected.has(alert.id) ? 'bg-slate-800/30' : ''}`}
                >
                  <td className="py-2 pr-3">
                    <input
                      type="checkbox"
                      checked={selected.has(alert.id)}
                      onChange={() => toggleOne(alert.id)}
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Select alert ${alert.id}`}
                      className="cursor-pointer accent-cyan-500"
                    />
                  </td>
                  <td
                    className="cursor-pointer py-2"
                    onClick={() => onSelectAlert(alert.id)}
                  >
                    {new Date(alert.created_at).toLocaleString()}
                  </td>
                  <td
                    className="cursor-pointer py-2 uppercase"
                    onClick={() => onSelectAlert(alert.id)}
                  >
                    {alert.prediction_label}
                  </td>
                  <td
                    className="cursor-pointer py-2"
                    onClick={() => onSelectAlert(alert.id)}
                  >
                    <StatusBadge status={alert.status} />
                  </td>
                  <td
                    className="cursor-pointer py-2"
                    onClick={() => onSelectAlert(alert.id)}
                  >
                    {alert.assigned_to ?? 'Unassigned'}
                  </td>
                  <td
                    className="cursor-pointer py-2"
                    onClick={() => onSelectAlert(alert.id)}
                  >
                    {(alert.confidence * 100).toFixed(2)}%
                  </td>
                  <td
                    className="cursor-pointer py-2"
                    onClick={() => onSelectAlert(alert.id)}
                  >
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

