import type { AlertRecord } from '../types/api'

interface AlertsTableProps {
  alerts: AlertRecord[]
}

export function AlertsTable({ alerts }: AlertsTableProps) {
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-3 text-lg font-semibold">Recent Alerts</h2>
      {alerts.length === 0 ? (
        <p className="text-sm text-slate-300">No alerts yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="pb-2">Time</th>
                <th className="pb-2">Label</th>
                <th className="pb-2">Confidence</th>
                <th className="pb-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id} className="border-t border-slate-800">
                  <td className="py-2">{new Date(alert.created_at).toLocaleString()}</td>
                  <td className="py-2 uppercase">{alert.prediction_label}</td>
                  <td className="py-2">{(alert.confidence * 100).toFixed(2)}%</td>
                  <td className="py-2 uppercase">{alert.risk_level}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
