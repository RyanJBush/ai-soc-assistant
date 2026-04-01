interface StatusBannerProps {
  kind: 'error' | 'info' | 'success'
  message: string
}

const styles: Record<StatusBannerProps['kind'], string> = {
  error: 'bg-red-900/40 border-red-600 text-red-100',
  info: 'bg-slate-800 border-slate-600 text-slate-100',
  success: 'bg-emerald-900/30 border-emerald-600 text-emerald-100',
}

export function StatusBanner({ kind, message }: StatusBannerProps) {
  return <div className={`rounded-md border px-4 py-2 text-sm ${styles[kind]}`}>{message}</div>
}
