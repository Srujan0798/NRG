import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

interface StatsCardProps {
  label: string
  labelHi?: string
  value: number | string | null | undefined
  sublabel: string
  icon?: React.ReactNode
  accentColor?: string
  delay?: number
  format?: 'number' | 'currency' | 'percent'
  'data-testid'?: string
}

function useAnimatedCounter(
  endValue: number,
  duration: number = 1600,
  delay: number = 0
) {
  const [displayValue, setDisplayValue] = useState(0)
  const startTimeRef = useRef<number | null>(null)
  const rafRef = useRef<number | null>(null)
  const startValueRef = useRef(0)

  useEffect(() => {
    const startAnimation = () => {
      startValueRef.current = 0
      startTimeRef.current = null

      const animate = (timestamp: number) => {
        if (!startTimeRef.current) startTimeRef.current = timestamp
        const elapsed = timestamp - startTimeRef.current
        const progress = Math.min(elapsed / duration, 1)

        const easeOutQuart = 1 - Math.pow(1 - progress, 4)
        const current = startValueRef.current + (endValue - startValueRef.current) * easeOutQuart

        setDisplayValue(Math.round(current))

        if (progress < 1) {
          rafRef.current = requestAnimationFrame(animate)
        }
      }

      rafRef.current = requestAnimationFrame(animate)
    }

    const timeoutId = setTimeout(startAnimation, delay)
    return () => {
      clearTimeout(timeoutId)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [endValue, duration, delay])

  return displayValue
}

function formatNumber(value: number, format: 'number' | 'currency' | 'percent'): string {
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(value)
    case 'percent':
      return new Intl.NumberFormat('en-IN', {
        style: 'percent',
        maximumFractionDigits: 1,
      }).format(value / 100)
    default:
      return new Intl.NumberFormat('en-IN').format(value)
  }
}

export const StatsCard: React.FC<StatsCardProps> = ({
  label,
  labelHi,
  value,
  sublabel,
  icon,
  accentColor = 'var(--nrg-chart-1)',
  delay = 0,
  format = 'number',
  'data-testid': testId,
}) => {
  const hasNumericValue = typeof value === 'number' && Number.isFinite(value)
  const animatedValue = useAnimatedCounter(hasNumericValue ? value : 0, 1600, delay)
  const displayValue = hasNumericValue ? formatNumber(animatedValue, format) : String(value ?? 'Pending')
  const isHindi = !!labelHi

  return (
    <motion.div
      className="nrg-panel relative overflow-hidden p-5 transition-all duration-300 hover:-translate-y-0.5"
      style={{
        borderLeft: `var(--nrg-accent-border-width) solid ${accentColor}`,
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay / 1000, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      data-testid={testId}
    >
      <div className="absolute inset-x-0 top-0 h-px opacity-80" style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }} />
      <div className="absolute -top-10 -right-8 w-28 h-28 opacity-15 rounded-full blur-2xl" style={{ background: accentColor }} />

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-[0.6875rem] font-semibold text-nrg-muted uppercase tracking-[0.12em]">{label}</p>
          {isHindi && (
            <p className="text-xs font-medium text-nrg-muted font-devanagari mt-0.5">{labelHi}</p>
          )}
        </div>
        {icon && (
          <motion.div
            className="w-11 h-11 rounded-2xl flex items-center justify-center border"
            style={{ background: `${accentColor}18`, color: accentColor, borderColor: `${accentColor}55` }}
            whileHover={{ scale: 1.1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
          >
            {icon}
          </motion.div>
        )}
      </div>

      <div
        className="h-0.5 rounded-full mb-3 transition-all duration-500"
        style={{
          background: `linear-gradient(90deg, ${accentColor}, ${accentColor}40)`,
        }}
      />

      <p className="text-3xl font-bold text-nrg-text font-display tracking-tight">
        {displayValue}
      </p>
      <p className="text-xs text-nrg-muted mt-1">{sublabel}</p>
    </motion.div>
  )
}

export default StatsCard
