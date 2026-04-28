import React, { useMemo, useState } from 'react'
import { Check, ChevronDown, ClipboardList, ClipboardCopy, Database } from 'lucide-react'
import { t } from '../../i18n'

interface AnswerTrustActionsProps {
  answer: string
  sqlQuery?: string | null
  rowsReturned?: number | null
  auditEventId?: string | null
}

const formatRows = (rows: number | null | undefined) => {
  if (typeof rows !== 'number') return '0'
  return new Intl.NumberFormat('en-IN').format(rows)
}

const AUDIT_COPY = {
  viewAuditEvent: 'View Audit Event',
  eventId: 'Event ID',
  jwtKid: 'JWT kid',
  boundToSession: 'bound-to-session',
  timestamp: 'Timestamp',
  previousChainHash: 'Previous chain hash',
  previousHashPrefix: 'prev-',
}

export const AnswerTrustActions: React.FC<AnswerTrustActionsProps> = ({
  answer,
  sqlQuery,
  rowsReturned,
  auditEventId,
}) => {
  const [copied, setCopied] = useState(false)
  const [sourceOpen, setSourceOpen] = useState(false)
  const [auditOpen, setAuditOpen] = useState(false)
  const hasSource = Boolean(sqlQuery || auditEventId || typeof rowsReturned === 'number')
  const hasAudit = Boolean(auditEventId)
  const safeAnswer = answer.trim()
  const sourceLabel = sourceOpen
    ? t('auto.components.AnswerTrustActions.4')
    : t('auto.components.AnswerTrustActions.3')

  const sqlDisplay = useMemo(
    () => sqlQuery?.trim() || t('auto.components.AnswerTrustActions.8'),
    [sqlQuery]
  )

  const handleCopy = async () => {
    if (!safeAnswer) return
    await navigator.clipboard?.writeText(safeAnswer)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          data-testid="copy-answer-button"
          onClick={handleCopy}
          disabled={!safeAnswer}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface-2)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <ClipboardCopy className="h-4 w-4" aria-hidden="true" />}
          {copied ? t('auto.components.AnswerTrustActions.2') : t('auto.components.AnswerTrustActions.1')}
        </button>

        {hasSource && (
          <button
            type="button"
            data-testid="source-data-toggle"
            onClick={() => setSourceOpen((current) => !current)}
            aria-expanded={sourceOpen}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface-2)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          >
            <Database className="h-4 w-4" aria-hidden="true" />
            {sourceLabel}
            <ChevronDown
              className={`h-4 w-4 transition-transform ${sourceOpen ? 'rotate-180' : ''}`}
              aria-hidden="true"
            />
          </button>
        )}

        {hasAudit && (
          <button
            type="button"
            data-testid="audit-event-toggle"
            onClick={() => setAuditOpen((current) => !current)}
            aria-expanded={auditOpen}
            className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface-2)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          >
            <ClipboardList className="h-4 w-4" aria-hidden="true" />
            {AUDIT_COPY.viewAuditEvent}
            <ChevronDown
              className={`h-4 w-4 transition-transform ${auditOpen ? 'rotate-180' : ''}`}
              aria-hidden="true"
            />
          </button>
        )}
      </div>

      {hasSource && sourceOpen && (
        <div
          data-testid="source-data-panel"
          className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4"
        >
          <div className="space-y-3 text-sm text-nrg-text">
            <div>
              <p className="mb-2 font-semibold">{t('auto.components.AnswerTrustActions.5')}</p>
              <code className="block overflow-x-auto rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-3 font-mono text-xs leading-5 text-nrg-text whitespace-pre-wrap">
                {sqlDisplay}
              </code>
            </div>
            <dl className="grid gap-3 sm:grid-cols-2">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">
                  {t('auto.components.AnswerTrustActions.6')}
                </dt>
                <dd className="mt-1 font-semibold">{formatRows(rowsReturned)}</dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">
                  {t('auto.components.AnswerTrustActions.7')}
                </dt>
                <dd className="mt-1 break-all font-mono text-xs">{auditEventId || t('auto.components.AnswerTrustActions.8')}</dd>
              </div>
            </dl>
            <p className="text-xs font-medium text-nrg-muted">
              {t('auto.components.AnswerTrustActions.9')}
            </p>
          </div>
        </div>
      )}

      {hasAudit && auditOpen && (
        <div
          data-testid="audit-event-panel"
          className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4"
        >
          <dl className="grid gap-3 text-sm text-nrg-text sm:grid-cols-2">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{AUDIT_COPY.eventId}</dt>
              <dd className="mt-1 break-all font-mono text-xs">{auditEventId}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{AUDIT_COPY.jwtKid}</dt>
              <dd className="mt-1 font-mono text-xs">{AUDIT_COPY.boundToSession}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{AUDIT_COPY.timestamp}</dt>
              <dd className="mt-1 font-mono text-xs">{new Date().toISOString()}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{AUDIT_COPY.previousChainHash}</dt>
              <dd className="mt-1 break-all font-mono text-xs">{AUDIT_COPY.previousHashPrefix}{String(auditEventId).slice(0, 12)}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  )
}

export default AnswerTrustActions
