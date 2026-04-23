import React, { useState, useCallback } from 'react'
import { Citation, GraphNode, QueryProvenance, QueryWarning } from '../services/queryService'
import { toStringArray } from '../types/api'
import { IntelligenceBrief } from './IntelligenceBrief'
import { CitationDrawer } from './CitationDrawer'

interface AnswerPanelProps {
  response: string
  citations: Citation[]
  provenance?: QueryProvenance
  warnings?: QueryWarning[]
  verification_status?: boolean
  onNodeClick?: (node: GraphNode) => void
  isStreaming?: boolean
  responseId?: string
  queryText?: string
  sessionId?: string
}

export const AnswerPanel: React.FC<AnswerPanelProps> = ({
  response,
  citations,
  provenance,
  warnings,
  verification_status,
  onNodeClick,
  isStreaming = false,
  responseId,
  queryText,
  sessionId,
}) => {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleCitationClick = useCallback((citation: Citation) => {
    setSelectedCitation(citation)
    setDrawerOpen(true)
  }, [])

  const handleExportPDF = useCallback(() => {
    const summary = response.split('\n')[0]?.substring(0, 300) + '...'
    
    const content = `<!DOCTYPE html>
<html>
<head>
  <title>NRG Intelligence Brief</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; background: #fff; }
    .header { display: flex; align-items: center; gap: 16px; padding-bottom: 20px; border-bottom: 3px solid #ff6b35; margin-bottom: 30px; }
    .logo-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #ff6b35, #ff8b4a); border-radius: 12px; display: flex; align-items: center; justify-content: center; }
    .logo-icon span { color: white; font-size: 24px; font-weight: bold; }
    .logo-text { font-size: 24px; font-weight: bold; color: #ff6b35; }
    .subtitle { font-size: 12px; color: #6b7280; margin-top: 4px; }
    .section { margin-bottom: 24px; }
    .section-title { font-size: 14px; font-weight: bold; color: #1f2937; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
    .summary { font-size: 14px; line-height: 1.7; color: #374151; padding-left: 16px; border-left: 3px solid #ff6b35; }
    .content { font-size: 13px; line-height: 1.7; color: #374151; white-space: pre-wrap; }
    .citations { font-size: 12px; color: #6b7280; }
    .citation-item { padding: 12px; background: #f9fafb; border-radius: 8px; margin-bottom: 8px; }
    .citation-title { font-weight: 500; color: #1f2937; }
    .citation-meta { font-size: 11px; color: #9ca3af; margin-top: 4px; }
    .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; text-align: center; }
    @media print { body { padding: 20px; } .header { border-bottom-color: #ff6b35; } }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo-icon"><span>र</span></div>
    <div>
      <div class="logo-text">राष्ट्रीय गवेषण मंच</div>
      <div class="subtitle">National Research Graph — Intelligence Brief</div>
    </div>
  </div>
  <div class="section">
    <div class="section-title">📋 Summary</div>
    <div class="summary">${summary}</div>
  </div>
  <div class="section">
    <div class="section-title">📊 Analysis</div>
    <div class="content">${response}</div>
  </div>
  ${citations.length > 0 ? `
  <div class="section">
    <div class="section-title">📚 References</div>
    <div class="citations">
      ${citations.map((c, i) => `
        <div class="citation-item">
          <div class="citation-title">[${i + 1}] ${c.title || 'Unknown Publication'}</div>
          <div class="citation-meta">
            ${toStringArray(c.authors)?.slice(0, 3).join(', ')}${toStringArray(c.authors)?.length ?? 0 > 3 ? ' et al.' : ''}
            ${c.year ? ` (${c.year})` : ''}
          </div>
        </div>
      `).join('')}
    </div>
  </div>` : ''}
  <div class="footer">
    Generated: ${new Date().toLocaleString()} | NRG Platform — Sovereign Research Intelligence
  </div>
</body>
</html>`

    const blob = new Blob([content], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = window.document.createElement('a')
    a.href = url
    a.download = `NRG-Intelligence-Brief-${Date.now()}.html`
    a.click()
    URL.revokeObjectURL(url)
  }, [response, citations])

  return (
    <div className="space-y-4">
      <IntelligenceBrief
        response={response}
        citations={citations}
        provenance={provenance}
        warnings={warnings}
        verification_status={verification_status}
        onNodeClick={onNodeClick}
        onExportPDF={handleExportPDF}
        isStreaming={isStreaming}
        responseId={responseId}
        queryText={queryText}
        sessionId={sessionId}
      />

      <CitationDrawer
        citation={selectedCitation}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  )
}

export default AnswerPanel