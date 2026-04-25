import React from 'react'

interface GeographicMapProps {
  data: Array<{ state: string; value: number }>
}

const stateCoordinates: Record<string, { x: number; y: number }> = {
  'andhra pradesh': { x: 280, y: 320 },
  'arunachal pradesh': { x: 420, y: 120 },
  'assam': { x: 400, y: 160 },
  'bihar': { x: 320, y: 200 },
  'chhattisgarh': { x: 280, y: 240 },
  'delhi': { x: 240, y: 180 },
  'goa': { x: 200, y: 320 },
  'gujarat': { x: 140, y: 260 },
  'haryana': { x: 230, y: 170 },
  'himachal pradesh': { x: 230, y: 130 },
  'jammu & kashmir': { x: 200, y: 80 },
  'jharkhand': { x: 310, y: 230 },
  'karnataka': { x: 220, y: 340 },
  'kerala': { x: 220, y: 400 },
  'ladakh': { x: 190, y: 60 },
  'madhya pradesh': { x: 220, y: 250 },
  'maharashtra': { x: 180, y: 300 },
  'manipur': { x: 420, y: 180 },
  'meghalaya': { x: 390, y: 190 },
  'mizoram': { x: 420, y: 210 },
  'nagaland': { x: 410, y: 160 },
  'odisha': { x: 300, y: 280 },
  'punjab': { x: 210, y: 150 },
  'rajasthan': { x: 160, y: 210 },
  'sikkim': { x: 350, y: 180 },
  'tamil nadu': { x: 260, y: 400 },
  'telangana': { x: 260, y: 320 },
  'tripura': { x: 400, y: 220 },
  'uttar pradesh': { x: 260, y: 190 },
  'uttarakhand': { x: 240, y: 150 },
  'west bengal': { x: 340, y: 250 },
}

export const GeographicMap: React.FC<GeographicMapProps> = ({ data }) => {
  const maxValue = Math.max(...data.map(d => d.value), 1)
  
  const getStateKey = (state: string): string | undefined => {
    const normalized = state.toLowerCase().trim()
    return Object.keys(stateCoordinates).find(k => normalized.includes(k) || k.includes(normalized))
  }

  return (
    <div className="relative w-full h-80 bg-nrg-navy-50 rounded-xl border border-nrg-border overflow-hidden">
      <svg viewBox="100 0 400 500" className="w-full h-full">
        <rect x="100" y="0" width="400" height="500" fill="var(--nrg-surface-2)" />
        
        {data.map((d, i) => {
          const key = getStateKey(d.state)
          if (!key) return null
          const coords = stateCoordinates[key]
          const intensity = d.value / maxValue
          
          return (
            <g key={i}>
              <circle
                cx={coords.x}
                cy={coords.y}
                r={10 + intensity * 20}
                fill={`rgba(255, 107, 53, ${0.3 + intensity * 0.5})`}
                stroke="var(--nrg-chart-1)"
                strokeWidth="1"
              />
              <text
                x={coords.x}
                y={coords.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-[0.375rem] fill-white font-medium pointer-events-none"
              >
                {d.value}
              </text>
            </g>
          )
        })}
      </svg>
      
      <div className="absolute bottom-4 right-4 bg-white/90 rounded-lg p-3 shadow-sm">
        <p className="text-xs font-medium text-nrg-muted mb-2">Intensity Scale</p>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(255, 107, 53, 0.3)' }} />
          <span className="text-xs text-nrg-muted">Low</span>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(255, 107, 53, 0.6)' }} />
          <span className="text-xs text-nrg-muted">Med</span>
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(255, 107, 53, 0.8)' }} />
          <span className="text-xs text-nrg-muted">High</span>
        </div>
      </div>
    </div>
  )
}

export default GeographicMap