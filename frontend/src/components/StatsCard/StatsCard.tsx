import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

interface StatsCardProps {
  label: string
  labelHi?: string
  value: number
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
  accentColor = '#ff6b35',
  delay = 0,
  format = 'number',
  'data-testid': testId,
}) => {
  const animatedValue = useAnimatedCounter(value, 1600, delay)
  const isHindi = !!labelHi

  return (
    <motion.div
      className="relative overflow-hidden rounded-2xl p-5 bg-white border border-slate-200/80 shadow-md transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lg"
      style={{
        borderLeft: `4px solid ${accentColor}`,
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay / 1000, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      data-testid={testId}
    >
      <div className="absolute top-0 right-0 w-32 h-32 opacity-5 rounded-bl-full" style={{ background: accentColor }} />

      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</p>
          {isHindi && (
            <p className="text-xs font-medium text-slate-400 font-hindi mt-0.5">{labelHi}</p>
          )}
        </div>
        {icon && (
          <motion.div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${accentColor}15`, color: accentColor }}
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

      <p className="text-3xl font-bold text-slate-900 font-mono tracking-tight">
        {formatNumber(animatedValue, format)}
      </p>
      <p className="text-xs text-slate-500 mt-1">{sublabel}</p>
    </motion.div>
  )
}

export default StatsCard
