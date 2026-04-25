import { useCallback, useEffect, useRef, useState } from 'react'
import { authService } from '../services/authService'
import { Citation, QueryRequest, queryService } from '../services/queryService'
import { useQueryStore } from '../stores/queryStore'
import { PlanDAG, StreamPhaseName, StreamQueryEvent } from '../types/api'
import { errorCopy } from '../i18n/en-IN'
import { emitTelemetry, trackQuerySubmitted } from '../lib/telemetry'

export interface StreamPhase {
  phase: StreamPhaseName
  label: string
  progress: number
}

export interface StreamCitation {
  id: string
  pub_id: string
  chunk_id: string
  title?: string
}

export interface StreamMeta {
  elapsed_ms: number
  synthesis_tier: string
  verification_status: boolean
  citations: StreamCitation[]
  provenance: Record<string, unknown>
  query_id: string
  audit_event_id?: string
  signature_bytes?: number
}

export interface EventSourceLike {
  addEventListener: EventSource['addEventListener']
  close: EventSource['close']
  onmessage: EventSource['onmessage']
  onerror: EventSource['onerror']
}

export interface UseStreamingQueryOptions {
  onPhaseChange?: (phase: StreamPhase) => void
  onCitation?: (citation: StreamCitation) => void
  onComplete?: (meta: StreamMeta, fullText: string) => void
  onError?: (error: string) => void
  eventSourceFactory?: (request: QueryRequest) => EventSourceLike
  silenceTimeoutMs?: number
}

const PHASES: Record<StreamPhaseName, StreamPhase> = {
  planning: { phase: 'planning', label: 'Planning evidence path', progress: 0.1 },
  planned: { phase: 'planned', label: 'Evidence plan ready', progress: 0.25 },
  executing: { phase: 'executing', label: 'Retrieving signed records', progress: 0.55 },
  synthesizing: { phase: 'synthesizing', label: 'Writing answer with citations', progress: 0.8 },
  verified: { phase: 'verified', label: 'Verified by HMAC chain', progress: 1 },
  error: { phase: 'error', label: 'Answer paused', progress: 0 },
}

const SILENCE_ERROR = 'This is taking longer than usual. Please try again.'
const CONNECTION_ERROR = errorCopy.generic

const toStreamCitation = (citation: Citation | StreamCitation): StreamCitation => ({
  id: citation.id,
  pub_id: citation.pub_id || ('source' in citation ? citation.source : undefined) || citation.id,
  chunk_id: citation.chunk_id || '0',
  title: citation.title,
})

type StreamEventPayload = Partial<StreamQueryEvent> & Record<string, any>

const parseEventData = (data: string): StreamEventPayload | string | null => {
  if (!data || data === '[DONE]') return null

  try {
    return JSON.parse(data) as StreamEventPayload
  } catch {
    return data
  }
}

const normalizeLegacyPhase = (phase: string): StreamPhaseName => {
  if (phase === 'intent_detection') return 'planning'
  if (phase === 'retrieval') return 'executing'
  if (phase === 'synthesis') return 'synthesizing'
  if (phase in PHASES) return phase as StreamPhaseName
  return 'planning'
}

export function useStreamingQuery(options: UseStreamingQueryOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<StreamPhase | null>(null)
  const [plan, setPlan] = useState<PlanDAG | null>(null)
  const [sql, setSql] = useState('')
  const [retrievedCount, setRetrievedCount] = useState(0)
  const [fullText, setFullText] = useState('')
  const [citations, setCitations] = useState<StreamCitation[]>([])
  const [auditEventId, setAuditEventId] = useState<string | null>(null)
  const [signatureBytes, setSignatureBytes] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isRecoverableError, setIsRecoverableError] = useState(false)

  const optionsRef = useRef(options)
  const eventSourceRef = useRef<EventSourceLike | null>(null)
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const fullTextRef = useRef('')
  const citationsRef = useRef<StreamCitation[]>([])
  const submitStartedAtRef = useRef<number | null>(null)
  const queryTelemetryIdRef = useRef<string | null>(null)
  const personaRef = useRef<string>('anonymous')
  const observedPhaseRef = useRef<Set<string>>(new Set())
  const currentPhaseRef = useRef<StreamPhaseName>('planning')

  useEffect(() => {
    optionsRef.current = options
  }, [options])

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current)
      silenceTimerRef.current = null
    }
  }, [])

  const closeSource = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  const setPhase = useCallback((phaseName: StreamPhaseName, override?: Partial<StreamPhase>) => {
    const nextPhase = { ...PHASES[phaseName], ...override }
    currentPhaseRef.current = phaseName
    setCurrentPhase(nextPhase)
    useQueryStore.getState().setStreaming({ phase: phaseName })
    if (
      submitStartedAtRef.current &&
      phaseName !== 'planning' &&
      phaseName !== 'verified' &&
      phaseName !== 'error' &&
      !observedPhaseRef.current.has(phaseName)
    ) {
      observedPhaseRef.current.add(phaseName)
      emitTelemetry('query.phase_observed', {
        phase: phaseName,
        ms_since_submit: Math.round(performance.now() - submitStartedAtRef.current),
        query_id: queryTelemetryIdRef.current,
      })
    }
    optionsRef.current.onPhaseChange?.(nextPhase)
  }, [])

  const failRecoverably = useCallback((message: string) => {
    closeSource()
    clearSilenceTimer()
    setIsStreaming(false)
    setIsRecoverableError(true)
    setError(message)
    useQueryStore.getState().setStreaming({ phase: 'error', error: message })
    setPhase('error')
    optionsRef.current.onError?.(message)
  }, [clearSilenceTimer, closeSource, setPhase])

  const resetSilenceTimer = useCallback(() => {
    clearSilenceTimer()
    const timeoutMs = optionsRef.current.silenceTimeoutMs ?? 25000
    silenceTimerRef.current = setTimeout(() => {
      failRecoverably(SILENCE_ERROR)
    }, timeoutMs)
  }, [clearSilenceTimer, failRecoverably])

  const addCitation = useCallback((citation: Citation | StreamCitation) => {
    const normalized = toStreamCitation(citation)
    setCitations((current) => {
      if (current.some((item) => item.id === normalized.id)) return current
      const next = [...current, normalized]
      citationsRef.current = next
      return next
    })
    optionsRef.current.onCitation?.(normalized)
  }, [])

  const appendToken = useCallback((token: string) => {
    if (!token) return
    setFullText((current) => {
      const next = current + token
      fullTextRef.current = next
      useQueryStore.getState().setStreaming({ answer: next })
      return next
    })
  }, [])

  const completeStream = useCallback((payload: Extract<StreamQueryEvent, { phase: 'verified' }>) => {
    closeSource()
    clearSilenceTimer()
    const verifiedCitations = payload.citations.map(toStreamCitation)
    citationsRef.current = verifiedCitations
    setCitations(verifiedCitations)
    setAuditEventId(payload.audit_event_id)
    setSignatureBytes(payload.signature_bytes ?? 26)
    if (submitStartedAtRef.current) {
      emitTelemetry('query.completed', {
        total_ms: Math.round(performance.now() - submitStartedAtRef.current),
        citation_count: verifiedCitations.length,
        persona: personaRef.current,
        query_id: queryTelemetryIdRef.current,
      })
    }
    useQueryStore.getState().setStreaming({
      phase: 'verified',
      answer: fullTextRef.current,
      auditEventId: payload.audit_event_id,
    })
    setError(null)
    setIsRecoverableError(false)
    setIsStreaming(false)
    setPhase('verified')
    optionsRef.current.onComplete?.({
      elapsed_ms: 0,
      synthesis_tier: 'stream',
      verification_status: true,
      citations: verifiedCitations,
      provenance: { verifier: 'hmac' },
      query_id: payload.audit_event_id,
      audit_event_id: payload.audit_event_id,
      signature_bytes: payload.signature_bytes ?? 26,
    }, fullTextRef.current)
  }, [clearSilenceTimer, closeSource, setPhase])

  const handleEvent = useCallback((eventType: string, data: string) => {
    const parsed = parseEventData(data)
    if (!parsed) return

    resetSilenceTimer()

    if (typeof parsed === 'string') {
      setPhase('synthesizing')
      appendToken(parsed)
      return
    }

    const phaseName = parsed.phase || eventType

    if (phaseName === 'heartbeat') return

    if (phaseName === 'planned') {
      setPlan(parsed.plan || { steps: ['Classify research intent', 'Retrieve matching evidence', 'Prepare verified answer'] })
      setPhase('planned')
      return
    }

    if (phaseName === 'executing') {
      setSql(parsed.sql || '')
      if (typeof parsed.retrieved_count === 'number') setRetrievedCount(parsed.retrieved_count)
      setPhase('executing')
      return
    }

    if (phaseName === 'synthesizing') {
      setPhase('synthesizing')
      appendToken(parsed.token || '')
      if (parsed.citation) addCitation(parsed.citation)
      return
    }

    if (phaseName === 'citation' && 'id' in parsed) {
      addCitation(parsed as Citation)
      return
    }

    if (phaseName === 'verified') {
      completeStream({
        phase: 'verified',
        citations: parsed.citations || [],
        audit_event_id: parsed.audit_event_id || `stream-${Date.now()}`,
        signature_bytes: parsed.signature_bytes,
      })
      return
    }

    if (phaseName === 'error') {
      failRecoverably(parsed.message || CONNECTION_ERROR)
      return
    }

    if (phaseName === 'done') {
      completeStream({
        phase: 'verified',
        citations: citationsRef.current,
        audit_event_id: `stream-${Date.now()}`,
        signature_bytes: 26,
      })
      return
    }

    if (typeof parsed.phase === 'string') {
      setPhase(normalizeLegacyPhase(parsed.phase), {
        label: parsed.label,
        progress: parsed.progress,
      })
    }
  }, [addCitation, appendToken, completeStream, failRecoverably, resetSilenceTimer, setPhase])

  const abortStream = useCallback(() => {
    if (eventSourceRef.current && submitStartedAtRef.current) {
      emitTelemetry('query.aborted', {
        ms_since_submit: Math.round(performance.now() - submitStartedAtRef.current),
        phase_at_abort: currentPhaseRef.current,
        query_id: queryTelemetryIdRef.current,
      })
    }
    closeSource()
    clearSilenceTimer()
    setIsStreaming(false)
  }, [clearSilenceTimer, closeSource])

  const startStream = useCallback((query: string) => {
    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      failRecoverably('Ask a question before starting the answer.')
      return
    }

    abortStream()
    fullTextRef.current = ''
    citationsRef.current = []
    observedPhaseRef.current = new Set()
    setIsStreaming(true)
    setPlan(null)
    setSql('')
    setRetrievedCount(0)
    setFullText('')
    setCitations([])
    setAuditEventId(null)
    setSignatureBytes(null)
    setError(null)
    setIsRecoverableError(false)
    useQueryStore.getState().setStreaming({
      phase: 'planning',
      answer: '',
      auditEventId: undefined,
      error: undefined,
    })
    setPhase('planning')

    const session = authService.getStoredSession()
    const sessionId = session?.user?.id || 'anonymous'
    personaRef.current = session?.user?.role || 'anonymous'
    const request: QueryRequest = {
      query: trimmedQuery,
      sessionId,
    }
    submitStartedAtRef.current = performance.now()
    queryTelemetryIdRef.current = trackQuerySubmitted(trimmedQuery, personaRef.current as any, { sessionId }).event_id

    const eventSource = optionsRef.current.eventSourceFactory
      ? optionsRef.current.eventSourceFactory(request)
      : queryService.streamQuery(request)

    eventSourceRef.current = eventSource
    resetSilenceTimer()

    const addTypedListener = (type: string) => {
      eventSource.addEventListener(type, ((event: MessageEvent<string>) => {
        handleEvent(type, event.data)
      }) as EventListener)
    }

    for (const eventType of ['planned', 'executing', 'synthesizing', 'verified', 'heartbeat', 'citation', 'phase', 'meta', 'done', 'error']) {
      addTypedListener(eventType)
    }

    eventSource.onmessage = (event) => {
      handleEvent('message', event.data)
    }

    eventSource.onerror = () => {
      failRecoverably(CONNECTION_ERROR)
    }
  }, [abortStream, failRecoverably, handleEvent, resetSilenceTimer, setPhase])

  useEffect(() => () => {
    closeSource()
    clearSilenceTimer()
  }, [clearSilenceTimer, closeSource])

  return {
    isStreaming,
    currentPhase,
    plan,
    sql,
    retrievedCount,
    fullText,
    citations,
    auditEventId,
    signatureBytes,
    error,
    isRecoverableError,
    isVerified: currentPhase?.phase === 'verified',
    startStream,
    abortStream,
  }
}
