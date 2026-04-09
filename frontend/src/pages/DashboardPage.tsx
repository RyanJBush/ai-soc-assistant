import { useEffect, useState } from 'react'

import { ActivityFeed } from '../components/ActivityFeed'
import { AlertDetailPanel } from '../components/AlertDetailPanel'
import { AlertsTable } from '../components/AlertsTable'
import { HealthPanel } from '../components/HealthPanel'
import { MetricsPanel } from '../components/MetricsPanel'
import { PredictionCard } from '../components/PredictionCard'
import { StatusBanner } from '../components/StatusBanner'
import { SummaryCards } from '../components/SummaryCards'
import { TrafficInputForm } from '../components/TrafficInputForm'
import {
  addAlertNote,
  assignAlert,
  fetchAlertDetail,
  fetchHealth,
  fetchMe,
  fetchModelInfo,
  fetchRecentAlerts,
  login,
  predict,
  setAuthToken,
  updateAlertStatus,
} from '../lib/api'
import type {
  AlertDetailResponse,
  AlertRecord,
  AlertStatus,
  HealthResponse,
  InferenceRequest,
  InferenceResponse,
  ModelInfoResponse,
  UserPrincipal,
} from '../types/api'

export function DashboardPage() {
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [prediction, setPrediction] = useState<InferenceResponse | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertRecord[]>([])
  const [alertDetail, setAlertDetail] = useState<AlertDetailResponse | null>(null)
  const [principal, setPrincipal] = useState<UserPrincipal | null>(null)

  const [username, setUsername] = useState('analyst')
  const [password, setPassword] = useState('analyst123!')

  const [page, setPage] = useState(1)
  const [pageSize] = useState(10)
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  async function loadDashboardData(currentPage = page) {
    setInitializing(true)
    try {
      const [healthData, model, recentAlerts] = await Promise.all([
        fetchHealth(),
        fetchModelInfo(),
        fetchRecentAlerts({
          page: currentPage,
          pageSize,
          status: statusFilter || undefined,
          sortBy,
          sortOrder,
        }),
      ])
      setHealth(healthData)
      setModelInfo(model)
      setAlerts(recentAlerts.alerts)
      setTotal(recentAlerts.total)
    } catch (apiError) {
      setError((apiError as Error).message)
    } finally {
      setInitializing(false)
    }
  }

  useEffect(() => {
    if (!principal) return
    void loadDashboardData(page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [principal, page, statusFilter, sortBy, sortOrder])

  async function handleLogin() {
    setError(null)
    try {
      const token = await login(username, password)
      setAuthToken(token.access_token)
      const me = await fetchMe()
      setPrincipal(me)
      setSuccess(`Authenticated as ${me.username} (${me.role})`)
    } catch (apiError) {
      setError((apiError as Error).message)
    }
  }

  async function handlePredict(payload: InferenceRequest) {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await predict(payload)
      setPrediction(result)
      setSuccess(`Prediction completed: ${result.prediction_label.toUpperCase()}`)
      await loadDashboardData(1)
      setPage(1)
    } catch (apiError) {
      setError((apiError as Error).message)
    } finally {
      setLoading(false)
    }
  }

  async function openAlert(alertId: number) {
    try {
      const detail = await fetchAlertDetail(alertId)
      setAlertDetail(detail)
    } catch (apiError) {
      setError((apiError as Error).message)
    }
  }

  async function refreshAlertDetail(alertId: number) {
    const detail = await fetchAlertDetail(alertId)
    setAlertDetail(detail)
    await loadDashboardData(page)
  }

  async function handleStatusUpdate(status: AlertStatus) {
    if (!alertDetail) return
    try {
      await updateAlertStatus(alertDetail.alert.id, status)
      await refreshAlertDetail(alertDetail.alert.id)
      setSuccess(`Alert ${alertDetail.alert.id} status updated to ${status}`)
    } catch (apiError) {
      setError((apiError as Error).message)
    }
  }

  async function handleAssign(assignee: string) {
    if (!alertDetail) return
    try {
      await assignAlert(alertDetail.alert.id, assignee)
      await refreshAlertDetail(alertDetail.alert.id)
      setSuccess(`Alert ${alertDetail.alert.id} assigned to ${assignee}`)
    } catch (apiError) {
      setError((apiError as Error).message)
    }
  }

  async function handleAddNote(note: string) {
    if (!alertDetail) return
    try {
      await addAlertNote(alertDetail.alert.id, note)
      await refreshAlertDetail(alertDetail.alert.id)
      setSuccess(`Added note to alert ${alertDetail.alert.id}`)
    } catch (apiError) {
      setError((apiError as Error).message)
    }
  }

  if (!principal) {
    return (
      <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
        <header className="mx-auto max-w-md rounded-lg border border-slate-800 bg-slate-900 p-6">
          <h1 className="text-2xl font-bold">SOC Dashboard Login</h1>
          <p className="mt-2 text-sm text-slate-400">Use demo users from README (`admin`, `analyst`, `viewer`).</p>
          <div className="mt-4 space-y-2">
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="username"
            />
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="password"
            />
            <button
              type="button"
              onClick={() => void handleLogin()}
              className="w-full rounded bg-emerald-600 px-3 py-2 font-medium text-white hover:bg-emerald-500"
            >
              Sign in
            </button>
          </div>
          <div className="mt-3">{error && <StatusBanner kind="error" message={error} />}</div>
        </header>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
      <header className="mb-6">
        <h1 className="text-3xl font-bold">SOC Intrusion Detection Dashboard</h1>
        <p className="mt-2 text-slate-300">Logged in as {principal.username} ({principal.role})</p>
      </header>

      <div className="mb-4 space-y-2">
        {initializing && <StatusBanner kind="info" message="Loading SOC context..." />}
        {error && <StatusBanner kind="error" message={error} />}
        {success && <StatusBanner kind="success" message={success} />}
      </div>

      <SummaryCards alerts={alerts} prediction={prediction} />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <TrafficInputForm onSubmit={handlePredict} loading={loading} />
        <PredictionCard prediction={prediction} />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <AlertsTable
            alerts={alerts}
            total={total}
            page={page}
            pageSize={pageSize}
            statusFilter={statusFilter}
            sortBy={sortBy}
            sortOrder={sortOrder}
            onPageChange={setPage}
            onStatusFilterChange={setStatusFilter}
            onSortChange={(nextSortBy, nextSortOrder) => {
              setSortBy(nextSortBy)
              setSortOrder(nextSortOrder)
            }}
            onSelectAlert={(id) => void openAlert(id)}
          />
        </div>
        <AlertDetailPanel
          detail={alertDetail}
          role={principal.role}
          onUpdateStatus={handleStatusUpdate}
          onAssign={handleAssign}
          onAddNote={handleAddNote}
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <MetricsPanel modelInfo={modelInfo} />
        <HealthPanel health={health} modelInfo={modelInfo} />
      </div>

      <div className="mt-4">
        <ActivityFeed prediction={prediction} alerts={alerts} />
      </div>
    </main>
  )
}
