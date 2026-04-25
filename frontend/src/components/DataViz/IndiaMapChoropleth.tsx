import React from 'react'
import { motion } from 'framer-motion'

interface StateData {
  state: string
  stateHi: string
  count: number
  growth?: number
}

interface IndiaMapChoroplethProps {
  data: StateData[]
  title?: string
  titleHi?: string
  subtitle?: string
  height?: number
}

const stateCoordinates: Record<string, { x: number; y: number }> = {
  'Maharashtra': { x: 45, y: 55 },
  'Delhi': { x: 58, y: 35 },
  'Karnataka': { x: 48, y: 65 },
  'Tamil Nadu': { x: 55, y: 72 },
  'Telangana': { x: 52, y: 58 },
  'West Bengal': { x: 68, y: 48 },
  'Gujarat': { x: 38, y: 48 },
  'Rajasthan': { x: 35, y: 35 },
  'Uttar Pradesh': { x: 55, y: 32 },
  'Madhya Pradesh': { x: 48, y: 42 },
  'Kerala': { x: 52, y: 78 },
  'Punjab': { x: 52, y: 25 },
  'Haryana': { x: 54, y: 28 },
  'Andhra Pradesh': { x: 52, y: 65 },
  ' Bihar': { x: 62, y: 40 },
  'Odisha': { x: 65, y: 52 },
  'Assam': { x: 75, y: 45 },
}

const IndiaMapPlaceholder: React.FC<{ maxCount: number; data: StateData[] }> = ({ maxCount, data }) => {
  const getColor = (count: number): string => {
    if (count === 0) return 'var(--nrg-border)'
    const intensity = Math.log(count + 1) / Math.log(maxCount + 1)
    if (intensity > 0.8) return 'var(--nrg-chart-1)'
    if (intensity > 0.6) return 'var(--nrg-saffron-soft)'
    if (intensity > 0.4) return 'var(--nrg-saffron-muted)'
    if (intensity > 0.2) return 'var(--nrg-saffron-subtle)'
    return 'var(--nrg-saffron-wash)'
  }

  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      <path
        d="M25 35 L35 30 L45 32 L55 30 L65 35 L70 40 L68 50 L70 55 L65 60 L75 65 L70 70 L60 68 L55 72 L50 75 L45 72 L40 75 L35 70 L30 65 L25 55 L28 45 Z"
        fill="var(--nrg-surface-3)"
        stroke="var(--nrg-border)"
        strokeWidth="0.5"
      />
      {data.map((state) => {
        const coords = stateCoordinates[state.state]
        if (!coords) return null
        return (
          <motion.g
            key={state.state}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.4 }}
          >
            <circle
              cx={coords.x}
              cy={coords.y}
              r={Math.max(2, Math.min(6, Math.sqrt(state.count) * 0.8))}
              fill={getColor(state.count)}
              stroke="var(--nrg-white)"
              strokeWidth="0.5"
            />
          </motion.g>
        )
      })}
    </svg>
  )
}

export const IndiaMapChoropleth: React.FC<IndiaMapChoroplethProps> = ({
  data,
  title = 'State Distribution',
  titleHi = 'राज्य वितरण',
  subtitle = 'Research activity by state',
  height = 280,
}) => {
  const maxCount = Math.max(...data.map(d => d.count), 1)
  const topStates = [...data].sort((a, b) => b.count - a.count).slice(0, 5)

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

      <div className="relative" style={{ height }}>
        <IndiaMapPlaceholder maxCount={maxCount} data={data} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {topStates.map((state) => (
          <div key={state.state} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-saffron-400" />
            <span className="text-xs text-slate-600 dark:text-slate-300 truncate">{state.state}</span>
            <span className="text-xs font-semibold text-slate-900 dark:text-white ml-auto">
              {state.count.toLocaleString('en-IN')}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-center gap-3 text-xs text-slate-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-saffron-500" />
          <span>High</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-saffron-300" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-saffron-100" />
          <span>Low</span>
        </div>
      </div>
    </motion.div>
  )
}

export default IndiaMapChoropleth
