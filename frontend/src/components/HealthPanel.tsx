import type { HealthResponse, ModelInfoResponse } from '../types/api'

interface HealthPanelProps {
  health: HealthResponse | null
  modelInfo: ModelInfoResponse | null
}

export function HealthPanel({ health, modelInfo }: HealthPanelProps) {
  const serviceStatus = health?.status ?? 'unknown'
  const up = serviceStatus === 'ok'

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold">Service & Model Health</h2>
      <div className="grid gap-3 text-sm md:grid-cols-2">
        <div className="rounded border border-slate-700 bg-slate-950/60 p-3">
          <p className="text-slate-400">Backend status</p>
          <p className={`mt-1 font-semibold ${up ? 'text-emerald-300' : 'text-amber-300'}`}>{serviceStatus}</p>
        </div>
        <div className="rounded border border-slate-700 bg-slate-950/60 p-3">
          <p className="text-slate-400">Model version</p>
          <p className="mt-1 font-semibold text-cyan-300">{modelInfo?.model_version ?? 'not loaded'}</p>
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Health checks support analyst trust by showing API and model readiness before triage.
      </p>
    </section>
  )
}
