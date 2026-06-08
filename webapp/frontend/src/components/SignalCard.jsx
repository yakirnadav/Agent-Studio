const SEVERITY_STYLES = {
  info: { dot: 'bg-slate-400', text: 'text-slate-400', bg: 'bg-slate-800/40', border: 'border-slate-700/50' },
  low: { dot: 'bg-emerald-400', text: 'text-emerald-400', bg: 'bg-emerald-950/20', border: 'border-emerald-800/40' },
  medium: { dot: 'bg-amber-400', text: 'text-amber-400', bg: 'bg-amber-950/20', border: 'border-amber-800/40' },
  high: { dot: 'bg-orange-400', text: 'text-orange-400', bg: 'bg-orange-950/20', border: 'border-orange-800/40' },
  critical: { dot: 'bg-red-400', text: 'text-red-400', bg: 'bg-red-950/20', border: 'border-red-800/40' },
}

const STATUS_STYLES = {
  matched: { label: 'Matched', color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50' },
  fuzzy: { label: 'Fuzzy Match', color: 'text-amber-400 bg-amber-950/40 border-amber-800/50' },
  not_found: { label: 'Not Found', color: 'text-red-400 bg-red-950/40 border-red-800/50' },
  none: { label: 'No Duplicate', color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50' },
  exact: { label: 'Exact Duplicate', color: 'text-red-400 bg-red-950/40 border-red-800/50' },
  near: { label: 'Near Duplicate', color: 'text-amber-400 bg-amber-950/40 border-amber-800/50' },
  compliant: { label: 'Compliant', color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50' },
  violations_found: { label: 'Violations Found', color: 'text-red-400 bg-red-950/40 border-red-800/50' },
  indeterminate: { label: 'Indeterminate', color: 'text-slate-400 bg-slate-800/40 border-slate-700/50' },
}

function StatusBadge({ status }) {
  const s = STATUS_STYLES[status] || { label: status, color: 'text-slate-400 bg-slate-800/40 border-slate-700/50' }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${s.color}`}>
      {s.label}
    </span>
  )
}

export default function SignalCard({ title, icon, status, detail, severity }) {
  const sev = severity || 'info'
  const style = SEVERITY_STYLES[sev] || SEVERITY_STYLES.info

  return (
    <div className={`rounded-xl border p-4 ${style.bg} ${style.border}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-slate-400">{icon}</span>
          <span className="text-sm font-semibold text-slate-200">{title}</span>
        </div>
        {status && <StatusBadge status={status} />}
      </div>
      {detail && (
        <p className="text-xs text-slate-400 leading-relaxed">{detail}</p>
      )}
    </div>
  )
}
