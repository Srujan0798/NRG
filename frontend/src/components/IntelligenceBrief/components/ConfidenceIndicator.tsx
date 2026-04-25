import React from 'react'

interface ConfidenceIndicatorProps {
  score: number
  status?: boolean
  provenance?: {
    verifier?: string
  }
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  score,
  status,
  provenance,
}) => {
  const level = score >= 0.8 ? 'high' : score >= 0.5 ? 'medium' : 'low'
  
  const colors = {
    high: {
      bar: 'bg-green-500',
      bg: 'bg-green-50 border-green-200',
      text: 'text-green-700',
    },
    medium: {
      bar: 'bg-amber-400',
      bg: 'bg-amber-50 border-amber-200',
      text: 'text-amber-700',
    },
    low: {
      bar: 'bg-red-400',
      bg: 'bg-red-50 border-red-200',
      text: 'text-red-700',
    },
  }

  const factors: string[] = []
  if (score >= 0.8) factors.push('Strong evidence base')
  if (provenance?.verifier?.includes('faithful')) factors.push('Verifier passed')
  if (status) factors.push('Source quality verified')

  const limitations: string[] = []
  if (score < 0.8) limitations.push('Evidence strength could be improved')
  if (!provenance?.verifier) limitations.push('No verifier score available')
  if (!status) limitations.push('Some sources unverified')

  return (
    <div className={`p-4 rounded-xl border ${colors[level].bg}`}>
      <div className="flex items-center gap-4">
        <div className="flex flex-col items-center">
          <div className="relative w-16 h-16">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="var(--nrg-border)"
                strokeWidth="3"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={level === 'high' ? 'var(--nrg-chart-3)' : level === 'medium' ? 'var(--nrg-warning)' : 'var(--nrg-danger)'}
                strokeWidth="3"
                strokeDasharray={`${score * 100}, 100`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-lg font-bold ${colors[level].text}`}>
                {Math.round(score * 100)}
              </span>
            </div>
          </div>
          <span className={`text-xs font-medium mt-1 ${colors[level].text}`}>
            {level.charAt(0).toUpperCase() + level.slice(1)}
          </span>
        </div>

        <div className="flex-1 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-medium text-nrg-muted mb-1.5">Factors</p>
            <ul className="space-y-1">
              {factors.map((f, i) => (
                <li key={i} className="flex items-center gap-1.5 text-xs text-green-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="text-xs font-medium text-nrg-muted mb-1.5">Limitations</p>
            <ul className="space-y-1">
              {limitations.map((l, i) => (
                <li key={i} className="flex items-center gap-1.5 text-xs text-amber-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  {l}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfidenceIndicator