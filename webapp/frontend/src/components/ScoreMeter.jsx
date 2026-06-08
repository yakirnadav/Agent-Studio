import { useEffect, useRef, useState } from 'react'

const BAND_CONFIG = {
  High: { color: '#10b981', trackColor: '#064e3b', label: 'High Reliability' },
  Medium: { color: '#f59e0b', trackColor: '#451a03', label: 'Medium Reliability' },
  Low: { color: '#f97316', trackColor: '#431407', label: 'Low Reliability' },
  Critical: { color: '#ef4444', trackColor: '#450a0a', label: 'Critical Risk' },
}

export default function ScoreMeter({ score, band }) {
  const [animatedWidth, setAnimatedWidth] = useState(0)
  const rafRef = useRef(null)
  const startRef = useRef(null)
  const duration = 1200

  const config = BAND_CONFIG[band] || BAND_CONFIG['Medium']

  useEffect(() => {
    startRef.current = null
    const target = score

    const animate = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedWidth(Math.round(eased * target))
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [score])

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Reliability Score</span>
        <span className="text-2xl font-bold" style={{ color: config.color }}>
          {animatedWidth}<span className="text-sm font-normal text-slate-500">/100</span>
        </span>
      </div>

      {/* Track */}
      <div className="relative h-3 rounded-full overflow-hidden" style={{ backgroundColor: config.trackColor }}>
        {/* Gradient fill bar */}
        <div
          className="h-full rounded-full transition-none"
          style={{
            width: `${animatedWidth}%`,
            backgroundColor: config.color,
            boxShadow: `0 0 10px ${config.color}60`,
          }}
        />
      </div>

      {/* Scale labels */}
      <div className="flex justify-between mt-1.5 text-xs text-slate-600">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>
    </div>
  )
}
