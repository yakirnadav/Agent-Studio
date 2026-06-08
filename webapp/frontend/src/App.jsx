import { useState, useCallback } from 'react'
import UploadZone from './components/UploadZone.jsx'
import SamplePicker from './components/SamplePicker.jsx'
import AssessmentResult from './components/AssessmentResult.jsx'

const SAMPLES = ['clean', 'duplicate', 'unknown_vendor', 'over_threshold', 'bad_arithmetic', 'foreign_currency']

export default function App() {
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [result, setResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [activeSample, setActiveSample] = useState(null)

  const handleResult = useCallback((data) => {
    setResult(data)
    setStatus('success')
  }, [])

  const handleError = useCallback((msg) => {
    setErrorMsg(msg)
    setStatus('error')
  }, [])

  const handleLoading = useCallback(() => {
    setStatus('loading')
    setResult(null)
    setErrorMsg('')
  }, [])

  const handleUpload = useCallback(async (file) => {
    handleLoading()
    setActiveSample(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch('/api/assess', { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      handleResult(data)
    } catch (e) {
      handleError(e.message || 'Upload failed. Please try again.')
    }
  }, [handleLoading, handleResult, handleError])

  const handleSample = useCallback(async (name) => {
    handleLoading()
    setActiveSample(name)
    try {
      const res = await fetch(`/api/assess/sample/${name}`, { method: 'POST' })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      handleResult(data)
    } catch (e) {
      handleError(e.message || 'Sample assessment failed.')
    }
  }, [handleLoading, handleResult, handleError])

  const handleReset = useCallback(() => {
    setStatus('idle')
    setResult(null)
    setErrorMsg('')
    setActiveSample(null)
  }, [])

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white leading-tight">Invoice Reliability Assessment</h1>
              <p className="text-xs text-slate-400">AI-powered authenticity &amp; compliance analysis</p>
            </div>
          </div>
          {status !== 'idle' && (
            <button
              onClick={handleReset}
              className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              New Assessment
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Loading state */}
        {status === 'loading' && (
          <div className="flex flex-col items-center justify-center py-32 animate-fade-in">
            <div className="relative mb-6">
              <div className="w-16 h-16 rounded-full border-4 border-indigo-600/30 border-t-indigo-500 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-6 h-6 rounded-full bg-indigo-600/20" />
              </div>
            </div>
            <p className="text-lg font-medium text-white mb-2">Claude is analyzing your invoice...</p>
            <p className="text-sm text-slate-400 max-w-sm text-center">
              Running multi-agent pipeline: extraction, validation, compliance, and scoring
            </p>
            {activeSample && (
              <div className="mt-4 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300">
                Sample: <span className="text-indigo-400 font-medium">{activeSample}</span>
              </div>
            )}
          </div>
        )}

        {/* Error state */}
        {status === 'error' && (
          <div className="max-w-xl mx-auto mt-16 animate-fade-in">
            <div className="rounded-xl border border-red-800/60 bg-red-950/30 p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-red-900/50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-red-300 mb-2">Assessment Failed</h3>
              <p className="text-sm text-red-400/80 mb-5">{errorMsg}</p>
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg bg-red-800/40 hover:bg-red-800/60 text-red-300 text-sm font-medium transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Idle / upload state */}
        {status === 'idle' && (
          <div className="animate-fade-in">
            <div className="text-center mb-10">
              <h2 className="text-3xl font-bold text-white mb-3">Assess an Invoice</h2>
              <p className="text-slate-400 max-w-lg mx-auto">
                Upload an invoice file or select a sample to run AI-powered authenticity, arithmetic,
                vendor, and compliance checks.
              </p>
            </div>
            <UploadZone onUpload={handleUpload} />
            <div className="mt-8">
              <div className="flex items-center gap-4 mb-5">
                <div className="flex-1 h-px bg-slate-800" />
                <span className="text-xs text-slate-500 uppercase tracking-widest font-medium">or try a sample</span>
                <div className="flex-1 h-px bg-slate-800" />
              </div>
              <SamplePicker samples={SAMPLES} onSelect={handleSample} activeSample={activeSample} />
            </div>
          </div>
        )}

        {/* Result state */}
        {status === 'success' && result && (
          <div className="animate-slide-up">
            <AssessmentResult result={result} onReset={handleReset} />
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800 mt-16 py-6 text-center text-xs text-slate-600">
        Invoice Reliability Assessment Agent &mdash; Advisory Only &mdash; Not a payment authorization system
      </footer>
    </div>
  )
}
