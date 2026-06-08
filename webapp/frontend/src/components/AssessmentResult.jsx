import { useCallback } from 'react'
import ScoreMeter from './ScoreMeter.jsx'
import SignalCard from './SignalCard.jsx'

const BAND_CONFIG = {
  High: {
    bg: 'bg-emerald-950/40',
    border: 'border-emerald-700/60',
    text: 'text-emerald-300',
    badge: 'bg-emerald-500',
    glow: 'shadow-emerald-900/40',
    dot: 'bg-emerald-400',
  },
  Medium: {
    bg: 'bg-amber-950/30',
    border: 'border-amber-700/60',
    text: 'text-amber-300',
    badge: 'bg-amber-500',
    glow: 'shadow-amber-900/40',
    dot: 'bg-amber-400',
  },
  Low: {
    bg: 'bg-orange-950/30',
    border: 'border-orange-700/60',
    text: 'text-orange-300',
    badge: 'bg-orange-500',
    glow: 'shadow-orange-900/40',
    dot: 'bg-orange-400',
  },
  Critical: {
    bg: 'bg-red-950/40',
    border: 'border-red-700/60',
    text: 'text-red-300',
    badge: 'bg-red-600',
    glow: 'shadow-red-900/40',
    dot: 'bg-red-400',
  },
}

const SEVERITY_COLORS = {
  info: 'text-slate-400 bg-slate-800/60 border-slate-700',
  low: 'text-emerald-400 bg-emerald-950/30 border-emerald-800/60',
  medium: 'text-amber-400 bg-amber-950/30 border-amber-800/60',
  high: 'text-orange-400 bg-orange-950/30 border-orange-800/60',
  critical: 'text-red-400 bg-red-950/30 border-red-800/60',
}

function SeverityBadge({ severity }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border uppercase tracking-wide ${SEVERITY_COLORS[severity] || SEVERITY_COLORS.info}`}>
      {severity}
    </span>
  )
}

function Section({ title, children, className = '' }) {
  return (
    <div className={`rounded-xl border border-slate-800 bg-slate-900/50 p-5 ${className}`}>
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">{title}</h3>
      {children}
    </div>
  )
}

export default function AssessmentResult({ result, onReset }) {
  const assessment = result?.assessment || {}
  const validation = result?.validation_result || {}
  const compliance = result?.compliance_result || {}
  const extracted = result?.extracted_invoice || {}

  const reliability = assessment?.reliability || {}
  const band = reliability?.band || 'Medium'
  const score = reliability?.score ?? 50
  const config = BAND_CONFIG[band] || BAND_CONFIG['Medium']

  const topReasons = assessment?.top_reasons || []
  const fieldsSummary = assessment?.fields_summary || {}
  const violations = compliance?.violations || []
  const authenticitySignals = validation?.authenticity_signals || []
  const humanReviewRequired = assessment?.human_review_required

  const handleDownload = useCallback(() => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice-assessment-${result?.assessment_id?.slice(0, 8) || 'result'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [result])

  // Determine vendor status severity
  const vendorSev = { matched: 'low', fuzzy: 'medium', not_found: 'high' }[validation?.vendor_status] || 'info'
  const dupSev = { none: 'low', near: 'high', exact: 'critical' }[validation?.duplicate_status] || 'info'
  const arithSev = validation?.arithmetic_consistent === false ? 'critical' : 'low'
  const compSev = compliance?.compliance_status === 'violations_found' ? 'high' : 'low'

  return (
    <div className="space-y-6">
      {/* Hero band + score */}
      <div className={`rounded-2xl border p-6 shadow-xl ${config.bg} ${config.border} ${config.glow}`}>
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
          {/* Band badge */}
          <div className="flex flex-col items-center text-center shrink-0">
            <div className={`w-24 h-24 rounded-2xl ${config.badge} flex flex-col items-center justify-center shadow-lg`}>
              <span className="text-white text-3xl font-black leading-none">{score}</span>
              <span className="text-white/70 text-xs font-medium mt-0.5">/ 100</span>
            </div>
            <span className={`mt-2 text-sm font-bold ${config.text}`}>{band} Reliability</span>
          </div>

          {/* Score meter + details */}
          <div className="flex-1 min-w-0">
            <ScoreMeter score={score} band={band} />

            <div className="mt-4 flex flex-wrap gap-2">
              {humanReviewRequired && (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-950/40 text-amber-400 border border-amber-800/50">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Human Review Required
                </span>
              )}
              {result?.assessment_id && (
                <span className="px-3 py-1 rounded-full text-xs font-mono text-slate-500 bg-slate-800/60 border border-slate-700/50">
                  ID: {result.assessment_id.slice(0, 12)}...
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex sm:flex-col gap-2 shrink-0">
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm text-slate-300 font-medium transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download JSON
            </button>
            <button
              onClick={onReset}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-700/50 text-sm text-indigo-300 font-medium transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Assessment
            </button>
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: extracted fields + explanation */}
        <div className="lg:col-span-2 space-y-5">
          {/* Extracted fields */}
          <Section title="Extracted Invoice Fields">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-slate-800">
                  {[
                    ['Vendor', extracted?.vendor_name || fieldsSummary?.vendor || '—'],
                    ['Invoice #', extracted?.invoice_number || fieldsSummary?.invoice_number || '—'],
                    ['Date', extracted?.invoice_date || fieldsSummary?.date || '—'],
                    ['Due Date', extracted?.due_date || '—'],
                    ['Amount', extracted?.total_amount != null
                      ? `${extracted?.currency || ''} ${Number(extracted.total_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                      : fieldsSummary?.amount || '—'],
                    ['Currency', extracted?.currency || '—'],
                    ['PO Number', extracted?.po_number || '—'],
                    ['Tax', extracted?.tax_amount != null ? `${extracted?.currency || ''} ${Number(extracted.tax_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : '—'],
                    ['Vendor Tax ID', extracted?.vendor_tax_id || '—'],
                  ].map(([key, val]) => (
                    <tr key={key}>
                      <td className="py-2 pr-4 text-slate-500 font-medium w-32 shrink-0">{key}</td>
                      <td className="py-2 text-slate-200 font-mono text-xs">{val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Line items */}
            {extracted?.line_items?.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-slate-500 mb-2">Line Items</p>
                <div className="rounded-lg overflow-hidden border border-slate-800">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-slate-800/60 text-slate-400">
                        <th className="text-left px-3 py-2 font-medium">Description</th>
                        <th className="text-right px-3 py-2 font-medium">Qty</th>
                        <th className="text-right px-3 py-2 font-medium">Unit Price</th>
                        <th className="text-right px-3 py-2 font-medium">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {extracted.line_items.map((li, i) => (
                        <tr key={i} className="text-slate-300">
                          <td className="px-3 py-2">{li.description}</td>
                          <td className="px-3 py-2 text-right">{li.quantity}</td>
                          <td className="px-3 py-2 text-right font-mono">{Number(li.unit_price).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                          <td className="px-3 py-2 text-right font-mono">{Number(li.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Section>

          {/* Claude explanation */}
          {assessment?.explanation && (
            <Section title="Claude's Analysis">
              <div className="flex gap-3">
                <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-700/40 flex items-center justify-center mt-0.5">
                  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">{assessment.explanation}</p>
              </div>
            </Section>
          )}

          {/* Top reasons */}
          {topReasons.length > 0 && (
            <Section title="Top Risk Signals">
              <div className="space-y-2">
                {topReasons.map((reason, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 border border-slate-700/40">
                    <SeverityBadge severity={reason.severity} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-slate-300 font-mono mb-0.5">{reason.signal_code}</p>
                      <p className="text-xs text-slate-400 leading-relaxed">{reason.contribution}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>

        {/* Right column: signal cards + violations */}
        <div className="space-y-5">
          {/* Signal cards */}
          <Section title="Checks">
            <div className="space-y-3">
              <SignalCard
                title="Vendor Status"
                status={validation?.vendor_status}
                severity={vendorSev}
                detail={
                  validation?.vendor_match_score != null
                    ? `Match score: ${(validation.vendor_match_score * 100).toFixed(0)}%`
                    : undefined
                }
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                }
              />

              <SignalCard
                title="Duplicate Detection"
                status={validation?.duplicate_status}
                severity={dupSev}
                detail={
                  validation?.duplicate_refs?.length > 0
                    ? `Refs: ${validation.duplicate_refs.join(', ')}`
                    : undefined
                }
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                }
              />

              <SignalCard
                title="Arithmetic Check"
                status={validation?.arithmetic_consistent ? 'compliant' : 'violations_found'}
                severity={arithSev}
                detail={
                  validation?.arithmetic_discrepancies?.length > 0
                    ? validation.arithmetic_discrepancies.join('; ')
                    : validation?.arithmetic_consistent === false
                    ? 'Line items do not match total'
                    : 'All totals verified'
                }
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                }
              />

              <SignalCard
                title="Compliance"
                status={compliance?.compliance_status}
                severity={compSev}
                detail={
                  compliance?.required_approval_tier
                    ? `Required tier: ${compliance.required_approval_tier}`
                    : compliance?.compliance_status === 'compliant'
                    ? 'No policy violations detected'
                    : undefined
                }
                icon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                }
              />
            </div>
          </Section>

          {/* Policy violations */}
          {violations.length > 0 && (
            <Section title={`Policy Violations (${violations.length})`}>
              <div className="space-y-2.5">
                {violations.map((v, i) => (
                  <div key={i} className="p-3 rounded-lg border border-red-800/40 bg-red-950/20">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="text-xs font-mono font-semibold text-red-300">{v.rule_id}</span>
                      <SeverityBadge severity={v.severity} />
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{v.description}</p>
                    {v.observed && (
                      <p className="text-xs text-slate-500 mt-1">
                        Observed: <span className="text-slate-400 font-mono">{v.observed}</span>
                        {v.threshold && <> / Limit: <span className="text-slate-400 font-mono">{v.threshold}</span></>}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Authenticity signals */}
          {authenticitySignals.length > 0 && (
            <Section title={`Authenticity Signals (${authenticitySignals.length})`}>
              <div className="space-y-2">
                {authenticitySignals.map((sig, i) => (
                  <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-800/30 border border-slate-700/30">
                    <SeverityBadge severity={sig.severity} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-mono text-slate-300 font-medium">{sig.code}</p>
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{sig.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* FX info if present */}
          {compliance?.normalization && compliance.normalization.fx_rate !== 1.0 && (
            <Section title="FX Normalization">
              <div className="text-xs space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Base currency</span>
                  <span className="font-mono text-slate-300">{compliance.normalization.base_currency}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>FX rate</span>
                  <span className="font-mono text-slate-300">{compliance.normalization.fx_rate}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Source</span>
                  <span className="font-mono text-slate-300">{compliance.normalization.fx_source}</span>
                </div>
              </div>
            </Section>
          )}
        </div>
      </div>

      {/* Advisory disclaimer */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4 flex items-start gap-3">
        <svg className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-xs text-slate-500 leading-relaxed">
          <span className="font-semibold text-slate-400">Advisory only.</span> This assessment is produced by an AI agent pipeline and is intended as a decision-support tool only.
          It does not constitute payment authorization, approval, or legal opinion. All material findings should be verified by a qualified human reviewer.
          Assessment ID: <span className="font-mono">{result?.assessment_id || 'N/A'}</span>
        </p>
      </div>
    </div>
  )
}
