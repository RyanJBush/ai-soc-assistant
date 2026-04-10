import type { InferenceResponse } from '../types/api'

interface PredictionCardProps {
  prediction: InferenceResponse | null
}

const RISK_STYLES: Record<string, string> = {
  low: 'text-emerald-400 border-emerald-700 bg-emerald-950/30',
  medium: 'text-yellow-400 border-yellow-700 bg-yellow-950/30',
  high: 'text-orange-400 border-orange-700 bg-orange-950/30',
  critical: 'text-red-400 border-red-700 bg-red-950/30',
}

export function PredictionCard({ prediction }: PredictionCardProps) {
  if (!prediction) {
    return <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm">No prediction yet.</div>
  }

  const verdictStyle =
    prediction.prediction_label === 'malicious'
      ? 'text-red-400 border-red-700 bg-red-950/30'
      : 'text-emerald-400 border-emerald-700 bg-emerald-950/30'

  const riskStyle = RISK_STYLES[prediction.risk_level] ?? RISK_STYLES.high

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold">Detection Result</h2>
      <div className={`rounded border px-3 py-2 font-semibold uppercase ${verdictStyle}`}>
        {prediction.prediction_label}
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-slate-400">Confidence</dt>
          <dd>{(prediction.confidence * 100).toFixed(2)}%</dd>
        </div>
        <div>
          <dt className="text-slate-400">Malicious Probability</dt>
          <dd>{(prediction.malicious_probability * 100).toFixed(2)}%</dd>
        </div>
        <div>
          <dt className="text-slate-400">Risk Level</dt>
          <dd className={`inline-block rounded px-1 font-semibold uppercase ${riskStyle}`}>{prediction.risk_level}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Model Version</dt>
          <dd>{prediction.model_version}</dd>
        </div>
      </dl>
      <h3 className="mt-4 text-sm font-medium">Top Contributors</h3>
      <ul className="mt-2 space-y-1 text-sm">
        {prediction.top_contributors.map((feature) => (
          <li key={feature.feature}>
            {feature.feature}: {(feature.impact * 100).toFixed(1)}%
          </li>
        ))}
      </ul>
      {prediction.explain_method && (
        <p className="mt-3 text-xs text-slate-400">
          Explain method: <span className="font-mono">{prediction.explain_method}</span>
        </p>
      )}
    </section>
  )
}
