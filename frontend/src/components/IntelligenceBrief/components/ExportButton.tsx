import React, { useCallback } from 'react'
import { Citation } from '../../../services/queryService'
import { toStringArray } from '../../../types/api'
import { printDesignTokenCss } from '../../../design-system/theme'
import { t } from '../../../i18n'

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
    ${printDesignTokenCss}
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: var(--nrg-font-sans); padding: var(--nrg-space-10); max-width: var(--nrg-export-width); margin: 0 auto; background: var(--nrg-white); }
    .header { display: flex; align-items: center; gap: var(--nrg-space-4); padding-bottom: var(--nrg-space-5); border-bottom: var(--nrg-space-three-quarter) solid var(--nrg-chart-1); margin-bottom: var(--nrg-space-7); }
    .logo-icon { width: var(--nrg-space-12); height: var(--nrg-space-12); background: linear-gradient(135deg, var(--nrg-chart-1), var(--nrg-saffron-soft)); border-radius: var(--nrg-space-3); display: flex; align-items: center; justify-content: center; }
    .logo-icon span { color: white; font-size: var(--nrg-type-body-line); font-weight: bold; }
    .logo-text { font-size: var(--nrg-type-body-line); font-weight: bold; color: var(--nrg-chart-1); }
    .subtitle { font-size: var(--nrg-type-caption-size); color: var(--nrg-ink-muted); margin-top: var(--nrg-space-1); }
    .section { margin-bottom: var(--nrg-space-6); }
    .section-title { font-size: var(--nrg-type-body-s-size); font-weight: bold; color: var(--nrg-ink); margin-bottom: var(--nrg-space-3); text-transform: uppercase; letter-spacing: 0.05em; }
    .summary { font-size: var(--nrg-type-body-s-size); line-height: 1.7; color: var(--nrg-ink-muted); padding-left: var(--nrg-space-4); border-left: var(--nrg-space-three-quarter) solid var(--nrg-chart-1); }
    .content { font-size: var(--nrg-type-export-body); line-height: 1.7; color: var(--nrg-ink-muted); white-space: pre-wrap; }
    .citations { font-size: var(--nrg-type-caption-size); color: var(--nrg-ink-muted); }
    .citation-item { padding: var(--nrg-space-3); background: var(--nrg-surface-2); border-radius: var(--nrg-space-2); margin-bottom: var(--nrg-space-2); }
    .citation-title { font-weight: 500; color: var(--nrg-ink); }
    .citation-meta { font-size: var(--nrg-type-caption-tight); color: var(--nrg-ink-muted); margin-top: var(--nrg-space-1); }
    .footer { margin-top: var(--nrg-space-10); padding-top: var(--nrg-space-4); border-top: var(--nrg-space-0) solid var(--nrg-border); font-size: var(--nrg-type-caption-tight); color: var(--nrg-ink-muted); text-align: center; }
    @media print {
      body { padding: var(--nrg-space-5); }
      .header { border-bottom-color: var(--nrg-chart-1); }
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
          <div class="citation-title">[${i + 1}] ${c.title || 'Publication title unavailable'}</div>
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
      <span>📥</span> {t("auto.components.IntelligenceBrief.components.ExportButton.1")}</button>
  )
}

export default ExportButton
