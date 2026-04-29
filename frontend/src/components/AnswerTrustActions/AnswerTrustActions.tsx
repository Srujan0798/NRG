import React, { useMemo, useState } from 'react'
import { Check, ChevronDown, ClipboardList, ClipboardCopy, Database } from 'lucide-react'
import { t } from '../../i18n'
import type { QueryProvenance } from '../../services/queryService'

interface AnswerTrustActionsProps {
  answer: string
  sqlQuery?: string | null
  rowsReturned?: number | null
  auditEventId?: string | null
  provenance?: QueryProvenance
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

const HYBRID_COPY = {
  evidenceMix: 'Evidence mix',
  structuredSqlRows: 'Structured SQL rows',
  documentExcerpts: 'Document excerpts',
  sourceSummary: 'This answer combines measurable database evidence with retrieved document context.',
}

const getHybridEvidence = (provenance?: QueryProvenance) => {
  const evidence = provenance?.hybrid_evidence
  if (!evidence) return null
  return {
    sqlRows: typeof evidence.sql_rows === 'number' ? evidence.sql_rows : 0,
    documentChunks: typeof evidence.document_chunks === 'number' ? evidence.document_chunks : 0,
  }
}

export const AnswerTrustActions: React.FC<AnswerTrustActionsProps> = ({
  answer,
  sqlQuery,
  rowsReturned,
  auditEventId,
  provenance,
}) => {
  const [copied, setCopied] = useState(false)
  const [sourceOpen, setSourceOpen] = useState(false)
  const [auditOpen, setAuditOpen] = useState(false)
  const hybridEvidence = getHybridEvidence(provenance)
  const hasSource = Boolean(sqlQuery || auditEventId || typeof rowsReturned === 'number' || hybridEvidence)
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
              {hybridEvidence && (
                <div
                  data-testid="hybrid-evidence-source"
                  className="mb-3 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-3"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{HYBRID_COPY.evidenceMix}</p>
                  <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                    <div>
                      <dt className="text-xs font-medium text-nrg-muted">{HYBRID_COPY.structuredSqlRows}</dt>
                      <dd className="mt-1 text-sm font-semibold text-nrg-text">{formatRows(hybridEvidence.sqlRows)}</dd>
                    </div>
                    <div>
                      <dt className="text-xs font-medium text-nrg-muted">{HYBRID_COPY.documentExcerpts}</dt>
                      <dd className="mt-1 text-sm font-semibold text-nrg-text">{formatRows(hybridEvidence.documentChunks)}</dd>
                    </div>
                  </dl>
                  <p className="mt-2 text-xs font-medium text-nrg-muted">
                    {HYBRID_COPY.sourceSummary}
                  </p>
                </div>
              )}
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
