import React, { useState, useCallback, useMemo } from 'react'
import { Citation, GraphNode, QueryProvenance, QueryWarning } from '../../services/queryService'
import { parseCitations } from '../../utils/parseCitations'
import { ConfidenceIndicator } from './components/ConfidenceIndicator'
import { ProvenanceBadge } from './components/ProvenanceBadge'
import { CitationChip, CitationList } from './components/CitationRenderer'
import { SourceBreakdown } from './components/SourceBreakdown'
import { ResponseRenderer } from './components/ResponseRenderer'
import { ResponseHistorySidebar } from './components/ResponseHistorySidebar'
import { ExportButton } from './components/ExportButton'
import { StreamIndicator } from './components/StreamIndicator'

export interface IntelligenceBriefProps {
  response: string
  citations: Citation[]
  provenance?: QueryProvenance
  warnings?: QueryWarning[]
  verification_status?: boolean
  onNodeClick?: (node: GraphNode) => void
  onExportPDF?: () => void
  isStreaming?: boolean
  responseId?: string
  queryText?: string
  sessionId?: string
}

interface HistoryItem {
  id: string
  timestamp: Date
  query: string
  response: string
  status: 'success' | 'error' | 'streaming'
}

export const IntelligenceBrief: React.FC<IntelligenceBriefProps> = ({
  response,
  citations,
  provenance,
  warnings,
  verification_status,
  onExportPDF,
  isStreaming = false,
  responseId,
  queryText,
  sessionId,
}) => {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [pinnedQueries, setPinnedQueries] = useState<Set<string>>(new Set())

  const handleCitationClick = useCallback((citation: Citation) => {
    setSelectedCitation(citation)
    setDrawerOpen(true)
  }, [])

  const parsedResult = useMemo(() => parseCitations(response, citations), [response, citations])
  const { segments, orderedCitations } = parsedResult

  const confidenceScore = useMemo(() => {
    if (!provenance?.verifier) return 0.5
    const match = provenance.verifier.match(/faithfulness[:\s]*([\d.]+)/i)
    return match ? parseFloat(match[1]) : 0.75
  }, [provenance])

  const summary = useMemo(() => {
    const lines = response.split('\n').filter(l => l.trim())
    const firstPara = lines[0] || ''
    const sentences = firstPara.split(/[.!?]+/).filter(s => s.trim())
    if (sentences.length >= 2) {
      return sentences.slice(0, 3).join('.') + '.'
    }
    return firstPara.length < 300 ? firstPara : firstPara.substring(0, 300) + '...'
  }, [response])

  const keyFindings = useMemo(() => {
    const findings: string[] = []
    const lines = response.split('\n')
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
        findings.push(trimmed.replace(/^[•\-*]\s*/, ''))
      }
      if (findings.length >= 5) break
    }
    return findings
  }, [response])

  const handleAddToHistory = useCallback((item: Omit<HistoryItem, 'id'>) => {
    const newItem = { ...item, id: `query-${Date.now()}` }
    setHistory(prev => [newItem, ...prev].slice(0, 50))
  }, [])

  const handleTogglePin = useCallback((id: string) => {
    setPinnedQueries(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  return (
    <div className="flex gap-4 h-full">
      <div className="flex-1 space-y-4 overflow-y-auto">
        <div className="nrg-glass overflow-hidden">
          <div className="border-b border-nrg-border bg-gradient-to-r from-saffron-50/50 to-nrg-navy-50/50">
            <div className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-saffron-400 to-saffron-600 flex items-center justify-center shadow-lg">
                  <span className="text-white text-lg">र</span>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-nrg-text">Intelligence Brief</h2>
                  <p className="text-xs text-nrg-muted">National Research Graph</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {isStreaming && <StreamIndicator />}
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border border-nrg-border text-nrg-muted hover:text-nrg-text hover:bg-nrg-navy-50 transition-all"
                >
                  {showHistory ? 'Hide History' : 'Show History'}
                </button>
                <ExportButton onExport={onExportPDF} />
              </div>
            </div>
          </div>

          <div className="p-6 space-y-6">
            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-saffron-500">📋</span>
                <h3 className="text-sm font-semibold text-nrg-text uppercase tracking-wider">Summary</h3>
              </div>
              <p className="text-sm text-nrg-text leading-relaxed pl-6 border-l-2 border-saffron-300">
                {summary}
              </p>
            </section>

            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-saffron-500">🔍</span>
                <h3 className="text-sm font-semibold text-nrg-text uppercase tracking-wider">Evidence</h3>
              </div>
              <div className="pl-6 space-y-4">
                {keyFindings.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-nrg-muted mb-2">Key Findings</h4>
                    <ul className="space-y-1.5">
                      {keyFindings.map((finding, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-nrg-text">
                          <span className="text-saffron-500 mt-0.5">•</span>
                          <span>{finding}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <ResponseRenderer
                  response={response}
                  citations={citations}
                  segments={segments}
                  onCitationClick={handleCitationClick}
                />
              </div>
            </section>

            {orderedCitations.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-saffron-500">📚</span>
                  <h3 className="text-sm font-semibold text-nrg-text uppercase tracking-wider">Citations</h3>
                </div>
                <CitationList
                  citations={orderedCitations}
                  onCitationClick={handleCitationClick}
                />
              </section>
            )}

            <section>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-saffron-500">🎯</span>
                <h3 className="text-sm font-semibold text-nrg-text uppercase tracking-wider">Confidence</h3>
              </div>
              <div className="pl-6">
                <ConfidenceIndicator
                  score={confidenceScore}
                  status={verification_status}
                  provenance={provenance}
                />
              </div>
            </section>
          </div>

          {warnings && warnings.length > 0 && (
            <div className="mx-6 mb-6 p-4 rounded-xl border border-amber-200 bg-amber-50">
              <h4 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-2">
                <span>⚠️</span> Notes
              </h4>
              <ul className="text-sm text-amber-700 space-y-1">
                {warnings.map((warning, index) => (
                  <li key={index} className="flex items-start gap-2">
                    {warning.skill && <span className="font-medium shrink-0">[{warning.skill}]</span>}
                    <span>{warning.message || warning.error_type || 'Warning'}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {showHistory && (
        <ResponseHistorySidebar
          history={history}
          pinnedQueries={pinnedQueries}
          onTogglePin={handleTogglePin}
          onSelectQuery={(item) => {
          }}
          onRerunQuery={(item) => {
          }}
        />
      )}
    </div>
  )
}

export default IntelligenceBrief