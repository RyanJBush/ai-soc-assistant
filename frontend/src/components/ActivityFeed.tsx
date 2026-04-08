import type { AlertRecord, InferenceResponse } from '../types/api'

interface ActivityFeedProps {
  prediction: InferenceResponse | null
  alerts: AlertRecord[]
}

export function ActivityFeed({ prediction, alerts }: ActivityFeedProps) {
  const recent = alerts.slice(0, 5)

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold">Recent Activity</h2>
      {!prediction && recent.length === 0 ? (
        <p className="text-sm text-slate-300">No activity yet. Score an event to start analyst context.</p>
      ) : (
        <ul className="space-y-2 text-sm">
          {prediction && (
            <li className="rounded border border-cyan-900/60 bg-cyan-950/20 p-2">
              Latest scoring result: <span className="font-semibold">{prediction.prediction_label}</span> at{' '}
              {(prediction.confidence * 100).toFixed(1)}% confidence.
            </li>
          )}
          {recent.map((alert) => (
            <li key={alert.id} className="rounded border border-slate-700 bg-slate-950/60 p-2">
              Alert #{alert.id}: {alert.prediction_label} ({alert.risk_level})
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
