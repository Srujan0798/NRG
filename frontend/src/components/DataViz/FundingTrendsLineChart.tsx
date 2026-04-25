import React from 'react'
import { motion } from 'framer-motion'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart
} from 'recharts'

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

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--nrg-surface)] px-3 py-2 rounded-lg shadow-lg border border-nrg-border">
        <p className="text-xs font-semibold text-nrg-text">FY {label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} className="text-xs" style={{ color: p.color }}>
            {p.name}: ₹{(p.value / 10000000).toFixed(1)}Cr
          </p>
        ))}
      </div>
    )
  }
  return null
}

export const FundingTrendsLineChart: React.FC<FundingTrendsLineChartProps> = ({
  data,
  title = 'Funding Trends',
  titleHi = 'वित्तीय रुझान',
  subtitle = 'Research funding over time (in Crores)',
  height = 280,
  showArea = true,
}) => {
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
        {showArea ? (
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -10 }}>
            <defs>
              <linearGradient id="fundingGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--nrg-chart-1)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="var(--nrg-chart-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--nrg-border)" strokeOpacity={0.5} vertical={false} />
            <XAxis
              dataKey="year"
              tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `₹${(v / 10000000).toFixed(0)}Cr`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="funding"
              stroke="var(--nrg-chart-1)"
              strokeWidth={2}
              fill="url(#fundingGradient)"
              dot={{ r: 3, fill: 'var(--nrg-chart-1)', strokeWidth: 0 }}
              activeDot={{ r: 5, fill: 'var(--nrg-chart-1)', strokeWidth: 2, stroke: 'var(--nrg-white)' }}
              animationDuration={1500}
            />
          </AreaChart>
        ) : (
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--nrg-border)" strokeOpacity={0.5} vertical={false} />
            <XAxis dataKey="year" tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: 'var(--nrg-ink-muted)' }} axisLine={false} tickLine={false} tickFormatter={(v) => `₹${(v / 10000000).toFixed(0)}Cr`} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="funding"
              stroke="var(--nrg-chart-1)"
              strokeWidth={2}
              dot={{ r: 3, fill: 'var(--nrg-chart-1)', strokeWidth: 0 }}
              activeDot={{ r: 5 }}
              animationDuration={1500}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </motion.div>
  )
}

export default FundingTrendsLineChart
