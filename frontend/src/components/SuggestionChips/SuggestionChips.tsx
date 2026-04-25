import React, { useRef } from 'react'
import { heroCopy } from '../../i18n/en-IN'
import { t } from '../../i18n'

interface SuggestionChipsProps {
  suggestions?: string[]
  onSelect: (query: string) => void
  onSubmit?: (query: string) => void
  autoSubmitDelay?: number
}

export const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  suggestions = heroCopy.suggestions,
  onSelect,
  onSubmit,
  autoSubmitDelay = 200,
}) => {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleClick = (query: string) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    onSelect(query)
    timeoutRef.current = setTimeout(() => {
      onSubmit?.(query)
    }, autoSubmitDelay)
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2" aria-label={t("auto.components.SuggestionChips.SuggestionChips.1")}>
      {suggestions.slice(0, 4).map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          data-testid="suggestion-chip"
          onClick={() => handleClick(suggestion)}
          className="min-h-11 rounded-xl border border-nrg-border bg-[var(--nrg-surface-1)] px-4 py-3 text-left text-sm font-medium text-nrg-text shadow-sm transition hover:-translate-y-0.5 hover:border-[var(--nrg-focus)] hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--nrg-focus)]"
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}

export default SuggestionChips
