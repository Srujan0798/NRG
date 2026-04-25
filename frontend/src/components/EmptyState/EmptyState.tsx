import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search } from 'lucide-react'
import { emitTelemetry } from '../../lib/telemetry'

interface EmptyStateProps {
  title?: string
  body?: string
  primaryLabel?: string
  secondaryLabel?: string
  onPrimary?: () => void
  onSecondary?: () => void
}

export function EmptyState({
  title = 'No matches in this slice.',
  body = 'Try widening the year range, removing the location filter, or switching to aggregated results.',
  primaryLabel = 'Widen the search',
  secondaryLabel = 'Edit query',
  onPrimary,
  onSecondary,
}: EmptyStateProps) {
  useEffect(() => {
    emitTelemetry('empty.shown', {
      cause: title,
      route: window.location.pathname,
    })
  }, [title])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-center dark:border-amber-800 dark:bg-amber-950/30"
    >
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-amber-700 shadow-sm dark:bg-navy-800 dark:text-amber-300">
        <Search size={24} />
      </div>
      <h3 className="mt-4 text-base font-semibold text-amber-950 dark:text-amber-100">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-amber-800 dark:text-amber-200">{body}</p>
      <div className="mt-4 flex flex-col justify-center gap-2 sm:flex-row">
        {onPrimary && (
          <button
            type="button"
            onClick={onPrimary}
            className="min-h-11 rounded-xl bg-amber-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-800"
          >
            {primaryLabel}
          </button>
        )}
        {onSecondary && (
          <button
            type="button"
            onClick={onSecondary}
            className="min-h-11 rounded-xl border border-amber-300 px-4 py-2 text-sm font-semibold text-amber-800 transition hover:bg-amber-100 dark:text-amber-100"
          >
            {secondaryLabel}
          </button>
        )}
      </div>
    </motion.div>
  )
}

export default EmptyState
