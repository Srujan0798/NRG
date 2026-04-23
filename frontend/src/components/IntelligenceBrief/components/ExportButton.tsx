import React, { useCallback } from 'react'
import { Citation } from '../../../services/queryService'
import { toStringArray } from '../../../types/api'

interface ExportButtonProps {
  onExport?: () => void
  response?: string
  citations?: Citation[]
  summary?: string
}

export const ExportButton: React.FC<ExportButtonProps> = ({ 
  onExport,
  response = '',
  citations = [],
  summary = ''
}) => {
  const handleExport = useCallback(async () => {
    if (onExport) {
      onExport()
      return
    }

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
    @media print {
      body { padding: 20px; }
      .header { border-bottom-color: #ff6b35; }
    }
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
    <div class="summary">${summary || 'Analysis summary not available.'}</div>
  </div>
  
  <div class="section">
    <div class="section-title">📊 Analysis</div>
    <div class="content">${response || 'No response data available.'}</div>
  </div>
  
  ${citations.length > 0 ? `
  <div class="section">
    <div class="section-title">📚 References</div>
    <div class="citations">
      ${citations.map((c, i) => `
        <div class="citation-item">
          <div class="citation-title">[${i + 1}] ${c.title || 'Unknown Publication'}</div>
          <div class="citation-meta">
            ${toStringArray(c.authors)?.slice(0, 3).join(', ')}${(toStringArray(c.authors)?.length ?? 0) > 3 ? ' et al.' : ''}
            ${c.year ? ` (${c.year})` : ''}
          </div>
        </div>
      `).join('')}
    </div>
  </div>
  ` : ''}
  
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
  }, [onExport, response, citations, summary])

  return (
    <button
      onClick={handleExport}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium 
        bg-gradient-to-r from-saffron-500 to-saffron-600 text-white border border-saffron-400
        hover:from-saffron-600 hover:to-saffron-700 shadow-sm transition-all duration-200"
    >
      <span>📥</span> Export PDF
    </button>
  )
}

export default ExportButton