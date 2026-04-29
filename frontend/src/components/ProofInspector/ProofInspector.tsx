import React, { useState } from 'react'
import type { PersonaRole } from '../../services/authService'

type ConfidenceLevel = 'high' | 'medium' | 'low'

export interface ProofCitation {
  id: string
  title?: string
  source?: string
}

interface ProofInspectorProps {
  role: PersonaRole
  confidence?: ConfidenceLevel
  citations?: ProofCitation[]
  sqlQuery?: string | null
  sqlResults?: Array<Record<string, unknown>>
  rowsReturned?: number | null
  auditEventId?: string | null
  freshness?: {
    database_snapshot?: string | null
    document_indexed_at?: string | null
    warning?: string | null
  }
  assumptions?: string[]
  caveats?: string[]
}

const PROOF_COPY = {
  title: 'Answer Proof',
  citations: 'Citations',
  citationsEmpty: 'Citations appear here when an answer is returned.',
  source: 'Source',
  audit: 'Audit',
  currentAuditId: 'Current audit event',
  rows: 'Rows',
  sqlUnavailable: 'Source SQL is unavailable for this response.',
  eventId: 'Event ID',
  auditUnavailable: 'Audit proof was not returned for this answer. Try again.',
  previousChainHash: 'Previous chain hash',
  inspectorLabel: 'Answer proof inspector',
  assumptions: 'Assumptions',
  caveats: 'Caveats',
  freshness: 'Freshness',
  databaseSnapshot: 'Database snapshot',
  documentIndexed: 'Document indexed',
}

const CONFIDENCE_COPY: Record<ConfidenceLevel, string> = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
}

const ROLE_NOTICE: Record<PersonaRole, string> = {
  researcher: 'Source rows can include identified records where policy allows.',
  government: 'Source evidence is aggregated and k-anonymized.',
  industry: 'Source evidence is anonymized for partnership discovery.',
}

const formatCell = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-'
  return String(value)
}

const containsRestrictedSqlField = (sql: string | null | undefined) => (
  /\b(email|phone|mobile|aadhaar|pan|contact|address)\b/i.test(sql || '')
)

const toCsv = (rows: Array<Record<string, unknown>>) => {
  if (!rows.length) return ''
  const headers = Object.keys(rows[0])
  const escape = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`
  return [headers.join(','), ...rows.map((row) => headers.map((header) => escape(row[header])).join(','))].join('\n')
}

const downloadCsv = (rows: Array<Record<string, unknown>>) => {
  if (typeof window === 'undefined' || typeof Blob === 'undefined') return
  const blob = new Blob([toCsv(rows)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'nrg-visible-source-rows.csv'
  anchor.click()
  URL.revokeObjectURL(url)
}

export function ProofInspector({
  role,
  confidence = 'medium',
  citations = [],
  sqlQuery,
  sqlResults = [],
  rowsReturned,
  auditEventId,
  freshness,
  assumptions = [],
  caveats = [],
}: ProofInspectorProps) {
  const [openPanel, setOpenPanel] = useState<'source' | 'audit'>('source')
  const sourceRows = sqlResults.slice(0, 25)
  const headers = sourceRows.length > 0 ? Object.keys(sourceRows[0]) : []
  const visibleSqlQuery = role === 'industry' && containsRestrictedSqlField(sqlQuery)
    ? PROOF_COPY.sqlUnavailable
    : sqlQuery

  return (
    <section
      data-testid="proof-inspector"
      className="rounded-lg border border-nrg-border bg-[var(--nrg-surface)] p-4"
      aria-label={PROOF_COPY.inspectorLabel}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-nrg-text">{PROOF_COPY.title}</h2>
          <p className="mt-1 text-xs text-nrg-muted">{ROLE_NOTICE[role]}</p>
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-700">
          {CONFIDENCE_COPY[confidence]}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {auditEventId && (
          <section className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">{PROOF_COPY.currentAuditId}</p>
            <p className="mt-1 break-all font-mono text-xs text-nrg-text">{auditEventId}</p>
          </section>
        )}

        {freshness && (freshness.database_snapshot || freshness.document_indexed_at || freshness.warning) && (
          <section className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2">
            <p className="text-xs font-semibold uppercase text-nrg-muted">{PROOF_COPY.freshness}</p>
            {freshness.database_snapshot && (
              <p className="mt-1 text-xs text-nrg-text">{PROOF_COPY.databaseSnapshot}: {freshness.database_snapshot}</p>
            )}
            {freshness.document_indexed_at && (
              <p className="mt-1 text-xs text-nrg-text">{PROOF_COPY.documentIndexed}: {freshness.document_indexed_at}</p>
            )}
            {freshness.warning && (
              <p className="mt-1 text-xs text-nrg-muted">{freshness.warning}</p>
            )}
          </section>
        )}

        {assumptions.length > 0 && (
          <section className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2">
            <p className="text-xs font-semibold uppercase text-nrg-muted">{PROOF_COPY.assumptions}</p>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-nrg-text">
              {assumptions.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        )}

        {caveats.length > 0 && (
          <section className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2">
            <p className="text-xs font-semibold uppercase text-nrg-muted">{PROOF_COPY.caveats}</p>
            <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-nrg-text">
              {caveats.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        )}

        <section>
          <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">{PROOF_COPY.citations}</h3>
          {citations.length > 0 ? (
            <ol className="mt-2 space-y-2">
              {citations.map((citation, index) => (
                <li key={citation.id} className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2 text-sm text-nrg-text">
                  <span className="font-mono text-xs text-nrg-muted">{`[${index + 1}]`}</span>
                  <span className="ml-2">{citation.title || citation.id}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-nrg-muted">{PROOF_COPY.citationsEmpty}</p>
          )}
        </section>

        <div className="flex gap-2">
          <button
            type="button"
            className="min-h-10 rounded-md border border-nrg-border px-3 text-sm font-semibold text-nrg-text"
            onClick={() => setOpenPanel('source')}
          >
            {PROOF_COPY.source}
          </button>
          <button
            type="button"
            className="min-h-10 rounded-md border border-nrg-border px-3 text-sm font-semibold text-nrg-text"
            onClick={() => setOpenPanel('audit')}
          >
            {PROOF_COPY.audit}
          </button>
        </div>

        {openPanel === 'source' && (
          <section data-testid="proof-source-data-panel" className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">
              {PROOF_COPY.rows} {rowsReturned ?? sourceRows.length}
            </p>
            {sourceRows.length > 0 && (
              <button
                type="button"
                className="mt-2 min-h-9 rounded-md border border-nrg-border px-3 text-xs font-semibold text-nrg-text"
                onClick={() => downloadCsv(sourceRows)}
              >
                Download visible rows
              </button>
            )}
            <pre className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap rounded-md bg-[var(--nrg-surface-2)] p-2 text-xs text-nrg-text">
              {visibleSqlQuery || PROOF_COPY.sqlUnavailable}
            </pre>
            {headers.length > 0 && (
              <div className="mt-3 overflow-x-auto">
                <table className="min-w-full text-left text-xs">
                  <thead>
                    <tr>
                      {headers.map((header) => (
                        <th key={header} className="border-b border-nrg-border px-2 py-1 font-semibold text-nrg-muted">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sourceRows.map((row, index) => (
                      <tr key={index}>
                        {headers.map((header) => (
                          <td key={header} className="border-b border-nrg-border px-2 py-1 text-nrg-text">
                            {formatCell(row[header])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {openPanel === 'audit' && (
          <section data-testid="audit-event-panel" className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-3 text-sm">
            <p className="font-semibold text-nrg-text">{PROOF_COPY.eventId}</p>
            <p className="mt-1 break-all font-mono text-xs text-nrg-muted">{auditEventId || PROOF_COPY.auditUnavailable}</p>
            <p className="mt-3 font-semibold text-nrg-text">{PROOF_COPY.previousChainHash}</p>
            <p className="mt-1 font-mono text-xs text-nrg-muted">{`prev-${String(auditEventId || 'pending').slice(0, 12)}`}</p>
          </section>
        )}
      </div>
    </section>
  )
}

export default ProofInspector
