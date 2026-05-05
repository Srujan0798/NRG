import React, { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

interface ResearchAreasBarChartProps {
  data: { area: string; count: number; color?: string }[]
  title?: string
  titleHi?: string
  subtitle?: string
  height?: number
}

interface BarChartItem {
  area: string
  count: number
  color: string
  x: number
  y: number
  width: number
  height: number
}

const SVG_WIDTH = 640
const Y_AXIS_TICKS = 4
const PADDING = {
  top: 12,
  right: 18,
  bottom: 72,
  left: 48,
}
const CHART_COLORS = ['var(--nrg-chart-1)', 'var(--nrg-chart-2)', 'var(--nrg-chart-3)', 'var(--nrg-chart-4)', 'var(--nrg-chart-5)', 'var(--nrg-chart-6)', 'var(--nrg-chart-7)']
const EMPTY_RESEARCH_AREA_MESSAGE = 'No research area data available'

const formatCount = (value: number) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value.toLocaleString('en-IN')
const trimLabel = (value: string) => value.length > 16 ? `${value.slice(0, 15)}...` : value

export const ResearchAreasBarChart: React.FC<ResearchAreasBarChartProps> = ({
  data,
  title = 'Research Area Distribution',
  titleHi = 'शोध क्षेत्र वितरण',
  subtitle = 'Top research areas across the network',
  height = 280,
}) => {
  const [activeBar, setActiveBar] = useState<BarChartItem | null>(null)
  const chartHeight = Math.max(height, 240)
  const chartBottom = chartHeight - PADDING.bottom
  const innerWidth = SVG_WIDTH - PADDING.left - PADDING.right
  const innerHeight = chartBottom - PADDING.top

  const { bars, yTicks } = useMemo(() => {
    const maxCount = Math.max(...data.map((item) => item.count), 1)
    const slotWidth = innerWidth / Math.max(data.length, 1)
    const barWidth = Math.min(42, Math.max(18, slotWidth * 0.58))
    const chartBars = data.map((item, index) => {
      const barHeight = (item.count / maxCount) * innerHeight
      const x = PADDING.left + index * slotWidth + (slotWidth - barWidth) / 2
      const y = chartBottom - barHeight
      return {
        ...item,
        color: item.color || CHART_COLORS[index % CHART_COLORS.length],
        x,
        y,
        width: barWidth,
        height: barHeight,
      }
    })
    const ticks = Array.from({ length: Y_AXIS_TICKS + 1 }, (_, index) => {
      const value = (maxCount / Y_AXIS_TICKS) * index
      const y = chartBottom - (value / maxCount) * innerHeight
      return { value, y }
    })
    return { bars: chartBars, yTicks: ticks }
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
        {bars.length === 0 ? (
          <div className="flex h-full items-center justify-center rounded border border-dashed border-nrg-border text-sm text-nrg-muted">
            {EMPTY_RESEARCH_AREA_MESSAGE}
          </div>
        ) : (
          <svg
            role="img"
            aria-label={`${title}: research area distribution chart`}
            className="h-full w-full overflow-visible"
            viewBox={`0 0 ${SVG_WIDTH} ${chartHeight}`}
            preserveAspectRatio="none"
          >
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
                  {formatCount(tick.value)}
                </text>
              </g>
            ))}
            {bars.map((bar, index) => (
              <g key={`${bar.area}-${index}`}>
                <motion.rect
                  x={bar.x}
                  y={bar.y}
                  width={bar.width}
                  height={bar.height}
                  rx={4}
                  fill={bar.color}
                  opacity={activeBar && activeBar.area !== bar.area ? 0.58 : 1}
                  initial={{ y: chartBottom, height: 0 }}
                  animate={{ y: bar.y, height: bar.height }}
                  transition={{ delay: index * 0.05, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                  tabIndex={0}
                  onMouseEnter={() => setActiveBar(bar)}
                  onMouseLeave={() => setActiveBar(null)}
                  onFocus={() => setActiveBar(bar)}
                  onBlur={() => setActiveBar(null)}
                />
                <text
                  x={bar.x + bar.width / 2}
                  y={chartHeight - 16}
                  textAnchor="end"
                  fontSize="10"
                  fill="var(--nrg-ink-muted)"
                  transform={`rotate(-30 ${bar.x + bar.width / 2} ${chartHeight - 16})`}
                >
                  {trimLabel(bar.area)}
                </text>
              </g>
            ))}
          </svg>
        )}
        {activeBar && (
          <div
            className="pointer-events-none absolute z-10 rounded-lg border border-nrg-border bg-[var(--nrg-surface)] px-3 py-2 shadow-lg"
            style={{
              left: `${((activeBar.x + activeBar.width / 2) / SVG_WIDTH) * 100}%`,
              top: `${(activeBar.y / chartHeight) * 100}%`,
              transform: 'translate(-50%, -115%)',
            }}
          >
            <p className="text-xs font-medium text-nrg-text">{activeBar.area}</p>
            <p className="text-sm font-bold text-saffron-500">{activeBar.count.toLocaleString('en-IN')}</p>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default ResearchAreasBarChart
