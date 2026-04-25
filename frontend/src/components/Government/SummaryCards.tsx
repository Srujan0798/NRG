import React from 'react'
import { motion } from 'framer-motion'
import { Building2, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react'

interface SummaryCardProps {
  title: string
  titleHi: string
  value: string | number
  change?: string
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ReactNode
  accentColor?: string
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  titleHi,
  value,
  change,
  changeType = 'neutral',
  icon,
  accentColor = 'var(--nrg-chart-1)',
}) => {
  const changeColor = {
    positive: 'text-green-600 dark:text-green-400',
    negative: 'text-red-600 dark:text-red-400',
    neutral: 'text-nrg-muted',
  }[changeType]

  return (
    <motion.div
      className="nrg-panel relative overflow-hidden p-5"
      style={{ borderLeft: `var(--nrg-accent-border-width) solid ${accentColor}` }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: 'var(--nrg-elevation-2)' }}
      transition={{ duration: 0.3 }}
    >
      <div className="absolute top-0 right-0 w-24 h-24 opacity-5 rounded-bl-full" style={{ background: accentColor }} />

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-nrg-muted uppercase tracking-[0.12em]">{title}</p>
          <p className="text-xs font-devanagari text-nrg-muted">{titleHi}</p>
          <p className="text-2xl font-bold text-nrg-text mt-1 font-display">{value}</p>
          {change && (
            <p className={`text-xs font-medium mt-1 flex items-center gap-1 ${changeColor}`}>
              <TrendingUp size={12} />
              {change}
            </p>
          )}
        </div>
        <motion.div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: `${accentColor}15`, color: accentColor }}
          whileHover={{ scale: 1.1, rotate: 5 }}
        >
          {icon}
        </motion.div>
      </div>
    </motion.div>
  )
}

interface MinistrySummaryCardProps {
  ministry: string
  ministryHi: string
  institutionCount: number
  researcherCount: number
  fundingCr: number
  topArea: string
}

export const MinistrySummaryCard: React.FC<MinistrySummaryCardProps> = ({
  ministry,
  ministryHi,
  institutionCount,
  researcherCount,
  fundingCr,
  topArea,
}) => (
  <motion.div
    className="nrg-panel overflow-hidden"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ y: -2, boxShadow: 'var(--nrg-elevation-2)' }}
  >
    <div className="px-5 py-4 bg-[var(--glass-bg)] border-b border-nrg-border">
      <div className="flex items-center gap-2">
        <Building2 size={16} className="text-saffron-600 dark:text-saffron-400" />
        <span className="text-sm font-semibold text-nrg-text">{ministry}</span>
        <span className="text-xs font-devanagari text-nrg-muted">({ministryHi})</span>
      </div>
    </div>
    <div className="p-5 grid grid-cols-2 gap-4">
      <div>
        <p className="text-xs text-nrg-muted">Institutions</p>
        <p className="text-lg font-bold text-nrg-text">{institutionCount.toLocaleString('en-IN')}</p>
      </div>
      <div>
        <p className="text-xs text-nrg-muted">Researchers</p>
        <p className="text-lg font-bold text-nrg-text">{researcherCount.toLocaleString('en-IN')}</p>
      </div>
      <div>
        <p className="text-xs text-nrg-muted">Funding</p>
        <p className="text-lg font-bold text-nrg-text">₹{fundingCr}Cr</p>
      </div>
      <div>
        <p className="text-xs text-nrg-muted">Top Area</p>
        <p className="text-sm font-medium text-nrg-text truncate">{topArea}</p>
      </div>
    </div>
  </motion.div>
)

interface AlertCardProps {
  type: 'warning' | 'critical' | 'info'
  title: string
  message: string
  action?: string
}

export const AlertCard: React.FC<AlertCardProps> = ({ type, title, message, action }) => {
  const config = {
    warning: {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      border: 'border-amber-200 dark:border-amber-700',
      icon: <AlertCircle size={18} className="text-amber-600" />,
    },
    critical: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-700',
      icon: <AlertCircle size={18} className="text-red-600" />,
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-700',
      icon: <CheckCircle size={18} className="text-blue-600" />,
    },
  }[type]

  return (
    <motion.div
      className={`flex items-start gap-3 p-4 rounded-xl ${config.bg} border ${config.border}`}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
    >
      <div className="shrink-0 mt-0.5">{config.icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-nrg-text">{title}</p>
        <p className="text-xs text-nrg-muted mt-0.5">{message}</p>
      </div>
      {action && (
        <button className="text-xs font-medium text-saffron-600 hover:text-saffron-700 shrink-0">
          {action}
        </button>
      )}
    </motion.div>
  )
}

export default SummaryCard
