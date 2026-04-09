import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { ModelInfoResponse } from '../types/api'

interface MetricsPanelProps {
  modelInfo: ModelInfoResponse | null
}

export function MetricsPanel({ modelInfo }: MetricsPanelProps) {
  if (!modelInfo) {
    return <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-4 text-sm">No model metrics loaded.</div>
  }

  const bars = [
    { name: 'Precision', value: modelInfo.metrics.precision ?? 0 },
    { name: 'Recall', value: modelInfo.metrics.recall ?? 0 },
    { name: 'F1', value: modelInfo.metrics.f1_score ?? 0 },
    { name: 'ROC-AUC', value: modelInfo.metrics.roc_auc ?? 0 },
    { name: 'FPR', value: modelInfo.metrics.false_positive_rate ?? 0 },
  ]

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold">Model Performance & Lineage</h2>
      <p className="mb-2 text-sm text-slate-300">
        {modelInfo.model_name} ({modelInfo.model_version}) | train rows: {modelInfo.training_rows} | test rows: {modelInfo.test_rows}
      </p>
      <p className="mb-2 break-all text-xs text-slate-400">
        Artifact SHA256: {modelInfo.lineage.artifact_sha256}
      </p>
      <p className="mb-3 break-all text-xs text-slate-400">
        Metrics SHA256: {modelInfo.lineage.metrics_sha256}
      </p>

      <div className="mb-3 grid gap-2 text-xs text-slate-300 md:grid-cols-2">
        <p>Decision threshold: {modelInfo.thresholds.malicious_decision_threshold.toFixed(2)}</p>
        <p>Medium threshold: {modelInfo.thresholds.risk_threshold_medium.toFixed(2)}</p>
        <p>High threshold: {modelInfo.thresholds.risk_threshold_high.toFixed(2)}</p>
        <p>Critical threshold: {modelInfo.thresholds.risk_threshold_critical.toFixed(2)}</p>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={bars}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#cbd5e1" />
            <YAxis domain={[0, 1]} stroke="#cbd5e1" />
            <Tooltip />
            <Bar dataKey="value" fill="#22d3ee" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 text-xs text-slate-400">
        Monitoring hook: {modelInfo.monitoring.monitoring_endpoint}
        <br />
        Events: {modelInfo.monitoring.supported_event_types.join(', ')}
      </div>
    </section>
  )
}
