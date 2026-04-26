import React, { useEffect, useRef, useState } from 'react'
import { SearchIcon } from './Icons'
import { heroCopy, heroLabels } from '../i18n/hero-copy'
import { SuggestionChips } from './SuggestionChips/SuggestionChips'

interface SearchBarProps {
  autoFocus?: boolean
  placeholderRotation?: string[]
  onSubmit: (query: string) => void
  disabled?: boolean
  multiline?: boolean
  showSuggestions?: boolean
  value?: string
  onValueChange?: (query: string) => void
}

const MAX_QUERY_LENGTH = 50000

const SearchBar: React.FC<SearchBarProps> = ({
  autoFocus = true,
  placeholderRotation = heroCopy.placeholders,
  onSubmit,
  disabled = false,
  multiline = true,
  showSuggestions = true,
  value,
  onValueChange,
}) => {
  const [internalValue, setInternalValue] = useState('')
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [isFocused, setIsFocused] = useState(false)
  const [hint, setHint] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastSubmittedAtRef = useRef(0)
  const query = value ?? internalValue

  const setQuery = (nextValue: string) => {
    const truncated = nextValue.slice(0, MAX_QUERY_LENGTH)
    if (nextValue.length > MAX_QUERY_LENGTH) {
      setHint('Query trimmed to the maximum supported length')
    } else if (hint) {
      setHint('')
    }
    onValueChange?.(truncated)
    if (value === undefined) setInternalValue(truncated)
  }

  const submit = (rawQuery: string = query) => {
    const trimmed = rawQuery.trim()
    if (!trimmed) {
      setHint(heroCopy.emptyHint)
      return
    }
    if (disabled) return

    const now = Date.now()
    if (now - lastSubmittedAtRef.current < 650) return
    lastSubmittedAtRef.current = now
    onSubmit(trimmed)
  }

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])

  useEffect(() => {
    const handleShortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        inputRef.current?.focus()
      }
    }
    document.addEventListener('keydown', handleShortcut)
    return () => document.removeEventListener('keydown', handleShortcut)
  }, [])

  useEffect(() => {
    if (isFocused || placeholderRotation.length <= 1) return undefined
    const interval = setInterval(() => {
      setPlaceholderIndex((current) => (current + 1) % placeholderRotation.length)
    }, 4000)
    return () => clearInterval(interval)
  }, [isFocused, placeholderRotation.length])

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Enter') return
    if (multiline && event.shiftKey) {
      event.preventDefault()
      const target = event.currentTarget
      const start = target.selectionStart
      const end = target.selectionEnd
      const nextValue = `${query.slice(0, start)}\n${query.slice(end)}`
      setQuery(nextValue)
      requestAnimationFrame(() => {
        target.selectionStart = start + 1
        target.selectionEnd = start + 1
      })
      return
    }
    event.preventDefault()
    submit()
  }

  return (
    <div className="w-full space-y-4">
      <form
        onSubmit={(event) => {
          event.preventDefault()
          submit()
        }}
        className={`rounded-2xl border bg-[var(--nrg-surface-1)] shadow-lg transition ${
          hint.includes('maximum') ? 'border-amber-500' : 'border-nrg-border focus-within:border-[var(--nrg-focus)]'
        }`}
      >
        <label htmlFor="hero-search-input" className="sr-only">
          {heroLabels.search}</label>
        <div className="flex items-start gap-3 px-4 py-4">
          <SearchIcon className="mt-1 h-5 w-5 shrink-0 text-nrg-muted" />
          <textarea
            ref={inputRef}
            id="hero-search-input"
            data-testid="hero-search-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder={placeholderRotation[placeholderIndex] || heroCopy.placeholders[0]}
            rows={multiline ? 2 : 1}
            disabled={disabled}
            className="min-h-12 flex-1 resize-none bg-transparent text-base font-medium leading-6 text-nrg-text outline-none placeholder:text-nrg-muted disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={disabled}
            className="min-h-11 rounded-xl bg-[var(--nrg-navy)] px-4 py-2 text-sm font-semibold text-white transition hover:translate-y-[-0.0625rem] disabled:cursor-not-allowed disabled:opacity-60"
            aria-label={disabled ? 'Stop query' : 'Submit query'}
            aria-busy={disabled}
          >
            {disabled ? (
              <span className="inline-flex h-5 items-center gap-1" aria-hidden="true">
                <span className="h-1.5 w-1.5 rounded-full bg-white/90 motion-safe:animate-pulse" />
                <span className="h-1.5 w-1.5 rounded-full bg-white/70 motion-safe:animate-pulse [animation-delay:120ms]" />
                <span className="h-1.5 w-1.5 rounded-full bg-white/50 motion-safe:animate-pulse [animation-delay:240ms]" />
              </span>
            ) : 'Enter'}
          </button>
        </div>
      </form>

      {hint && (
        <p className="text-sm font-medium text-amber-700" role="status">
          {hint}
        </p>
      )}

      {showSuggestions && (
        <SuggestionChips
          onSelect={(nextQuery) => {
            setQuery(nextQuery)
            inputRef.current?.focus()
          }}
          onSubmit={submit}
        />
      )}
    </div>
  )
}

export default SearchBar
