import React from 'react'
import { useAnimatedCounter } from '../../hooks/useAnimatedCounter'
import { heroLabels } from '../../i18n/hero-copy'

interface ScaleMetric {
  label: string
  value: number | string
  suffix?: string
  compact?: boolean
}

const metrics: ScaleMetric[] = [
  { label: 'Researchers', value: 50000, compact: true },
  { label: 'Publications', value: 50000, compact: true },
  { label: 'Institutions', value: 181 },
  { label: 'Tables', value: 58 },
  { label: 'DPDP-compliant', value: 'Active' },
]

function formatMetric(value: number | string, metric: ScaleMetric) {
  if (typeof value === 'string') return value
  if (metric.compact && value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
  if (metric.compact && value >= 1000) return `${Math.round(value / 1000)}K`
  return `${value.toLocaleString('en-IN')}${metric.suffix || ''}`
}

const Counter: React.FC<{ metric: ScaleMetric; delay: number }> = ({ metric, delay }) => {
  const animatedValue = useAnimatedCounter(typeof metric.value === 'number' ? metric.value : 0, 4800, delay)
  const value = typeof metric.value === 'number' ? animatedValue : metric.value

  return (
    <div className="rounded-xl border border-nrg-border bg-[var(--nrg-surface-1)] px-4 py-3 shadow-sm">
      <div data-testid="scale-counter" className="font-mono text-xl font-bold tabular-nums text-nrg-text">
        {formatMetric(value, metric)}
      </div>
      <div className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">
        {metric.label}
      </div>
    </div>
  )
}

export const ScaleStrip: React.FC = () => (
  <section aria-label={heroLabels.scale} className="grid gap-3 sm:grid-cols-5">
    {metrics.map((metric, index) => (
      <Counter key={metric.label} metric={metric} delay={index * 80} />
    ))}
  </section>
)

export default ScaleStrip
