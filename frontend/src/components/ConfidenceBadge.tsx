import React, { useState } from 'react'
export type ConfidenceLevel = 'high' | 'partial' | 'low_clarify'

interface ConfidenceBadgeProps {
  level: ConfidenceLevel
  score?: number
  signals?: string[]
  className?: string
}

const CONFIG: Record<ConfidenceLevel, {
  label: string
  bg: string
  text: string
  border: string
  dot: string
  tooltipTitle: string
}> = {
  high: {
    label: 'Verified',
    bg: 'bg-emerald-50',
    text: 'text-emerald-800',
    border: 'border-emerald-200',
    dot: 'bg-emerald-500',
    tooltipTitle: 'Verified against returned evidence',
  },
  partial: {
    label: 'Partially verified',
    bg: 'bg-amber-50',
    text: 'text-amber-800',
    border: 'border-amber-200',
    dot: 'bg-amber-500',
    tooltipTitle: 'Some claims need review',
  },
  low_clarify: {
    label: 'Needs clarification',
    bg: 'bg-rose-50',
    text: 'text-rose-800',
    border: 'border-rose-200',
    dot: 'bg-rose-500',
    tooltipTitle: 'More detail is needed',
  },
}

const CONFIDENCE_COPY = {
  emptySignals: 'No additional verification signals.',
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  level,
  score,
  signals = [],
  className = '',
}) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const cfg = CONFIG[level]

  const tooltipLines: string[] = []
  if (score !== undefined) {
    tooltipLines.push(`Score: ${Math.round(score * 100)}%`)
  }
  if (signals.length > 0) {
    tooltipLines.push(`Signals: ${signals.join(', ')}`)
  }

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onFocus={() => setShowTooltip(true)}
      onBlur={() => setShowTooltip(false)}
      tabIndex={0}
      aria-label={`${cfg.label} confidence`}
    >
      <span
        className={`
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
          border ${cfg.bg} ${cfg.text} ${cfg.border}
          transition-colors duration-150
        `}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
        {cfg.label}
        {score !== undefined && (
          <span className="opacity-75">({Math.round(score * 100)}%)</span>
        )}
      </span>

      {showTooltip && (
        <div
          className="absolute z-50 bottom-full mb-2 left-1/2 -translate-x-1/2 w-64
                     bg-white rounded-lg shadow-lg border border-gray-200 p-3 text-xs"
          role="tooltip"
        >
          <div className="font-semibold text-gray-900 mb-1">{cfg.tooltipTitle}</div>
          {tooltipLines.length > 0 ? (
            <ul className="text-gray-600 space-y-0.5">
              {tooltipLines.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">{CONFIDENCE_COPY.emptySignals}</p>
          )}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 rotate-45 w-2 h-2 bg-white border-r border-b border-gray-200" />
        </div>
      )}
    </div>
  )
}

export default ConfidenceBadge
