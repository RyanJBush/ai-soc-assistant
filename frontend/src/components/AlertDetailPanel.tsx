import { useState } from 'react'

import type { AlertDetailResponse, AlertStatus } from '../types/api'

interface AlertDetailPanelProps {
  detail: AlertDetailResponse | null
  role: string | null
  onUpdateStatus: (status: AlertStatus) => Promise<void>
  onAssign: (assignee: string) => Promise<void>
  onAddNote: (note: string) => Promise<void>
}

const STATUS_OPTIONS: AlertStatus[] = ['new', 'acknowledged', 'escalated', 'resolved']

export function AlertDetailPanel({ detail, role, onUpdateStatus, onAssign, onAddNote }: AlertDetailPanelProps) {
  const [newAssignee, setNewAssignee] = useState('')
  const [newNote, setNewNote] = useState('')

  if (!detail) {
    return (
      <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
        <h2 className="mb-2 text-lg font-semibold">Alert Detail</h2>
        <p className="text-sm text-slate-400">Select an alert row to view triage details.</p>
      </section>
    )
  }

  const canTriage = role === 'admin' || role === 'analyst'

  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900/70 p-4">
      <h2 className="mb-2 text-lg font-semibold">Alert #{detail.alert.id}</h2>
      <div className="grid gap-1 text-sm text-slate-300">
        <p>Status: {detail.alert.status}</p>
        <p>Assigned: {detail.alert.assigned_to ?? 'Unassigned'}</p>
        <p>Model: {detail.alert.model_version ?? 'unknown'}</p>
        <p>Malicious probability: {((detail.alert.malicious_probability ?? 0) * 100).toFixed(2)}%</p>
      </div>

      <div className="mt-3 rounded border border-slate-800 bg-slate-950 p-3 text-xs">
        <p className="font-medium text-slate-200">Top contributors</p>
        <ul className="mt-1 list-disc pl-4 text-slate-300">
          {detail.alert.top_contributors.map((item) => (
            <li key={`${item.feature}-${item.impact}`}>
              {item.feature}: {(item.impact * 100).toFixed(1)}%
            </li>
          ))}
        </ul>
      </div>

      {canTriage && (
        <div className="mt-4 space-y-3 border-t border-slate-800 pt-3">
          <div>
            <p className="mb-1 text-xs uppercase text-slate-400">Status transition</p>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((status) => (
                <button
                  key={status}
                  type="button"
                  className="rounded border border-slate-700 px-2 py-1 text-xs"
                  onClick={() => void onUpdateStatus(status)}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="mb-1 text-xs uppercase text-slate-400">Assignment</p>
            <div className="flex gap-2">
              <input
                value={newAssignee}
                onChange={(event) => setNewAssignee(event.target.value)}
                placeholder="analyst username"
                className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
              />
              <button
                type="button"
                className="rounded border border-slate-700 px-2 py-1 text-xs"
                onClick={() => {
                  if (newAssignee.trim()) {
                    void onAssign(newAssignee.trim())
                    setNewAssignee('')
                  }
                }}
              >
                Assign
              </button>
            </div>
          </div>

          <div>
            <p className="mb-1 text-xs uppercase text-slate-400">Add note</p>
            <textarea
              value={newNote}
              onChange={(event) => setNewNote(event.target.value)}
              rows={3}
              className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
              placeholder="Add analyst investigation context"
            />
            <button
              type="button"
              className="mt-2 rounded border border-slate-700 px-2 py-1 text-xs"
              onClick={() => {
                if (newNote.trim()) {
                  void onAddNote(newNote.trim())
                  setNewNote('')
                }
              }}
            >
              Save note
            </button>
          </div>
        </div>
      )}

      <div className="mt-4 border-t border-slate-800 pt-3">
        <p className="mb-1 text-xs uppercase text-slate-400">Analyst notes</p>
        {detail.notes.length === 0 ? (
          <p className="text-xs text-slate-400">No notes yet.</p>
        ) : (
          <ul className="space-y-2 text-xs">
            {detail.notes.map((note) => (
              <li key={note.id} className="rounded border border-slate-800 bg-slate-950 p-2">
                <p className="text-slate-200">{note.note}</p>
                <p className="mt-1 text-slate-500">
                  {note.author} • {new Date(note.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
