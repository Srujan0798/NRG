import React, { Suspense, lazy, useState, useEffect } from 'react'
import SearchBar from '../components/SearchBar'
import { ScaleStrip } from '../components/ScaleStrip/ScaleStrip'
import { QueryPhaseProgress } from '../components/QueryPhaseProgress'
import { Citation } from '../services/queryService'
import { heroCopy, heroLabels } from '../i18n/hero-copy'
import { useAuth } from '../hooks/useAuth'
import PersonaToggle from '../components/PersonaToggle'

const StreamingAnswerPanel = lazy(() => import('../components/StreamingAnswerPanel'))
const CitationDrawer = lazy(() => import('../components/CitationDrawer/CitationDrawer'))
const SideBySidePanel = lazy(() => import('../components/SideBySidePanel/SideBySidePanel'))

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

type QueryDomain = 'research' | 'policy' | 'industry'

const roleToDomain = (role?: string): QueryDomain => {
  if (role === 'government') return 'policy'
  if (role === 'industry') return 'industry'
  return 'research'
}

const tierCopy: Record<string, { label: string; className: string; scope: string }> = {
  researcher: {
    label: 'Researcher',
    className: 'border-indigo-200 bg-indigo-50 text-indigo-800',
    scope: 'Full researcher workspace with source rows and identified records where policy allows.',
  },
  government: {
    label: 'Government',
    className: 'border-amber-200 bg-amber-50 text-amber-900',
    scope: 'Aggregated cohorts, state-level numbers, and k-anonymized policy evidence.',
  },
  industry: {
    label: 'Industry',
    className: 'border-slate-200 bg-slate-100 text-slate-800',
    scope: 'Anonymized labels and partnership opportunities without personal identifiers.',
  },
}

export const Hero: React.FC = () => {
  const bootQuery = typeof window === 'undefined' ? '' : window.__nrgBootQuery || ''
  const shouldSubmitBootQuery = typeof window !== 'undefined' && window.__nrgBootSubmit === true && bootQuery.trim().length > 0
  const [searchValue, setSearchValue] = useState(bootQuery)
  const [lastQuery, setLastQuery] = useState(shouldSubmitBootQuery ? bootQuery.trim() : '')
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [isCitationOpen, setIsCitationOpen] = useState(false)
  const [isSlowQuery, setIsSlowQuery] = useState(false)
  const { user, logout } = useAuth()
  const tier = tierCopy[user?.role || 'researcher']

  useEffect(() => {
    document.title = 'NRG · Ask National Research Graph'
  }, [])

  const handleSubmit = (query: string) => {
    setSearchValue(query)
    if (typeof window !== 'undefined') {
      window.__nrgBootQuery = query
      window.__nrgBootSubmit = false
    }
    setLastQuery(query)
    setIsSlowQuery(false)
  }

  useEffect(() => {
    if (!lastQuery) return
    const timer = window.setTimeout(() => setIsSlowQuery(true), 3000)
    return () => window.clearTimeout(timer)
  }, [lastQuery])

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation)
    setIsCitationOpen(true)
  }

  const handleProofOpen = (auditEventId: string) => {
    setSelectedCitation({
      id: auditEventId,
      audit_event_id: auditEventId,
      title: 'Verified audit event',
      source: 'Audit',
    })
    setIsCitationOpen(true)
  }

  return (
    <main id="main-content" tabIndex={-1} className="nrg-app-canvas min-h-screen px-4 py-6 text-nrg-text sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl flex-col gap-7">
        <header className="flex flex-col gap-4 border-b border-nrg-border pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-950 text-base font-bold text-[#ff8b4a]">
              न
            </div>
            <div>
              <p className="font-devanagari text-lg font-bold leading-tight">राष्ट्रीय गवेषण मंच</p>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">National Research Graph</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <PersonaToggle />
            <button
              type="button"
              onClick={() => void logout()}
              className="min-h-10 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
            >
              Logout
            </button>
          </div>
        </header>
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--nrg-warning)]">
            {heroCopy.productName}</p>
          <h1 className="max-w-4xl text-4xl font-bold leading-tight text-nrg-text sm:text-5xl">
            {heroCopy.welcome}</h1>
          <p className="max-w-2xl text-base leading-7 text-nrg-muted sm:text-lg">
            {heroCopy.trustLine}</p>
        </div>

        <div className={`rounded-lg border px-4 py-3 text-sm font-medium ${tier.className}`} data-testid="tier-banner">
          You are viewing as {tier.label}. {tier.scope}
        </div>

        <div className="sticky top-0 z-30 rounded-lg bg-[var(--nrg-app-bg)] py-2 sm:static sm:bg-transparent sm:py-0">
          <SearchBar
            value={searchValue}
            onValueChange={(query) => {
              setSearchValue(query)
              if (typeof window !== 'undefined') window.__nrgBootQuery = query
            }}
            onSubmit={handleSubmit}
          />
        </div>

        <ScaleStrip />

        {lastQuery && (
          <Suspense fallback={<AnswerPanelFallback />}>
            {isSlowQuery && (
              <QueryPhaseProgress domain={roleToDomain(user?.role)} isSlowQuery={isSlowQuery} />
            )}
            <StreamingAnswerPanel
              key={`${user?.role || 'anonymous'}:${lastQuery}`}
              query={lastQuery}
              onCitationClick={handleCitationClick}
              onProofOpen={handleProofOpen}
            />
            <SideBySidePanel />
          </Suspense>
        )}
      </section>

      <Suspense fallback={null}>
        <CitationDrawer
          citation={selectedCitation}
          isOpen={isCitationOpen}
          onClose={() => setIsCitationOpen(false)}
        />
      </Suspense>
    </main>
  )
}

export default Hero
