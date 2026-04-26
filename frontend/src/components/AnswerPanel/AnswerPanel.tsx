import React, { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CitationDrawer } from '../CitationDrawer/CitationDrawer'
import { Citation, GraphNode, QueryProvenance, QueryWarning } from '../../services/queryService'
import { parseCitations } from '../../utils/parseCitations'
import { toStringArray } from '../../types/api'
import { CheckCircle, AlertCircle, Cloud, Database, GitMerge, ChevronDown, Download, ClipboardList, BarChart3, BookOpen } from 'lucide-react'
import { printDesignTokenCss } from '../../design-system/theme'
import { t } from '../../i18n'
import AnswerTrustActions from '../AnswerTrustActions/AnswerTrustActions'

interface AnswerPanelProps {
  response: string
  citations: Citation[]
  provenance?: QueryProvenance
  warnings?: QueryWarning[]
  verification_status?: boolean
  answer_confidence?: 'high' | 'partial' | 'low_clarify'
  sqlQuery?: string | null
  sqlResults?: Array<Record<string, unknown>>
  rowsReturned?: number | null
  auditEventId?: string | null
  onNodeClick?: (node: GraphNode) => void
}

type ResponseType = 'tabular' | 'geographic' | 'statistical' | 'comparison' | 'text'

const SourceIcon: React.FC<{ source?: string }> = ({ source }) => {
  if (source === 'SQL') return <Database size={14} className="text-blue-500" />
  if (source === 'RAG') return <GitMerge size={14} className="text-purple-500" />
  return <GitMerge size={14} className="text-saffron-500" />
}

const ConfidenceMeter: React.FC<{
  status: boolean | undefined
  answerConfidence?: 'high' | 'partial' | 'low_clarify'
}> = ({ status, answerConfidence }) => {
  const resolved = answerConfidence || (status === true ? 'high' : 'partial')
  const isVerified = resolved === 'high'
  const bars = resolved === 'high' ? 3 : resolved === 'partial' ? 2 : 1
  const label = resolved === 'high'
    ? 'High Confidence'
    : resolved === 'partial'
      ? 'Partial Confidence'
      : 'Needs Clarification'

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--glass-bg)] border border-nrg-border">
      <div className="flex gap-0.5">
        {[1, 2, 3].map((level) => (
          <motion.div
            key={level}
            className={`w-1.5 h-5 rounded-sm ${
              level <= bars
                ? isVerified ? 'bg-green-500' : 'bg-amber-400'
                : 'bg-slate-300 dark:bg-navy-600'
            }`}
            initial={{ scaleY: 0 }}
            animate={{ scaleY: 1 }}
            transition={{ delay: level * 0.1, duration: 0.3 }}
            style={{ transformOrigin: 'bottom' }}
          />
        ))}
      </div>
      <span className={`text-xs font-medium ${isVerified ? 'text-green-700 dark:text-green-400' : 'text-amber-700 dark:text-amber-400'}`}>
        {label}
      </span>
    </div>
  )
}

const ProvenanceBadge: React.FC<{ provenance?: QueryProvenance }> = ({ provenance }) => {
  if (!provenance) return null

  return (
    <div className="flex flex-wrap gap-2">
      {provenance.planner && (
        <motion.span
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-navy-50 dark:bg-navy-700/50 text-navy-700 dark:text-navy-300 border border-navy-100 dark:border-navy-600"
        >
          {provenance.planner} {t("auto.components.AnswerPanel.AnswerPanel.1")}</motion.span>
      )}
      <motion.span
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
          provenance.cloud_synthesis_used
            ? 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-700'
            : 'bg-navy-50 dark:bg-navy-700/50 text-navy-700 dark:text-navy-300 border-navy-100 dark:border-navy-600'
        }`}
      >
        {provenance.cloud_synthesis_used ? <Cloud size={12} /> : <Database size={12} />}
        {provenance.cloud_synthesis_used ? 'Cloud Synthesis' : 'Local Model'}
      </motion.span>
      {provenance.synth && (
        <motion.span
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-700"
        >
          <CheckCircle size={12} />
          {provenance.synth}
        </motion.span>
      )}
    </div>
  )
}

const downloadTextFile = (filename: string, content: string, type: string) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const anchor = window.document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

const csvEscape = (value: string) => `"${String(value ?? '').replace(/"/g, '""')}"`

const TabularView: React.FC<{
  headers: string[]
  rows: string[][]
  testId?: string
}> = ({ headers, rows, testId }) => {
  const [sortIndex, setSortIndex] = useState(0)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const sortedRows = useMemo(() => {
    return [...rows].sort((a, b) => {
      const left = a[sortIndex] ?? ''
      const right = b[sortIndex] ?? ''
      const comparison = left.localeCompare(right, 'en-IN', { numeric: true, sensitivity: 'base' })
      return sortDir === 'asc' ? comparison : -comparison
    })
  }, [rows, sortDir, sortIndex])

  const exportCsv = () => {
    const csv = [
      headers.map(csvEscape).join(','),
      ...sortedRows.map((row) => headers.map((_, index) => csvEscape(row[index] ?? '')).join(',')),
    ].join('\n')
    downloadTextFile(`NRG-table-${Date.now()}.csv`, csv, 'text/csv;charset=utf-8')
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-nrg-border bg-[var(--glass-bg)] px-4 py-8 text-center">
        <p className="text-sm font-medium text-nrg-text">{t("auto.components.AnswerPanel.AnswerPanel.7")}</p>
        <p className="mt-1 text-xs text-nrg-muted">{t("auto.components.AnswerPanel.AnswerPanel.8")}</p>
      </div>
    )
  }

  return (
    <div className="max-w-full overflow-hidden rounded-xl border border-nrg-border" data-testid={testId}>
      <div className="flex items-center justify-between gap-3 border-b border-nrg-border bg-[var(--glass-bg)] px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">
          {rows.length.toLocaleString('en-IN')} {t("auto.components.AnswerPanel.AnswerPanel.9")}
        </p>
        <button
          type="button"
          onClick={exportCsv}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 py-1.5 text-xs font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          aria-label={t("auto.components.AnswerPanel.AnswerPanel.10")}
        >
          <Download size={14} aria-hidden="true" />
          CSV
        </button>
      </div>
      <div className="w-full max-w-full overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-[var(--glass-bg)]">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={header}
                  className="border-b border-nrg-border px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-nrg-muted"
                  aria-sort={sortIndex === index ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                >
                  <button
                    type="button"
                    onClick={() => {
                      if (sortIndex === index) setSortDir((current) => current === 'asc' ? 'desc' : 'asc')
                      else {
                        setSortIndex(index)
                        setSortDir('asc')
                      }
                    }}
                    className="inline-flex min-h-8 items-center gap-1 rounded-md px-1 text-left transition hover:text-[var(--nrg-focus)]"
                  >
                    {header}
                    {sortIndex === index && (
                      <ChevronDown
                        size={12}
                        className={`transition-transform ${sortDir === 'asc' ? 'rotate-180' : ''}`}
                        aria-hidden="true"
                      />
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, rowIndex) => (
              <motion.tr
                key={`${row.join('|')}-${rowIndex}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: Math.min(rowIndex * 0.02, 0.16) }}
                className="transition-colors hover:bg-saffron-500/5"
              >
                {headers.map((_, cellIndex) => (
                  <td key={cellIndex} className="max-w-[18rem] break-words border-b border-nrg-border/40 px-4 py-3 text-sm text-nrg-text">
                    {row[cellIndex] || '—'}
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const StatisticalChart: React.FC<{ response: string }> = ({ response }) => {
  const data = useMemo(() => {
    const matches = response.match(/(\d+(?:\.\d+)?)%/g) || []
    return matches.slice(0, 6).map((p) => ({
      label: p,
      value: parseFloat(p.replace('%', '')),
    }))
  }, [response])

  const maxVal = Math.max(...data.map(d => d.value), 1)

  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs font-medium text-nrg-muted w-12 text-right">
            {d.value}%
          </span>
          <div className="flex-1 bg-[var(--glass-bg)] border border-nrg-border rounded-full h-6 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: 'linear-gradient(90deg, var(--nrg-chart-1), var(--nrg-saffron-soft))',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${(d.value / maxVal) * 100}%` }}
              transition={{ delay: i * 0.1, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

const detectResponseType = (response: string): ResponseType => {
  const lower = response.toLowerCase()
  if (lower.includes('table') || lower.includes('|') || lower.includes('count:') || lower.includes('total:')) return 'tabular'
  if (lower.includes('india') || lower.includes('state') || lower.includes('gujarat') || lower.includes('maharashtra')) return 'geographic'
  if (lower.includes('%') || lower.includes('percentage') || lower.includes('increase') || lower.includes('decrease')) return 'statistical'
  if (lower.includes('compare') || lower.includes('vs') || lower.includes('versus') || lower.includes('better')) return 'comparison'
  return 'text'
}

const extractTabularData = (response: string): { headers: string[]; rows: string[][] } => {
  const lines = response.split('\n')
  const rows: string[][] = []
  let headers: string[] = []

  for (const line of lines) {
    if (line.includes('|')) {
      const cells = line.split('|').filter(c => c.trim()).map(c => c.trim())
      if (cells.length > 1 && !line.includes('---')) {
        if (headers.length === 0) headers = cells
        else rows.push(cells)
      }
    }
  }

  return { headers: headers.slice(0, 8), rows: rows.slice(0, 20) }
}

const formatCellValue = (value: unknown): string => {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'number') return new Intl.NumberFormat('en-IN').format(value)
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (Array.isArray(value)) return value.map(formatCellValue).join(', ')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const humanizeHeader = (key: string): string => (
  key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
)

const buildSqlResultTable = (
  sqlResults?: Array<Record<string, unknown>>
): { headers: string[]; rows: string[][] } | null => {
  if (!sqlResults?.length) return null

  const headers = Array.from(
    sqlResults.reduce((keys, row) => {
      Object.keys(row).forEach((key) => keys.add(key))
      return keys
    }, new Set<string>())
  ).slice(0, 12)

  return {
    headers: headers.map(humanizeHeader),
    rows: sqlResults.slice(0, 500).map((row) => headers.map((key) => formatCellValue(row[key]))),
  }
}

const generatePDF = async (response: string, citations: Citation[]) => {
  const content = `<!DOCTYPE html><html><head><title>NRG Intelligence Brief</title><style>
    ${printDesignTokenCss}
    body { font-family: var(--nrg-font-sans); padding: var(--nrg-space-10); max-width: var(--nrg-export-width); margin: 0 auto; }
    .header { border-bottom: var(--nrg-space-three-quarter) solid var(--nrg-chart-1); padding-bottom: var(--nrg-space-5); margin-bottom: var(--nrg-space-7); }
    .logo { font-size: var(--nrg-type-body-line); font-weight: bold; color: var(--nrg-chart-1); }
    .subtitle { color: var(--nrg-ink-muted); font-size: var(--nrg-type-body-s-size); margin-top: var(--nrg-space-tight); }
    .section { margin-bottom: var(--nrg-space-6); }
    .section-title { font-size: var(--nrg-type-body-size); font-weight: bold; color: var(--nrg-ink); margin-bottom: var(--nrg-space-2); }
    .content { font-size: var(--nrg-type-body-s-size); line-height: 1.6; color: var(--nrg-ink-muted); white-space: pre-wrap; }
    .citations { font-size: var(--nrg-type-caption-size); color: var(--nrg-ink-muted); border-top: var(--nrg-space-0) solid var(--nrg-border); padding-top: var(--nrg-space-3); }
    .footer { margin-top: var(--nrg-space-10); padding-top: var(--nrg-space-3); border-top: var(--nrg-space-0) solid var(--nrg-border); font-size: var(--nrg-type-caption-tight); color: var(--nrg-ink-muted); }
  </style></head><body>
  <div class="header"><div class="logo">राष्ट्रीय गवेषण मंच</div><div class="subtitle">National Research Graph — Intelligence Brief</div></div>
  <div class="section"><div class="section-title">Analysis</div><div class="content">${response}</div></div>
  ${citations.length > 0 ? `<div class="section citations"><div class="section-title">References</div>${citations.map((c, i) => `<div>${i + 1}. ${c.title || 'Unknown'} ${c.year ? `(${c.year})` : ''}</div>`).join('')}</div>` : ''}
  <div class="footer">Generated: ${new Date().toLocaleString()} | NRG Platform — Sovereign Research Intelligence</div>
  </body></html>`

  downloadTextFile(`NRG-Intelligence-Brief-${Date.now()}.html`, content, 'text/html;charset=utf-8')
}

export const AnswerPanel: React.FC<AnswerPanelProps> = ({
  response,
  citations,
  provenance,
  warnings,
  verification_status,
  answer_confidence,
  sqlQuery,
  sqlResults,
  rowsReturned,
  auditEventId,
}) => {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [showSummary, setShowSummary] = useState(true)

  const handleCitationClick = useCallback((citation: Citation) => {
    setSelectedCitation(citation)
    setDrawerOpen(true)
  }, [])

  const parsedResult = useMemo(() => parseCitations(response, citations), [response, citations])
  const { segments, orderedCitations } = parsedResult

  const responseType = useMemo(() => detectResponseType(response), [response])
  const tabularData = useMemo(
    () => responseType === 'tabular' ? extractTabularData(response) : null,
    [response, responseType]
  )
  const sqlResultTable = useMemo(() => buildSqlResultTable(sqlResults), [sqlResults])

  const summary = useMemo(() => {
    const firstPara = response.split('\n')[0]
    return firstPara.length < 300 ? firstPara : firstPara.substring(0, 300) + '...'
  }, [response])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ProvenanceBadge provenance={provenance} />
        <div className="flex items-center gap-3">
          <ConfidenceMeter status={verification_status} answerConfidence={answer_confidence} />
          <motion.button
            onClick={() => generatePDF(response, citations)}
            className="flex min-h-10 items-center gap-1.5 rounded-xl border border-nrg-border bg-[var(--glass-bg)] px-3 py-1.5 text-xs font-medium text-nrg-muted transition-all duration-200 hover:bg-saffron-500/10"
            aria-label={t("auto.components.AnswerPanel.AnswerPanel.11")}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Download size={14} />
            {t("auto.components.AnswerPanel.AnswerPanel.2")}</motion.button>
        </div>
      </div>

      <motion.div
        className="nrg-panel overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="border-b border-nrg-border">
          <button
            onClick={() => setShowSummary(!showSummary)}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-saffron-500/5 transition-colors"
          >
            <span className="font-semibold text-nrg-text text-sm flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-xs">
                <ClipboardList size={14} aria-hidden="true" />
              </span>
              {t("auto.components.AnswerPanel.AnswerPanel.3")}</span>
            <motion.span
              animate={{ rotate: showSummary ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="text-nrg-muted"
            >
              <ChevronDown size={16} />
            </motion.span>
          </button>

          <AnimatePresence>
            {showSummary && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-5">
                   <p className="text-sm text-nrg-muted leading-relaxed font-hindi">
                    {summary}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-6">
          <h3 className="text-sm font-semibold text-nrg-text mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-md bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-xs">
              <BarChart3 size={14} aria-hidden="true" />
            </span>
            {t("auto.components.AnswerPanel.AnswerPanel.4")}</h3>

          {sqlResultTable?.headers.length ? (
            <TabularView
              headers={sqlResultTable.headers}
              rows={sqlResultTable.rows}
              testId="sql-results-table"
            />
          ) : responseType === 'tabular' && tabularData?.headers.length ? (
            <TabularView headers={tabularData.headers} rows={tabularData.rows} />
          ) : responseType === 'statistical' ? (
            <StatisticalChart response={response} />
          ) : (
            <div className="prose prose-sm max-w-none text-nrg-text leading-relaxed">
              {segments.map((part, index) => {
                if (part.type === 'text') {
                  return <span key={index}>{part.content}</span>
                }

                return (
                  <motion.sup
                    key={index}
                    className="cursor-pointer text-saffron-500 hover:text-saffron-700 font-bold mx-0.5 transition-colors inline-flex items-center justify-center w-5 h-5 text-xs rounded-full bg-saffron-50 hover:bg-saffron-100"
                    onClick={() => part.citation && handleCitationClick(part.citation)}
                    title={part.citation?.title || 'Citation'}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    [{part.citationNumber || '?'}]
                  </motion.sup>
                )
              })}
            </div>
          )}
        </div>

        {orderedCitations.length > 0 && (
          <div className="border-t border-nrg-border px-6 py-4 bg-[var(--glass-bg)]">
            <h4 className="text-sm font-semibold text-nrg-text mb-3 flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs">
                <BookOpen size={14} aria-hidden="true" />
              </span>
              {t("auto.components.AnswerPanel.AnswerPanel.5")}{orderedCitations.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {orderedCitations.slice(0, 8).map((citation, index) => (
                <motion.button
                  key={citation.id}
                  className="text-left p-3 rounded-xl bg-[var(--nrg-surface)] border border-nrg-border hover:border-saffron-300 dark:hover:border-saffron-600 hover:shadow-md transition-all duration-200"
                  onClick={() => handleCitationClick(citation)}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ y: -2 }}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-bold text-saffron-500 dark:text-saffron-400 shrink-0 mt-0.5 w-5 h-5 rounded-full bg-saffron-50 dark:bg-saffron-900/30 flex items-center justify-center">
                      {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-nrg-text line-clamp-2 leading-snug">
                        {citation.title || 'Publication title unavailable'}
                      </p>
                      <p className="text-xs text-nrg-muted mt-0.5 flex items-center gap-1">
                        <SourceIcon source={citation.source} />
                        {citation.year && <span className="mr-2">{citation.year}</span>}
                        {toStringArray(citation.authors)?.slice(0, 2).join(', ')}
                      </p>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <div className="border-t border-nrg-border px-6 py-4 bg-[var(--glass-bg)]">
          <AnswerTrustActions
            answer={response}
            sqlQuery={sqlQuery}
            rowsReturned={rowsReturned}
            auditEventId={auditEventId}
          />
        </div>
      </motion.div>

      {warnings && warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20"
        >
          <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2 flex items-center gap-2">
            <AlertCircle size={16} />
            {t("auto.components.AnswerPanel.AnswerPanel.6")}</h4>
          <ul className="text-sm text-amber-700 dark:text-amber-300 space-y-1">
            {warnings.map((warning, index) => (
              <li key={index} className="flex items-start gap-2">
                {warning.skill && <span className="font-medium shrink-0">[{warning.skill}]</span>}
                <span>{warning.message || warning.error_type || 'Warning'}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      <CitationDrawer
        citation={selectedCitation}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  )
}

export default AnswerPanel
