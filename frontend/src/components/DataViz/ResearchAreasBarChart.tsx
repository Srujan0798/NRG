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

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-navy-800 px-3 py-2 rounded-lg shadow-lg border border-slate-200 dark:border-navy-600">
        <p className="text-xs font-medium text-slate-900 dark:text-slate-100">{label}</p>
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
  const chartColors = ['#ff6b35', '#2563eb', '#10b981', '#c49538', '#6366f1', '#ec4899', '#8b5cf6']

  return (
    <motion.div
      className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200/80 dark:border-navy-700 p-5 shadow-md"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
        <p className="text-xs font-devanagari text-slate-500 dark:text-slate-400">{titleHi}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeOpacity={0.5} vertical={false} />
          <XAxis
            dataKey="area"
            tick={{ fontSize: 10, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            angle={-30}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,107,53,0.08)' }} />
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
