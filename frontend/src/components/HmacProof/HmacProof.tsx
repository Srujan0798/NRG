import React, { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, GitCommit, ShieldCheck } from 'lucide-react'
import { AuditEventRecord, VerifyAuditEventResponse, queryService } from '../../services/queryService'
import { emitTelemetry } from '../../lib/telemetry'

interface HmacProofProps {
  auditEventId: string
}

const COPY = {
  heading: 'HMAC chain proof',
  loading: 'Loading signed event',
  current: 'Current',
  previous: 'Previous',
  next: 'Next',
  verify: 'Verify integrity',
  verified: 'Chain intact',
  pending: 'Verification pending',
  failed: 'Verification failed',
  event: 'Audit event',
  action: 'Action',
  actor: 'Actor',
  timestamp: 'Timestamp',
}

const shortHash = (hash?: string | null) => hash ? `${hash.slice(0, 12)}...${hash.slice(-6)}` : 'Boundary'

export const HmacProof: React.FC<HmacProofProps> = ({ auditEventId }) => {
  const [event, setEvent] = useState<AuditEventRecord | null>(null)
  const [verification, setVerification] = useState<VerifyAuditEventResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [verifying, setVerifying] = useState(false)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    queryService.getAuditEvent(auditEventId)
      .then((nextEvent) => {
        if (mounted) setEvent(nextEvent)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [auditEventId])

  const nodes = useMemo(() => {
    const hmac = event?.hmac || auditEventId
    return [
      { label: COPY.previous, value: event?.prev_hmac || null },
      { label: COPY.current, value: event?.current_hmac || hmac },
      { label: COPY.next, value: event?.next_hmac || null },
    ]
  }, [auditEventId, event])

  const verify = async () => {
    setVerifying(true)
    emitTelemetry('audit.verified', { audit_event_id: auditEventId, state: 'requested' })
    try {
      const result = await queryService.verifyAuditEvent(auditEventId)
      setVerification(result)
      emitTelemetry('audit.verified', {
        audit_event_id: auditEventId,
        verified: result.verified,
        latency_ms: result.latency_ms || null,
      })
    } finally {
      setVerifying(false)
    }
  }

  const statusLabel = verification
    ? verification.verified ? COPY.verified : COPY.failed
    : COPY.pending

  return (
    <section data-testid="hmac-proof" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--nrg-success-soft)] text-[var(--nrg-success)]">
            <ShieldCheck size={18} aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-sm font-semibold text-nrg-text">{COPY.heading}</h3>
            <p className="mt-1 font-mono text-xs text-nrg-muted">{auditEventId}</p>
          </div>
        </div>
        <span
          data-testid="hmac-proof-status"
          className="rounded-full border border-nrg-border bg-[var(--nrg-surface-1)] px-3 py-1 text-xs font-semibold text-nrg-text"
        >
          {statusLabel}
        </span>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-nrg-muted">{COPY.loading}</p>
      ) : (
        <div className="mt-4 space-y-4">
          <div className="grid gap-2">
            {nodes.map((node) => (
              <div key={node.label} className="flex items-center gap-3 rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] px-3 py-2">
                <GitCommit size={14} className="text-[var(--nrg-focus)]" aria-hidden="true" />
                <span className="w-20 text-xs font-semibold uppercase tracking-wider text-nrg-muted">{node.label}</span>
                <code className="truncate text-xs text-nrg-text">{shortHash(node.value)}</code>
              </div>
            ))}
          </div>

          <dl className="grid gap-2 text-xs">
            <div className="flex justify-between gap-3">
              <dt className="font-semibold text-nrg-muted">{COPY.event}</dt>
              <dd className="text-right font-mono text-nrg-text">{shortHash(event?.hmac)}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="font-semibold text-nrg-muted">{COPY.action}</dt>
              <dd className="text-right text-nrg-text">{event?.action}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="font-semibold text-nrg-muted">{COPY.actor}</dt>
              <dd className="text-right text-nrg-text">{event?.actor || event?.user_id}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="font-semibold text-nrg-muted">{COPY.timestamp}</dt>
              <dd className="text-right text-nrg-text">{event?.timestamp ? new Date(event.timestamp).toLocaleString('en-IN') : '-'}</dd>
            </div>
          </dl>

          <button
            type="button"
            data-testid="verify-hmac-button"
            onClick={() => void verify()}
            disabled={verifying}
            className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--nrg-success)] px-4 py-2 text-sm font-bold text-white transition hover:brightness-105 disabled:cursor-wait disabled:opacity-70"
          >
            <CheckCircle2 size={16} aria-hidden="true" />
            {verifying ? COPY.pending : COPY.verify}
          </button>
        </div>
      )}
    </section>
  )
}

export default HmacProof
