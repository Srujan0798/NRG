import React from 'react'
import { useAnimatedCounter } from '../../hooks/useAnimatedCounter'
import { heroLabels } from '../../i18n/hero-copy'

interface ScaleMetric {
  label: string
  value: number
  suffix?: string
  compact?: boolean
}

const metrics: ScaleMetric[] = [
  { label: 'Tables', value: 58 },
  { label: 'Researchers', value: 1200000, compact: true },
  { label: 'Institutes', value: 47000, compact: true },
  { label: 'Research Data', value: 600, suffix: 'GB' },
]

function formatMetric(value: number, metric: ScaleMetric) {
  if (metric.compact && value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
  if (metric.compact && value >= 1000) return `${Math.round(value / 1000)}K`
  return `${value.toLocaleString('en-IN')}${metric.suffix || ''}`
}

const Counter: React.FC<{ metric: ScaleMetric; delay: number }> = ({ metric, delay }) => {
  const value = useAnimatedCounter(metric.value, 4800, delay)

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
  <section aria-label={heroLabels.scale} className="grid gap-3 sm:grid-cols-4">
    {metrics.map((metric, index) => (
      <Counter key={metric.label} metric={metric} delay={index * 80} />
    ))}
  </section>
)

export default ScaleStrip
