import React, { lazy, Suspense, useEffect, useState } from 'react'
import type { PersonaRole } from '../../services/authService'
import type { Citation } from '../../services/queryService'
import { heroCopy, heroLabels } from '../../i18n/hero-copy'
import SearchBar from '../SearchBar'
import { ScaleStrip } from '../ScaleStrip/ScaleStrip'
import { QueryPhaseProgress } from '../QueryPhaseProgress'
import type { StreamingProofPayload } from '../StreamingAnswerPanel'

const StreamingAnswerPanel = lazy(() => import('../StreamingAnswerPanel'))
const SideBySidePanel = lazy(() => import('../SideBySidePanel/SideBySidePanel'))

interface QueryWorkbenchProps {
  role: PersonaRole
  onCitationClick: (citation: Citation) => void
  onProofOpen: (auditEventId: string) => void
  onProofChange: (payload: StreamingProofPayload) => void
}

type QueryDomain = 'research' | 'policy' | 'industry'

const roleToDomain = (role: PersonaRole): QueryDomain => {
  if (role === 'government') return 'policy'
  if (role === 'industry') return 'industry'
  return 'research'
}

const WORKBENCH_COPY = {
  eyebrow: 'Reviewer path',
  emptyTitle: 'Start with one high-signal question',
  emptyBody: 'Suggestion chips run immediately and keep source proof visible beside the answer.',
}

const AnswerPanelFallback = () => (
  <section
    data-testid="streaming-answer-panel"
    className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-5 shadow-lg"
    aria-live="polite"
  >
    <div data-testid="phase-planning" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4">
      <h2 className="text-sm font-semibold text-nrg-text">{heroLabels.phasePlanning}</h2>
      <p className="mt-2 text-sm text-nrg-muted">{heroLabels.phaseWaiting}</p>
    </div>
  </section>
)

export function QueryWorkbench({
  role,
  onCitationClick,
  onProofOpen,
  onProofChange,
}: QueryWorkbenchProps) {
  const bootQuery = typeof window === 'undefined' ? '' : window.__nrgBootQuery || ''
  const shouldSubmitBootQuery = typeof window !== 'undefined' && window.__nrgBootSubmit === true && bootQuery.trim().length > 0
  const [searchValue, setSearchValue] = useState(bootQuery)
  const [lastQuery, setLastQuery] = useState(shouldSubmitBootQuery ? bootQuery.trim() : '')
  const [streamNonce, setStreamNonce] = useState(0)
  const [isSlowQuery, setIsSlowQuery] = useState(false)

  const handleSubmit = (query: string) => {
    setSearchValue(query)
    if (typeof window !== 'undefined') {
      window.__nrgBootQuery = query
      window.__nrgBootSubmit = false
    }
    setLastQuery(query)
    setStreamNonce((current) => current + 1)
    setIsSlowQuery(false)
  }

  useEffect(() => {
    if (!lastQuery) return undefined
    const timer = window.setTimeout(() => setIsSlowQuery(true), 3000)
    return () => window.clearTimeout(timer)
  }, [lastQuery])

  return (
    <section
      data-testid="query-workbench"
      className="rounded-lg border border-nrg-border bg-[var(--nrg-surface)] p-4 shadow-sm"
    >
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">{WORKBENCH_COPY.eyebrow}</p>
        <div>
          <h1 className="max-w-3xl text-3xl font-bold leading-tight text-nrg-text sm:text-4xl">{heroCopy.welcome}</h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-nrg-muted">{heroCopy.trustLine}</p>
        </div>
        <div className="mt-4">
          <ScaleStrip />
        </div>
      </div>

      <div className="mt-5">
        <SearchBar
          value={searchValue}
          onValueChange={(query) => {
            setSearchValue(query)
            if (typeof window !== 'undefined') window.__nrgBootQuery = query
          }}
          onSubmit={handleSubmit}
        />
      </div>

      <div className="mt-5 space-y-4">
        {!lastQuery && (
          <div className="rounded-lg border border-dashed border-nrg-border bg-[var(--nrg-surface-1)] p-4">
            <h2 className="text-sm font-semibold text-nrg-text">{WORKBENCH_COPY.emptyTitle}</h2>
            <p className="mt-2 text-sm text-nrg-muted">{WORKBENCH_COPY.emptyBody}</p>
          </div>
        )}

        {lastQuery && (
          <Suspense fallback={<AnswerPanelFallback />}>
            {isSlowQuery && <QueryPhaseProgress domain={roleToDomain(role)} isSlowQuery={isSlowQuery} />}
            <StreamingAnswerPanel
              key={`${role}:${streamNonce}:${lastQuery}`}
              query={lastQuery}
              onCitationClick={onCitationClick}
              onProofOpen={onProofOpen}
              onProofChange={onProofChange}
            />
            <SideBySidePanel />
          </Suspense>
        )}
      </div>
    </section>
  )
}

export default QueryWorkbench
