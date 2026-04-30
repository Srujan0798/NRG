import React, { useEffect, useMemo, useRef } from 'react'
import { Citation, QueryProvenance } from '../services/queryService'
import { useStreamingQuery, type StreamAnswerConfidence } from '../hooks/useStreamingQuery'
import PhaseHeader from './PhaseHeader/PhaseHeader'
import SqlBlock from './SqlBlock/SqlBlock'
import TokenStream from './TokenStream/TokenStream'
import VerifiedBadge from './VerifiedBadge/VerifiedBadge'
import AnswerTrustActions from './AnswerTrustActions/AnswerTrustActions'
import PromptBlocked from './PromptBlocked/PromptBlocked'
import { t } from '../i18n'

interface StreamingAnswerPanelProps {
  query: string
  onCitationClick?: (citation: Citation) => void
  onDrawerOpen?: (citation: Citation) => void
  onProofOpen?: (auditEventId: string) => void
  onProofChange?: (payload: StreamingProofPayload) => void
}

export interface StreamingProofPayload {
  response: string
  citations: Citation[]
  sqlQuery: string
  sqlResults: Array<Record<string, unknown>>
  rowsReturned: number
  auditEventId: string | null
  confidence: StreamAnswerConfidence
  provenance?: QueryProvenance
}

const formatNumber = (value: number) => new Intl.NumberFormat('en-IN').format(value)

const defaultPlan = ['Classify research intent', 'Retrieve matching evidence', 'Prepare verified answer']

const CONTEXT_COPY = {
  title: 'Answer context',
  sourceRows: 'Source rows',
  citations: 'Citations',
  synthesis: 'Synthesis',
  auditState: 'Audit state',
  localDatabase: 'Local database',
  cloudSynthesis: 'Cloud synthesis',
  hmacBound: 'HMAC-bound',
  pending: 'Pending',
}

const formatSynthesis = (provenance?: QueryProvenance) => {
  if (provenance?.cloud_synthesis_used) return CONTEXT_COPY.cloudSynthesis
  if (provenance?.synth) return provenance.synth.replace(/_/g, ' ')
  return CONTEXT_COPY.localDatabase
}

const AnswerContextGrid: React.FC<{
  rowsReturned: number
  citations: Citation[]
  auditEventId: string | null
  provenance?: QueryProvenance
}> = ({ rowsReturned, citations, auditEventId, provenance }) => {
  const items = [
    { label: CONTEXT_COPY.sourceRows, value: formatNumber(rowsReturned) },
    { label: CONTEXT_COPY.citations, value: formatNumber(citations.length) },
    { label: CONTEXT_COPY.synthesis, value: formatSynthesis(provenance) },
    { label: CONTEXT_COPY.auditState, value: auditEventId ? CONTEXT_COPY.hmacBound : CONTEXT_COPY.pending },
  ]

  return (
    <section
      data-testid="answer-context-grid"
      className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4"
      aria-label={CONTEXT_COPY.title}
    >
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-nrg-muted">
        {CONTEXT_COPY.title}
      </p>
      <dl className="grid gap-3 sm:grid-cols-4">
        {items.map((item) => (
          <div key={item.label} className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-3">
            <dt className="text-xs font-medium text-nrg-muted">{item.label}</dt>
            <dd className="mt-1 break-words text-sm font-semibold text-nrg-text">{item.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export const StreamingAnswerPanel: React.FC<StreamingAnswerPanelProps> = ({
  query,
  onCitationClick,
  onProofOpen,
  onProofChange,
}) => {
  const lastStartedQueryRef = useRef('')
  const pendingStartRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const {
    isStreaming,
    currentPhase,
    plan,
    sql,
    retrievedCount,
    fullText,
    citations,
    auditEventId,
    signatureBytes,
    provenance,
    answerConfidence,
    error,
    isVerified,
    startStream,
    abortStream,
  } = useStreamingQuery()

  useEffect(() => {
    const trimmedQuery = query.trim()
    if (!trimmedQuery || lastStartedQueryRef.current === trimmedQuery) return

    pendingStartRef.current = setTimeout(() => {
      lastStartedQueryRef.current = trimmedQuery
      pendingStartRef.current = null
      startStream(trimmedQuery)
    }, 0)

    return () => {
      if (pendingStartRef.current) {
        clearTimeout(pendingStartRef.current)
        pendingStartRef.current = null
      }
    }
  }, [query, startStream])

  useEffect(() => {
    if (!isVerified) return
    onProofChange?.({
      response: fullText,
      citations: citations.map((citation) => ({
        id: citation.id,
        pub_id: citation.pub_id,
        chunk_id: citation.chunk_id,
        title: citation.title || citation.pub_id,
        audit_event_id: citation.audit_event_id || auditEventId || undefined,
      })),
      sqlQuery: sql,
      sqlResults: [],
      rowsReturned: retrievedCount,
      auditEventId,
      confidence: answerConfidence,
      provenance,
    })
  }, [answerConfidence, auditEventId, citations, fullText, isVerified, onProofChange, provenance, retrievedCount, sql])

  const planSteps = useMemo(() => plan?.steps?.length ? plan.steps : defaultPlan, [plan])
  const hasStarted = Boolean(query.trim())

  if (!hasStarted) return null

  return (
    <section
      data-testid="streaming-answer-panel"
      className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-5 shadow-lg"
      aria-live="polite"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <PhaseHeader phase={currentPhase} isStreaming={isStreaming} />

        {(currentPhase?.phase === 'executing' || currentPhase?.phase === 'synthesizing') && isStreaming && (
          <button
            type="button"
            data-testid="stop-stream"
            onClick={abortStream}
            className="min-h-11 rounded-xl border border-nrg-border px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          >
            {t("auto.components.StreamingAnswerPanel.1")}</button>
        )}
      </div>

      {error ? (
        error.toLowerCase().includes('sensitive information') ? (
          <div className="mt-5">
            <PromptBlocked reason={`${error} Try a privacy-safe aggregate question instead.`} />
          </div>
        ) : (
          <div className="mt-5 rounded-lg border border-[var(--nrg-warning)] bg-[var(--nrg-warning-soft)] p-4 text-sm font-medium text-[var(--nrg-warning)]">
            {error}
          </div>
        )
      ) : (
        <div className="mt-6 space-y-5">
          <div data-testid="phase-planning" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)] p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-nrg-text">{t("auto.components.StreamingAnswerPanel.2")}</h2>
              {!plan && currentPhase?.phase === 'planning' && (
                <span className="text-xs font-semibold uppercase tracking-wider text-nrg-muted">{t("auto.components.StreamingAnswerPanel.3")}</span>
              )}
            </div>
            <ol className="space-y-2">
              {planSteps.map((step, index) => (
                <li key={step} className="flex items-center gap-3 text-sm text-nrg-text">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--nrg-surface-1)] text-xs font-bold text-[var(--nrg-focus)]">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {(currentPhase?.phase === 'executing' || currentPhase?.phase === 'synthesizing' || isVerified) && (
            <div data-testid="phase-executing" className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-nrg-text">{t("auto.components.StreamingAnswerPanel.4")}</h2>
                <p className="text-sm font-medium text-nrg-muted">
                  {t("auto.components.StreamingAnswerPanel.5")}<span className="font-semibold text-nrg-text">{formatNumber(retrievedCount)}</span>
                </p>
              </div>
              <SqlBlock sql={sql} />
            </div>
          )}

          {(currentPhase?.phase === 'synthesizing' || isVerified) && (
            <div data-testid="phase-synthesizing" className="space-y-3">
              <h2 className="text-sm font-semibold text-nrg-text">{t("auto.components.StreamingAnswerPanel.6")}</h2>
              <TokenStream text={fullText} isStreaming={isStreaming && currentPhase?.phase === 'synthesizing'} />

              {isVerified && (
                <AnswerContextGrid
                  rowsReturned={retrievedCount}
                  citations={citations.map((citation) => ({
                    id: citation.id,
                    pub_id: citation.pub_id,
                    chunk_id: citation.chunk_id,
                    title: citation.title || citation.pub_id,
                    audit_event_id: citation.audit_event_id || auditEventId || undefined,
                  }))}
                  auditEventId={auditEventId}
                  provenance={provenance}
                />
              )}

              {citations.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {citations.map((citation, index) => (
                    <button
                      key={citation.id}
                      type="button"
                      onClick={() => onCitationClick?.({
                        id: citation.id,
                        pub_id: citation.pub_id,
                        chunk_id: citation.chunk_id,
                        title: citation.title || citation.pub_id,
                        audit_event_id: citation.audit_event_id || auditEventId,
                      })}
                      className="rounded-full border border-nrg-border bg-[var(--nrg-surface-2)] px-3 py-1.5 text-xs font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
                    >
                      [{index + 1}] {citation.title || citation.pub_id}
                    </button>
                  ))}
                </div>
              )}

              <AnswerTrustActions
                answer={fullText}
                sqlQuery={sql}
                rowsReturned={retrievedCount}
                auditEventId={auditEventId}
                provenance={provenance}
              />
            </div>
          )}

          {isVerified && (
            <div data-testid="phase-verified" className="pt-1">
              <VerifiedBadge
                auditEventId={auditEventId}
                signatureBytes={signatureBytes}
                onOpenProof={auditEventId ? () => onProofOpen?.(auditEventId) : undefined}
              />
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default StreamingAnswerPanel
