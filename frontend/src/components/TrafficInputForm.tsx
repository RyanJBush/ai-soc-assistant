import { useState } from 'react'

import type { InferenceRequest } from '../types/api'

interface TrafficInputFormProps {
  onSubmit: (payload: InferenceRequest) => Promise<void>
  loading: boolean
}

const defaultPayload: InferenceRequest = {
  duration: 0,
  protocol_type: 'tcp',
  service: 'http',
  flag: 'SF',
  src_bytes: 181,
  dst_bytes: 5450,
  count: 8,
  srv_count: 8,
  serror_rate: 0,
  same_srv_rate: 1,
  dst_host_count: 20,
  dst_host_srv_count: 20,
}

export function TrafficInputForm({ onSubmit, loading }: TrafficInputFormProps) {
  const [form, setForm] = useState<InferenceRequest>(defaultPayload)

  function update<K extends keyof InferenceRequest>(key: K, value: InferenceRequest[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <form
      className="grid gap-3 rounded-lg border border-slate-700 bg-slate-900/70 p-4"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit(form)
      }}
    >
      <h2 className="text-lg font-semibold">Traffic Feature Input</h2>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <label className="text-sm">
          Protocol
          <select
            value={form.protocol_type}
            onChange={(event) => update('protocol_type', event.target.value as InferenceRequest['protocol_type'])}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          >
            <option value="tcp">tcp</option>
            <option value="udp">udp</option>
            <option value="icmp">icmp</option>
          </select>
        </label>
        <label className="text-sm">
          Service
          <input
            value={form.service}
            onChange={(event) => update('service', event.target.value)}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          />
        </label>
        <label className="text-sm">
          Flag
          <input
            value={form.flag}
            onChange={(event) => update('flag', event.target.value)}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          />
        </label>
        <label className="text-sm">
          Source Bytes
          <input
            type="number"
            min={0}
            value={form.src_bytes}
            onChange={(event) => update('src_bytes', Number(event.target.value))}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          />
        </label>
        <label className="text-sm">
          Destination Bytes
          <input
            type="number"
            min={0}
            value={form.dst_bytes}
            onChange={(event) => update('dst_bytes', Number(event.target.value))}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          />
        </label>
        <label className="text-sm">
          Error Rate
          <input
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={form.serror_rate}
            onChange={(event) => update('serror_rate', Number(event.target.value))}
            className="mt-1 w-full rounded bg-slate-800 p-2"
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={loading}
        className="mt-2 rounded bg-cyan-600 px-3 py-2 font-medium hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-slate-700"
      >
        {loading ? 'Running Detection...' : 'Run Detection'}
      </button>
    </form>
  )
}
