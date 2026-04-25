import React, { useState, useEffect } from 'react'
import { Citation } from '../services/queryService'
import { useStreamingQuery, StreamPhase, StreamCitation } from '../hooks/useStreamingQuery'
import { AnswerPanel } from './AnswerPanel'

interface StreamingAnswerPanelProps {
  query: string
  onCitationClick?: (citation: Citation) => void
  onDrawerOpen?: (citation: Citation) => void
}

const PHASES: { phase: string; label: string; icon: string }[] = [
  { phase: 'intent_detection', label: 'Analysing query', icon: '🎯' },
  { phase: 'retrieval', label: 'Fetching evidence', icon: '📚' },
  { phase: 'synthesis', label: 'Generating response', icon: '⚙️' },
]

function PhaseProgress({ currentPhase }: { currentPhase: StreamPhase | null }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
        <div className="w-8 h-8 rounded-full bg-saffron-100 dark:bg-saffron-900/30 flex items-center justify-center">
          {currentPhase ? (
            <span className="text-saffron-600 animate-pulse">⚙️</span>
          ) : (
            <span className="text-slate-400">⋯</span>
          )}
        </div>
        <span className="font-medium">{currentPhase?.label || 'Starting...'}</span>
      </div>
      <div className="flex gap-1.5 ml-10">
        {PHASES.map((p, i) => {
          const progress = currentPhase?.progress ?? 0
          const phaseIdx = PHASES.findIndex(ph => ph.phase === currentPhase?.phase)
          const isComplete = phaseIdx > i || (phaseIdx === i && progress >= 1)
          const isActive = phaseIdx === i
          return (
            <div
              key={p.phase}
              className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                isComplete
                  ? 'bg-saffron-500'
                  : isActive
                  ? 'bg-saffron-300 animate-pulse'
                  : 'bg-slate-200 dark:bg-navy-700'
              }`}
            />
          )
        })}
      </div>
    </div>
  )
}

function StreamingText({ text }: { text: string }) {
  return (
    <div className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap font-mono">
      {text}
      <span className="inline-block w-2 h-4 bg-saffron-500 ml-1 animate-pulse align-middle" />
    </div>
  )
}

function StreamingCitationChips({
  citations,
  onCitationClick,
}: {
  citations: StreamCitation[]
  onCitationClick?: (c: StreamCitation) => void
}) {
  if (citations.length === 0) return null
  return (
    <div className="flex flex-wrap gap-2">
      {citations.map((c, i) => (
        <button
          key={c.id}
          onClick={() => onCitationClick?.(c)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
            bg-saffron-50 dark:bg-saffron-900/30 text-saffron-700 dark:text-saffron-300
            border border-saffron-200 dark:border-saffron-700
            hover:bg-saffron-100 dark:hover:bg-saffron-900/50 transition-all cursor-pointer"
        >
          <span className="font-bold">[{i + 1}]</span>
          <span className="max-w-[100px] truncate">{c.pub_id}</span>
        </button>
      ))}
    </div>
  )
}

export const StreamingAnswerPanel: React.FC<StreamingAnswerPanelProps> = ({
  query,
  onCitationClick,
}) => {
  const [_pendingCitation, setPendingCitation] = useState<Citation | null>(null)
  const [finalText, setFinalText] = useState('')
  const [finalCitations, setFinalCitations] = useState<Citation[]>([])
  const [isDone, setIsDone] = useState(false)

  const { isStreaming, currentPhase, fullText, citations, error, startStream } =
    useStreamingQuery({
      onCitation: (c) => {
        const cite: Citation = {
          id: c.id,
          pub_id: c.pub_id,
          chunk_id: c.chunk_id,
          title: c.pub_id,
        }
        setPendingCitation(cite)
        onCitationClick?.(cite)
      },
      onComplete: (meta, text) => {
        setFinalText(text)
        setFinalCitations(
          meta.citations.map((c) => ({
            id: c.id,
            pub_id: c.pub_id,
            chunk_id: c.chunk_id,
            title: c.pub_id,
          }))
        )
        setIsDone(true)
      },
      onError: () => {},
    })

  useEffect(() => {
    if (query.trim()) {
      startStream(query)
    }
  }, [query, startStream])

  if (error) {
    return (
      <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-sm text-red-700">
        Stream failed: {error}
      </div>
    )
  }

  if (isDone && finalText) {
    return (
      <AnswerPanel
        response={finalText}
        citations={finalCitations}
        provenance={{ synth: currentPhase?.phase || 'stream' }}
        warnings={[]}
        verification_status={false}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-navy-800 rounded-2xl border border-slate-200 dark:border-navy-700 shadow-md p-5">
        <PhaseProgress currentPhase={currentPhase} />

        <div className="mt-4 min-h-[80px]">
          {isStreaming && <StreamingText text={fullText} />}
          {!isStreaming && !currentPhase && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <div className="w-5 h-5 rounded-full border-2 border-saffron-200 border-t-saffron-500 animate-spin" />
              Connecting...
            </div>
          )}
        </div>

        <div className="mt-3">
          <StreamingCitationChips
            citations={citations}
            onCitationClick={(c) => {
              const cite: Citation = { id: c.id, pub_id: c.pub_id, chunk_id: c.chunk_id, title: c.pub_id }
              onCitationClick?.(cite)
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default StreamingAnswerPanel
