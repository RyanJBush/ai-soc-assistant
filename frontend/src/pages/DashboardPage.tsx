import { useEffect, useState } from 'react'

import { AlertsTable } from '../components/AlertsTable'
import { MetricsPanel } from '../components/MetricsPanel'
import { PredictionCard } from '../components/PredictionCard'
import { StatusBanner } from '../components/StatusBanner'
import { TrafficInputForm } from '../components/TrafficInputForm'
import { fetchModelInfo, fetchRecentAlerts, predict } from '../lib/api'
import type { AlertRecord, InferenceRequest, InferenceResponse, ModelInfoResponse } from '../types/api'

export function DashboardPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [prediction, setPrediction] = useState<InferenceResponse | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertRecord[]>([])

  useEffect(() => {
    void (async () => {
      try {
        const [model, recentAlerts] = await Promise.all([fetchModelInfo(), fetchRecentAlerts(10)])
        setModelInfo(model)
        setAlerts(recentAlerts.alerts)
      } catch (apiError) {
        setError((apiError as Error).message)
      }
    })()
  }, [])

  async function handlePredict(payload: InferenceRequest) {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await predict(payload)
      setPrediction(result)
      setSuccess(`Prediction completed: ${result.prediction_label.toUpperCase()}`)
      const recentAlerts = await fetchRecentAlerts(10)
      setAlerts(recentAlerts.alerts)
    } catch (apiError) {
      setError((apiError as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">SOC Intrusion Detection Dashboard</h1>
        <p className="mt-2 text-slate-300">
          Run AI-assisted network detection, review model metrics, and monitor recent alerts.
        </p>
      </header>

      <div className="mb-4 space-y-2">
        {error && <StatusBanner kind="error" message={error} />}
        {success && <StatusBanner kind="success" message={success} />}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <TrafficInputForm onSubmit={handlePredict} loading={loading} />
        <PredictionCard prediction={prediction} />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <MetricsPanel modelInfo={modelInfo} />
        <AlertsTable alerts={alerts} />
      </div>
    </main>
  )
}
