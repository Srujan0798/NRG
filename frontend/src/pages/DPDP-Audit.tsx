import React, { Suspense, lazy, useEffect, useState } from 'react'
import AuditEventList from '../components/AuditEventList/AuditEventList'
import ChainIntegrityFooter from '../components/ChainIntegrityFooter/ChainIntegrityFooter'
import { AuditEventRecord, queryService } from '../services/queryService'

const CitationDrawer = lazy(() => import('../components/CitationDrawer/CitationDrawer'))

const COPY = {
  eyebrow: 'DPDP audit trail',
  title: 'Signed activity history',
  body: 'Use this screen to show the professor exactly where a query was logged and how the chain verifies.',
  loading: 'Loading signed audit events',
  openEvent: 'Open event page',
}

export default function DPDPAudit() {
  const [events, setEvents] = useState<AuditEventRecord[]>([])
  const [selectedEvent, setSelectedEvent] = useState<AuditEventRecord | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    queryService.listAuditEvents(2000)
      .then((response) => {
        if (mounted) setEvents(response.events)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  const openEventPage = () => {
    if (selectedEvent) window.history.pushState(null, '', `/app/audit/event/${selectedEvent.hmac}`)
    if (selectedEvent) window.dispatchEvent(new PopStateEvent('popstate'))
  }

  return (
    <main id="main-content" tabIndex={-1} className="nrg-app-canvas min-h-screen px-4 py-8 text-nrg-text sm:px-6 lg:px-8">
      <section className="mx-auto max-w-6xl space-y-6">
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[var(--nrg-warning)]">{COPY.eyebrow}</p>
          <h1 className="text-3xl font-bold text-nrg-text sm:text-4xl">{COPY.title}</h1>
          <p className="max-w-3xl text-base leading-7 text-nrg-muted">{COPY.body}</p>
        </div>

        <ChainIntegrityFooter eventId={events[0]?.hmac} totalEvents={events.length} />

        {loading ? (
          <div className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-8 text-sm text-nrg-muted">
            {COPY.loading}
          </div>
        ) : (
          <AuditEventList events={events} onSelect={setSelectedEvent} />
        )}
      </section>

      <Suspense fallback={null}>
        <CitationDrawer
          citation={selectedEvent ? {
            id: selectedEvent.hmac,
            audit_event_id: selectedEvent.hmac,
            title: selectedEvent.action,
            source: 'Audit',
          } : null}
          isOpen={Boolean(selectedEvent)}
          onClose={() => setSelectedEvent(null)}
        />
      </Suspense>

      {selectedEvent && (
        <button
          type="button"
          data-testid="open-audit-event-page"
          onClick={openEventPage}
          className="fixed bottom-4 left-4 z-50 min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-4 py-2 text-sm font-bold text-nrg-text shadow-lg"
        >
          {COPY.openEvent}
        </button>
      )}
    </main>
  )
}
