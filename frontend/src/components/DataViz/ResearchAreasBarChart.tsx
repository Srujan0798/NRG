import React from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

interface ResearchAreasBarChartProps {
  data: { area: string; count: number; color?: string }[]
  title?: string
  titleHi?: string
  subtitle?: string
  height?: number
}

const SAFFRON_CURSOR_FILL = 'rgba(255, 107, 53, 0.08)'

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--nrg-surface)] px-3 py-2 rounded-lg shadow-lg border border-nrg-border">
        <p className="text-xs font-medium text-nrg-text">{label}</p>
        <p className="text-sm font-bold text-saffron-500">{payload[0].value.toLocaleString('en-IN')}</p>
      </div>
    )
  }
  return null
}

export const ResearchAreasBarChart: React.FC<ResearchAreasBarChartProps> = ({
  data,
  title = 'Research Area Distribution',
  titleHi = 'शोध क्षेत्र वितरण',
  subtitle = 'Top research areas across the network',
  height = 280,
}) => {
  const chartColors = ['var(--nrg-chart-1)', 'var(--nrg-chart-2)', 'var(--nrg-chart-3)', 'var(--nrg-chart-4)', 'var(--nrg-chart-5)', 'var(--nrg-chart-6)', 'var(--nrg-chart-7)']

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

      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--nrg-border)" strokeOpacity={0.5} vertical={false} />
          <XAxis
            dataKey="area"
            tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }}
            axisLine={false}
            tickLine={false}
            angle={-30}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: SAFFRON_CURSOR_FILL }} />
          <Bar
            dataKey="count"
            radius={[4, 4, 0, 0]}
            maxBarSize={40}
            animationDuration={1500}
            animationEasing="ease-out"
          >
            {data.map((entry, index) => (
              <motion.rect
                key={`bar-${index}`}
                fill={entry.color || chartColors[index % chartColors.length]}
                initial={{ scaleY: 0 }}
                animate={{ scaleY: 1 }}
                transition={{ delay: index * 0.08, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ transformOrigin: 'bottom' }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

export default ResearchAreasBarChart
