import { useState, useCallback, useRef } from 'react'
import { authService } from '../services/authService'

export interface StreamPhase {
  phase: string
  label: string
  progress: number
}

export interface StreamCitation {
  id: string
  pub_id: string
  chunk_id: string
}

export interface StreamMeta {
  elapsed_ms: number
  synthesis_tier: string
  verification_status: boolean
  citations: StreamCitation[]
  provenance: Record<string, unknown>
  query_id: string
}

export interface UseStreamingQueryOptions {
  onPhaseChange?: (phase: StreamPhase) => void
  onCitation?: (citation: StreamCitation) => void
  onComplete?: (meta: StreamMeta, fullText: string) => void
  onError?: (error: string) => void
}

export function useStreamingQuery(options: UseStreamingQueryOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<StreamPhase | null>(null)
  const [fullText, setFullText] = useState('')
  const [citations, setCitations] = useState<StreamCitation[]>([])
  const [error, setError] = useState<string | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const startStream = useCallback((query: string) => {
    const session = authService.getStoredSession()
    if (!session) {
      options.onError?.('Not authenticated')
      return
    }

    abortStream()
    setIsStreaming(true)
    setFullText('')
    setCitations([])
    setError(null)
    setCurrentPhase(null)

    const url = `/api/query/stream?query=${encodeURIComponent(query)}&session_id=${session.user.id || 'anonymous'}`
    const eventSource = new EventSource(url, {
      // EventSource doesn't support custom headers; token goes in cookie or URL for SSE
    } as EventSourceInit)

    eventSourceRef.current = eventSource

    eventSource.addEventListener('phase', (e) => {
      try {
        const phase = JSON.parse(e.data) as StreamPhase
        setCurrentPhase(phase)
        options.onPhaseChange?.(phase)
      } catch { /* ignore parse error */ }
    })

    eventSource.addEventListener('citation', (e) => {
      try {
        const citation = JSON.parse(e.data) as StreamCitation
        setCitations(prev => {
          if (prev.some(c => c.id === citation.id)) return prev
          return [...prev, citation]
        })
        options.onCitation?.(citation)
      } catch { /* ignore parse error */ }
    })

    eventSource.onmessage = (e) => {
      if (e.data) {
        setFullText(prev => prev + e.data)
      }
    }

    eventSource.addEventListener('meta', (e) => {
      try {
        const meta = JSON.parse(e.data) as StreamMeta
        options.onComplete?.(meta, fullText)
      } catch { /* ignore parse error */ }
    })

    eventSource.addEventListener('done', () => {
      abortStream()
      const meta: StreamMeta = {
        elapsed_ms: 0,
        synthesis_tier: currentPhase?.phase || 'unknown',
        verification_status: false,
        citations,
        provenance: {},
        query_id: '',
      }
      options.onComplete?.(meta, fullText)
    })

    eventSource.addEventListener('error', () => {
      const errMsg = 'Stream connection failed'
      setError(errMsg)
      options.onError?.(errMsg)
      abortStream()
    })

    eventSource.onerror = () => {
      abortStream()
    }
  }, [options, fullText, citations, currentPhase])

  const abortStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsStreaming(false)
  }, [])

  return {
    isStreaming,
    currentPhase,
    fullText,
    citations,
    error,
    startStream,
    abortStream,
  }
}