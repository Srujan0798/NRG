import React, { useMemo } from 'react'

interface StatisticalChartProps {
  data: Array<{ label: string; value: number }>
  type?: 'bar' | 'pie'
}

export const StatisticalChart: React.FC<StatisticalChartProps> = ({ data, type = 'bar' }) => {
  const maxVal = useMemo(() => Math.max(...data.map(d => d.value), 1), [data])
  
  const colors = ['#ff6b35', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dfe6e9', '#fd79a8', '#a29bfe']

  if (type === 'pie') {
    let currentAngle = 0
    const slices = data.map((d, i) => {
      const angle = (d.value / 100) * 360
      const slice = {
        ...d,
        color: colors[i % colors.length],
        startAngle: currentAngle,
        endAngle: currentAngle + angle,
      }
      currentAngle += angle
      return slice
    })

    return (
      <div className="flex items-center justify-center gap-6">
        <svg viewBox="0 0 100 100" className="w-32 h-32">
          {slices.map((slice, i) => {
            const startRad = (slice.startAngle - 90) * Math.PI / 180
            const endRad = (slice.endAngle - 90) * Math.PI / 180
            const x1 = 50 + 40 * Math.cos(startRad)
            const y1 = 50 + 40 * Math.sin(startRad)
            const x2 = 50 + 40 * Math.cos(endRad)
            const y2 = 50 + 40 * Math.sin(endRad)
            const largeArc = slice.endAngle - slice.startAngle > 180 ? 1 : 0
            
            if (slice.endAngle - slice.startAngle >= 359.9) {
              return <circle key={i} cx="50" cy="50" r="40" fill={slice.color} />
            }
            
            return (
              <path
                key={i}
                d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                fill={slice.color}
                stroke="white"
                strokeWidth="1"
              />
            )
          })}
        </svg>
        <div className="space-y-2">
          {slices.map((slice, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: slice.color }} />
              <span className="text-nrg-muted">{slice.label.substring(0, 20)}</span>
              <span className="font-medium text-nrg-text">{slice.value}%</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs font-medium text-nrg-muted w-10 text-right">{d.value}%</span>
          <div className="flex-1 bg-nrg-navy-50 rounded-full h-5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${(d.value / maxVal) * 100}%`,
                background: `linear-gradient(90deg, ${colors[i % colors.length]}, ${colors[(i + 1) % colors.length]})`,
                animationDelay: `${i * 100}ms`,
              }}
            />
          </div>
          <span className="text-xs text-nrg-text w-24 truncate">{d.label}</span>
        </div>
      ))}
    </div>
  )
}

export default StatisticalChart