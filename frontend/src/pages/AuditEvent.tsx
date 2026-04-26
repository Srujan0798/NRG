import React, { useEffect, useMemo, useState } from 'react'
import HmacProof from '../components/HmacProof/HmacProof'
import ChainIntegrityFooter from '../components/ChainIntegrityFooter/ChainIntegrityFooter'
import { AuditEventRecord, queryService } from '../services/queryService'

const COPY = {
  eyebrow: 'Audit event',
  title: 'Chain neighborhood',
  loading: 'Loading audit event',
  back: 'Back to audit trail',
  query: 'Query',
  status: 'Status',
}

function eventIdFromPath(): string {
  const parts = window.location.pathname.split('/')
  return decodeURIComponent(parts[parts.length - 1] || 'hmac-release-001')
}

export default function AuditEvent() {
  const eventId = useMemo(eventIdFromPath, [])
  const [event, setEvent] = useState<AuditEventRecord | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    queryService.getAuditEvent(eventId)
      .then((nextEvent) => {
        if (mounted) setEvent(nextEvent)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [eventId])

  const back = () => {
    window.history.pushState(null, '', '/app/audit')
    window.dispatchEvent(new PopStateEvent('popstate'))
  }

  return (
    <main id="main-content" tabIndex={-1} className="nrg-app-canvas min-h-screen px-4 py-8 text-nrg-text sm:px-6 lg:px-8">
      <section className="mx-auto max-w-4xl space-y-6">
        <button
          type="button"
          onClick={back}
          className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-4 py-2 text-sm font-bold text-nrg-text"
        >
          {COPY.back}
        </button>
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-[var(--nrg-warning)]">{COPY.eyebrow}</p>
          <h1 className="text-3xl font-bold text-nrg-text sm:text-4xl">{COPY.title}</h1>
          <p className="font-mono text-sm text-nrg-muted">{eventId}</p>
        </div>

        {loading ? (
          <div className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-8 text-sm text-nrg-muted">
            {COPY.loading}
          </div>
        ) : (
          <>
            <HmacProof auditEventId={eventId} />
            <div className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-4">
              <dl className="grid gap-3 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="font-semibold text-nrg-muted">{COPY.query}</dt>
                  <dd className="text-right text-nrg-text">{event?.query || event?.action}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="font-semibold text-nrg-muted">{COPY.status}</dt>
                  <dd className="text-right text-nrg-text">{event?.status || event?.integrity_status}</dd>
                </div>
              </dl>
            </div>
            <ChainIntegrityFooter eventId={eventId} totalEvents={1} />
          </>
        )}
      </section>
    </main>
  )
}
