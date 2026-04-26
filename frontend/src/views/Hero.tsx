import React, { Suspense, lazy, useState } from 'react'
import SearchBar from '../components/SearchBar'
import { ScaleStrip } from '../components/ScaleStrip/ScaleStrip'
import { Citation } from '../services/queryService'
import { heroCopy, heroLabels } from '../i18n/hero-copy'

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

export const Hero: React.FC = () => {
  const bootQuery = typeof window === 'undefined' ? '' : window.__nrgBootQuery || ''
  const shouldSubmitBootQuery = typeof window !== 'undefined' && window.__nrgBootSubmit === true && bootQuery.trim().length > 0
  const [searchValue, setSearchValue] = useState(bootQuery)
  const [lastQuery, setLastQuery] = useState(shouldSubmitBootQuery ? bootQuery.trim() : '')
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [isCitationOpen, setIsCitationOpen] = useState(false)

  const handleSubmit = (query: string) => {
    setSearchValue(query)
    if (typeof window !== 'undefined') {
      window.__nrgBootQuery = query
      window.__nrgBootSubmit = false
    }
    setLastQuery(query)
  }

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
    <main id="main-content" tabIndex={-1} className="nrg-app-canvas min-h-screen px-4 py-8 text-nrg-text sm:px-6 lg:px-8">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col justify-center gap-8">
        <div className="space-y-4">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--nrg-warning)]">
            {heroCopy.productName}</p>
          <h1 className="max-w-4xl text-4xl font-bold leading-tight text-nrg-text sm:text-5xl">
            {heroCopy.welcome}</h1>
          <p className="max-w-2xl text-base leading-7 text-nrg-muted sm:text-lg">
            {heroCopy.trustLine}</p>
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
            <StreamingAnswerPanel query={lastQuery} onCitationClick={handleCitationClick} onProofOpen={handleProofOpen} />
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
