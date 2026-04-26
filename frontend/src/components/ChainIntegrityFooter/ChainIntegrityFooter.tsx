import React, { useState } from 'react'
import { CheckCircle2, ShieldCheck } from 'lucide-react'
import { queryService } from '../../services/queryService'

interface ChainIntegrityFooterProps {
  eventId?: string
  totalEvents?: number
}

const COPY = {
  title: 'Audit chain',
  body: 'Every query and proof action is chained to the previous signed event.',
  verify: 'Verify integrity',
  intact: 'Chain intact',
  verifying: 'Checking chain',
  total: 'events sealed',
}

export const ChainIntegrityFooter: React.FC<ChainIntegrityFooterProps> = ({ eventId = 'hmac-release-001', totalEvents = 0 }) => {
  const [status, setStatus] = useState<'idle' | 'checking' | 'intact'>('idle')

  const verify = async () => {
    setStatus('checking')
    const result = await queryService.verifyAuditEvent(eventId)
    setStatus(result.verified ? 'intact' : 'idle')
  }

  return (
    <footer data-testid="chain-integrity-footer" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--nrg-success-soft)] text-[var(--nrg-success)]">
            <ShieldCheck size={18} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-sm font-bold text-nrg-text">{COPY.title}</h2>
            <p className="mt-1 text-sm text-nrg-muted">{COPY.body}</p>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wider text-nrg-muted">
              {totalEvents.toLocaleString('en-IN')} {COPY.total}
            </p>
          </div>
        </div>
        <button
          type="button"
          data-testid="chain-verify-button"
          onClick={() => void verify()}
          disabled={status === 'checking'}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[var(--nrg-success)] px-4 py-2 text-sm font-bold text-white transition hover:brightness-105 disabled:cursor-wait disabled:opacity-70"
        >
          <CheckCircle2 size={16} aria-hidden="true" />
          {status === 'checking' ? COPY.verifying : status === 'intact' ? COPY.intact : COPY.verify}
        </button>
      </div>
    </footer>
  )
}

export default ChainIntegrityFooter
