import type { AlertRecord, InferenceResponse, RiskLevel } from '../types/api'

interface SummaryCardsProps {
  alerts: AlertRecord[]
  prediction: InferenceResponse | null
}

function countByRisk(alerts: AlertRecord[], risk: RiskLevel): number {
  return alerts.filter((alert) => alert.risk_level === risk).length
}

export function SummaryCards({ alerts, prediction }: SummaryCardsProps) {
  const highRisk = countByRisk(alerts, 'high')
  const mediumRisk = countByRisk(alerts, 'medium')
  const lowRisk = countByRisk(alerts, 'low')

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
        <p className="text-xs uppercase tracking-wider text-slate-400">Recent Alerts</p>
        <p className="mt-2 text-2xl font-semibold">{alerts.length}</p>
      </article>
      <article className="rounded-lg border border-red-800 bg-red-950/20 p-4">
        <p className="text-xs uppercase tracking-wider text-red-300">High Risk</p>
        <p className="mt-2 text-2xl font-semibold text-red-200">{highRisk}</p>
      </article>
      <article className="rounded-lg border border-amber-800 bg-amber-950/20 p-4">
        <p className="text-xs uppercase tracking-wider text-amber-300">Medium Risk</p>
        <p className="mt-2 text-2xl font-semibold text-amber-200">{mediumRisk}</p>
      </article>
      <article className="rounded-lg border border-emerald-800 bg-emerald-950/20 p-4">
        <p className="text-xs uppercase tracking-wider text-emerald-300">Latest Score</p>
        <p className="mt-2 text-2xl font-semibold text-emerald-200">
          {prediction ? `${(prediction.confidence * 100).toFixed(0)}%` : '—'}
        </p>
        <p className="mt-1 text-xs text-emerald-100/80">Low risk: {lowRisk}</p>
      </article>
    </section>
  )
}
