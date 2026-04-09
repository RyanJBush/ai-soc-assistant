import type { AlertStatus, RiskLevel } from '../types/api'

const STATUS_STYLES: Record<AlertStatus, string> = {
  new: 'bg-slate-700 text-slate-200',
  acknowledged: 'bg-blue-900 text-blue-200',
  escalated: 'bg-amber-900 text-amber-200',
  resolved: 'bg-emerald-900 text-emerald-200',
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: 'bg-emerald-900 text-emerald-200',
  medium: 'bg-amber-900 text-amber-200',
  high: 'bg-red-900 text-red-200',
}

export function StatusBadge({ status }: { status: AlertStatus }) {
  const style = STATUS_STYLES[status] ?? 'bg-slate-700 text-slate-200'
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium uppercase ${style}`}>{status}</span>
  )
}

export function RiskBadge({ risk }: { risk: string }) {
  const style = RISK_STYLES[risk as RiskLevel] ?? 'bg-slate-700 text-slate-200'
  return (
    <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium uppercase ${style}`}>{risk}</span>
  )
}
