import React, { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CitationDrawer } from '../CitationDrawer'
import { Citation, GraphNode, QueryProvenance, QueryWarning } from '../../services/queryService'
import { parseCitations } from '../../utils/parseCitations'
import { toStringArray } from '../../types/api'
import { CheckCircle, AlertCircle, Cloud, Database, GitMerge, ChevronDown, Download } from 'lucide-react'

interface AnswerPanelProps {
  response: string
  citations: Citation[]
  provenance?: QueryProvenance
  warnings?: QueryWarning[]
  verification_status?: boolean
  onNodeClick?: (node: GraphNode) => void
}

type ResponseType = 'tabular' | 'geographic' | 'statistical' | 'comparison' | 'text'

const SourceIcon: React.FC<{ source?: string }> = ({ source }) => {
  if (source === 'SQL') return <Database size={14} className="text-blue-500" />
  if (source === 'RAG') return <GitMerge size={14} className="text-purple-500" />
  return <GitMerge size={14} className="text-saffron-500" />
}

const ConfidenceMeter: React.FC<{ status: boolean | undefined }> = ({ status }) => {
  const isVerified = status === true
  const bars = isVerified ? 3 : 2

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-navy-700/50">
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
        {isVerified ? 'High Confidence' : 'Medium Confidence'}
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
          {provenance.planner} planner
        </motion.span>
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

const TabularView: React.FC<{ headers: string[]; rows: string[][] }> = ({ headers, rows }) => (
  <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-navy-700">
    <table className="min-w-full text-sm">
      <thead className="bg-gradient-to-r from-saffron-50 to-white dark:from-navy-700/50 dark:to-navy-800">
        <tr>
          {headers.map((h, i) => (
            <th key={i} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-navy-700">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <motion.tr
            key={ri}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: ri * 0.03 }}
            className="hover:bg-saffron-50/50 dark:hover:bg-navy-700/30 transition-colors"
          >
            {row.map((cell, ci) => (
              <td key={ci} className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300 border-b border-slate-100 dark:border-navy-700/50">
                {cell}
              </td>
            ))}
          </motion.tr>
        ))}
      </tbody>
    </table>
  </div>
)

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
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400 w-12 text-right">
            {d.value}%
          </span>
          <div className="flex-1 bg-slate-100 dark:bg-navy-700 rounded-full h-6 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: 'linear-gradient(90deg, #ff6b35, #ff8b4a)',
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

const generatePDF = async (response: string, citations: Citation[]) => {
  const content = `<!DOCTYPE html><html><head><title>NRG Intelligence Brief</title><style>
    body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
    .header { border-bottom: 3px solid #ff6b35; padding-bottom: 20px; margin-bottom: 30px; }
    .logo { font-size: 24px; font-weight: bold; color: #ff6b35; }
    .subtitle { color: #6b7280; font-size: 14px; margin-top: 5px; }
    .section { margin-bottom: 25px; }
    .section-title { font-size: 16px; font-weight: bold; color: #1f2937; margin-bottom: 10px; }
    .content { font-size: 14px; line-height: 1.6; color: #374151; white-space: pre-wrap; }
    .citations { font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 15px; }
    .footer { margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #9ca3af; }
  </style></head><body>
  <div class="header"><div class="logo">राष्ट्रीय गवेषण मंच</div><div class="subtitle">National Research Graph — Intelligence Brief</div></div>
  <div class="section"><div class="section-title">Analysis</div><div class="content">${response}</div></div>
  ${citations.length > 0 ? `<div class="section citations"><div class="section-title">References</div>${citations.map((c, i) => `<div>${i + 1}. ${c.title || 'Unknown'} ${c.year ? `(${c.year})` : ''}</div>`).join('')}</div>` : ''}
  <div class="footer">Generated: ${new Date().toLocaleString()} | NRG Platform — Sovereign Research Intelligence</div>
  </body></html>`

  const blob = new Blob([content], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = window.document.createElement('a')
  a.href = url
  a.download = `NRG-Intel-Brief-${Date.now()}.html`
  a.click()
  URL.revokeObjectURL(url)
}

export const AnswerPanel: React.FC<AnswerPanelProps> = ({
  response,
  citations,
  provenance,
  warnings,
  verification_status,
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

  const summary = useMemo(() => {
    const firstPara = response.split('\n')[0]
    return firstPara.length < 300 ? firstPara : firstPara.substring(0, 300) + '...'
  }, [response])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ProvenanceBadge provenance={provenance} />
        <div className="flex items-center gap-3">
          <ConfidenceMeter status={verification_status} />
          <motion.button
            onClick={() => generatePDF(response, citations)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-100 dark:bg-navy-700/50 border border-slate-200 dark:border-navy-600 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-navy-600 transition-all duration-200"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Download size={14} />
            Export
          </motion.button>
        </div>
      </div>

      <motion.div
        className="overflow-hidden rounded-2xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-700 shadow-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="border-b border-slate-200 dark:border-navy-700">
          <button
            onClick={() => setShowSummary(!showSummary)}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-navy-700/30 transition-colors"
          >
            <span className="font-semibold text-slate-900 dark:text-white text-sm flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-xs">
                📋
              </span>
              Summary
            </span>
            <motion.span
              animate={{ rotate: showSummary ? 180 : 0 }}
              transition={{ duration: 0.2 }}
              className="text-slate-400"
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
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-hindi">
                    {summary}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="p-6">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded-md bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-xs">
              📊
            </span>
            Detailed Analysis
          </h3>

          {responseType === 'tabular' && tabularData?.headers.length ? (
            <TabularView headers={tabularData.headers} rows={tabularData.rows} />
          ) : responseType === 'statistical' ? (
            <StatisticalChart response={response} />
          ) : (
            <div className="prose prose-sm max-w-none text-slate-700 dark:text-slate-300 leading-relaxed">
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
          <div className="border-t border-slate-200 dark:border-navy-700 px-6 py-4 bg-slate-50 dark:bg-navy-700/30">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-3 flex items-center gap-2">
              <span className="w-6 h-6 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center text-xs">
                📚
              </span>
              References ({orderedCitations.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {orderedCitations.slice(0, 8).map((citation, index) => (
                <motion.button
                  key={citation.id}
                  className="text-left p-3 rounded-xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-600 hover:border-saffron-300 dark:hover:border-saffron-600 hover:shadow-md transition-all duration-200"
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
                      <p className="text-xs font-medium text-slate-900 dark:text-slate-100 line-clamp-2 leading-snug">
                        {citation.title || 'Unknown Publication'}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 flex items-center gap-1">
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
      </motion.div>

      {warnings && warnings.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border border-amber-200 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/20"
        >
          <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2 flex items-center gap-2">
            <AlertCircle size={16} />
            Notes
          </h4>
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
