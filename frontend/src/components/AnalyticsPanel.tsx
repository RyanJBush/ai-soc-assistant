import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { AnalyticsResponse } from '../types/api'

interface AnalyticsPanelProps {
  analytics: AnalyticsResponse | null
  days: number
  onDaysChange: (days: number) => void
}

const RISK_COLORS: Record<string, string> = {
  low: '#22d3ee',
  medium: '#facc15',
  high: '#f97316',
  critical: '#ef4444',
}

const STATUS_COLORS: Record<string, string> = {
  new: '#64748b',
  acknowledged: '#818cf8',
  escalated: '#f97316',
  resolved: '#22c55e',
}

const DAYS_OPTIONS = [7, 14, 30, 60, 90]

export function AnalyticsPanel({ analytics, days, onDaysChange }: AnalyticsPanelProps) {
  if (!analytics) {
    return (
      <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm text-slate-400">
        Analytics loading…
      </section>
    )
  }

  const riskData = Object.entries(analytics.by_risk_level).map(([name, value]) => ({ name, value }))
  const statusData = Object.entries(analytics.by_status).map(([name, value]) => ({ name, value }))

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      {/* Header */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Analytics &amp; Reporting</h2>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-400">Window:</span>
          {DAYS_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => onDaysChange(d)}
              className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                days === d
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI summary cards */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard label="Total Alerts" value={analytics.total_alerts} />
        <KpiCard
          label="Malicious Rate"
          value={`${(analytics.malicious_rate * 100).toFixed(1)}%`}
          highlight={analytics.malicious_rate > 0.5}
        />
        <KpiCard label="Open Alerts" value={analytics.open_count} highlight={analytics.open_count > 0} />
        <KpiCard
          label="Avg Resolution"
          value={
            analytics.avg_resolution_hours != null
              ? `${analytics.avg_resolution_hours.toFixed(1)}h`
              : '—'
          }
        />
      </div>

      {/* Volume timeline */}
      <div className="mb-6">
        <h3 className="mb-2 text-sm font-medium text-slate-300">Alert Volume (last {days} days)</h3>
        {analytics.alert_volume_by_day.length === 0 ? (
          <p className="text-xs text-slate-500">No alerts in this window.</p>
        ) : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.alert_volume_by_day} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradMalicious" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#cbd5e1" tick={{ fontSize: 10 }} />
                <YAxis stroke="#cbd5e1" tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="count" name="Total" stroke="#6366f1" fill="url(#gradTotal)" strokeWidth={2} />
                <Area
                  type="monotone"
                  dataKey="malicious"
                  name="Malicious"
                  stroke="#ef4444"
                  fill="url(#gradMalicious)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Risk level + Status charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Risk breakdown */}
        <div>
          <h3 className="mb-2 text-sm font-medium text-slate-300">Risk Level Breakdown</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#cbd5e1" tick={{ fontSize: 11 }} />
                <YAxis stroke="#cbd5e1" tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', fontSize: 12 }}
                />
                <Bar dataKey="value" name="Alerts" radius={[3, 3, 0, 0]}>
                  {riskData.map((entry) => (
                    <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? '#64748b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status donut */}
        <div>
          <h3 className="mb-2 text-sm font-medium text-slate-300">Status Distribution</h3>
          <div className="h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius="40%"
                  outerRadius="70%"
                  paddingAngle={2}
                >
                  {statusData.map((entry) => (
                    <Cell key={entry.name} fill={STATUS_COLORS[entry.name] ?? '#64748b'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  )
}

interface KpiCardProps {
  label: string
  value: string | number
  highlight?: boolean
}

function KpiCard({ label, value, highlight }: KpiCardProps) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/60 p-3 text-center">
      <p className="mb-1 text-xs text-slate-400">{label}</p>
      <p className={`text-xl font-bold ${highlight ? 'text-orange-400' : 'text-cyan-300'}`}>{value}</p>
    </div>
  )
}
