const SAMPLE_META = {
  clean: {
    label: 'Clean Invoice',
    description: 'Compliant, known vendor',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50 hover:border-emerald-600',
  },
  duplicate: {
    label: 'Duplicate',
    description: 'Matches existing record',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    color: 'text-amber-400 bg-amber-950/40 border-amber-800/50 hover:border-amber-600',
  },
  unknown_vendor: {
    label: 'Unknown Vendor',
    description: 'Unregistered supplier',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'text-orange-400 bg-orange-950/40 border-orange-800/50 hover:border-orange-600',
  },
  over_threshold: {
    label: 'Over Threshold',
    description: 'Exceeds approval limit',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
    color: 'text-orange-400 bg-orange-950/40 border-orange-800/50 hover:border-orange-600',
  },
  bad_arithmetic: {
    label: 'Bad Arithmetic',
    description: 'Totals do not add up',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
    ),
    color: 'text-red-400 bg-red-950/40 border-red-800/50 hover:border-red-600',
  },
  foreign_currency: {
    label: 'Foreign Currency',
    description: 'EUR invoice, over threshold',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
      </svg>
    ),
    color: 'text-violet-400 bg-violet-950/40 border-violet-800/50 hover:border-violet-600',
  },
}

export default function SamplePicker({ samples, onSelect, activeSample }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {samples.map((name) => {
        const meta = SAMPLE_META[name] || {
          label: name,
          description: '',
          icon: null,
          color: 'text-slate-400 bg-slate-800/40 border-slate-700 hover:border-slate-500',
        }
        const isActive = activeSample === name
        return (
          <button
            key={name}
            onClick={() => onSelect(name)}
            className={`
              flex flex-col items-center gap-2 p-4 rounded-xl border text-center
              transition-all duration-200 cursor-pointer
              ${meta.color}
              ${isActive ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-950' : ''}
            `}
          >
            <span className="opacity-80">{meta.icon}</span>
            <div>
              <p className="text-xs font-semibold leading-tight">{meta.label}</p>
              <p className="text-xs opacity-60 mt-0.5 leading-tight">{meta.description}</p>
            </div>
          </button>
        )
      })}
    </div>
  )
}
