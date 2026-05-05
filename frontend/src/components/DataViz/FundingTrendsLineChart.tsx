import React, { useId, useMemo, useState } from 'react'
import { motion } from 'framer-motion'

interface FundingTrendData {
  year: number
  funding: number
  publications: number
}

interface FundingTrendsLineChartProps {
  data: FundingTrendData[]
  title?: string
  titleHi?: string
  subtitle?: string
  height?: number
  showArea?: boolean
}

interface FundingChartPoint extends FundingTrendData {
  x: number
  y: number
}

const SVG_WIDTH = 640
const Y_AXIS_TICKS = 4
const PADDING = {
  top: 12,
  right: 18,
  bottom: 38,
  left: 58,
}
const EMPTY_FUNDING_MESSAGE = 'No funding data available'
const FUNDING_TOOLTIP_LABEL = 'Funding'

const formatCrores = (value: number) => `₹${(value / 10000000).toFixed(value >= 100000000 ? 0 : 1)}Cr`

const buildLinePath = (points: FundingChartPoint[]) => (
  points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ')
)

export const FundingTrendsLineChart: React.FC<FundingTrendsLineChartProps> = ({
  data,
  title = 'Funding Trends',
  titleHi = 'वित्तीय रुझान',
  subtitle = 'Research funding over time (in Crores)',
  height = 280,
  showArea = true,
}) => {
  const gradientId = useId().replace(/:/g, '')
  const [activePoint, setActivePoint] = useState<FundingChartPoint | null>(null)
  const chartHeight = Math.max(height, 220)
  const chartBottom = chartHeight - PADDING.bottom
  const innerWidth = SVG_WIDTH - PADDING.left - PADDING.right
  const innerHeight = chartBottom - PADDING.top

  const { points, yTicks, areaPath, linePath } = useMemo(() => {
    const maxFunding = Math.max(...data.map((item) => item.funding), 1)
    const scaledPoints = data.map((item, index) => {
      const x = data.length <= 1
        ? PADDING.left + innerWidth / 2
        : PADDING.left + (index / (data.length - 1)) * innerWidth
      const y = chartBottom - (item.funding / maxFunding) * innerHeight
      return { ...item, x, y }
    })
    const ticks = Array.from({ length: Y_AXIS_TICKS + 1 }, (_, index) => {
      const value = (maxFunding / Y_AXIS_TICKS) * index
      const y = chartBottom - (value / maxFunding) * innerHeight
      return { value, y }
    })
    const path = buildLinePath(scaledPoints)
    const filledPath = scaledPoints.length
      ? `${path} L ${scaledPoints[scaledPoints.length - 1].x.toFixed(1)} ${chartBottom} L ${scaledPoints[0].x.toFixed(1)} ${chartBottom} Z`
      : ''
    return { points: scaledPoints, yTicks: ticks, areaPath: filledPath, linePath: path }
  }, [chartBottom, data, innerHeight, innerWidth])

  return (
    <motion.div
      className="nrg-panel p-5"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-nrg-text">{title}</h3>
        <p className="text-xs font-devanagari text-nrg-muted">{titleHi}</p>
        <p className="text-xs text-nrg-muted mt-0.5">{subtitle}</p>
      </div>

      <div className="relative" style={{ height: chartHeight }}>
        {points.length === 0 ? (
          <div className="flex h-full items-center justify-center rounded border border-dashed border-nrg-border text-sm text-nrg-muted">
            {EMPTY_FUNDING_MESSAGE}
          </div>
        ) : (
          <svg
            role="img"
            aria-label={`${title}: funding trend chart`}
            className="h-full w-full overflow-visible"
            viewBox={`0 0 ${SVG_WIDTH} ${chartHeight}`}
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id={`${gradientId}-funding`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--nrg-chart-1)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="var(--nrg-chart-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            {yTicks.map((tick) => (
              <g key={tick.value}>
                <line
                  x1={PADDING.left}
                  x2={SVG_WIDTH - PADDING.right}
                  y1={tick.y}
                  y2={tick.y}
                  stroke="var(--nrg-border)"
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                />
                <text x={PADDING.left - 10} y={tick.y + 4} textAnchor="end" fontSize="10" fill="var(--nrg-ink-muted)">
                  {formatCrores(tick.value)}
                </text>
              </g>
            ))}
            {points.map((point) => (
              <text key={point.year} x={point.x} y={chartHeight - 12} textAnchor="middle" fontSize="10" fill="var(--nrg-ink-muted)">
                {point.year}
              </text>
            ))}
            {showArea && <path d={areaPath} fill={`url(#${gradientId}-funding)`} />}
            <motion.path
              d={linePath}
              fill="none"
              stroke="var(--nrg-chart-1)"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
            />
            {points.map((point) => (
              <circle
                key={`point-${point.year}`}
                cx={point.x}
                cy={point.y}
                r={activePoint?.year === point.year ? 5 : 3.5}
                fill="var(--nrg-chart-1)"
                stroke="var(--nrg-white)"
                strokeWidth={activePoint?.year === point.year ? 2 : 0}
                tabIndex={0}
                onMouseEnter={() => setActivePoint(point)}
                onMouseLeave={() => setActivePoint(null)}
                onFocus={() => setActivePoint(point)}
                onBlur={() => setActivePoint(null)}
              />
            ))}
          </svg>
        )}
        {activePoint && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-nrg-border bg-[var(--nrg-surface)] px-3 py-2 shadow-lg"
            style={{
              left: `${(activePoint.x / SVG_WIDTH) * 100}%`,
              top: `${(activePoint.y / chartHeight) * 100}%`,
              transform: 'translate(-50%, -115%)',
            }}
          >
            <p className="text-xs font-semibold text-nrg-text">FY {activePoint.year}</p>
            <p className="text-xs text-[var(--nrg-chart-1)]">{FUNDING_TOOLTIP_LABEL}: {formatCrores(activePoint.funding)}</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default FundingTrendsLineChart
