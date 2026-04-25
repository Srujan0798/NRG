import React, { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Citation } from '../../services/queryService'
import { queryService } from '../../services/queryService'
import { toStringArray } from '../../types/api'
import { X, Copy, FileText, Database, GitMerge, Shield } from 'lucide-react'

interface CitationDrawerProps {
  citation: Citation | null
  isOpen: boolean
  onClose: () => void
}

const SourceIcon: React.FC<{ source?: string }> = ({ source }) => {
  if (source === 'SQL') return <Database size={14} className="text-blue-500" />
  if (source === 'RAG') return <GitMerge size={14} className="text-purple-500" />
  return <GitMerge size={14} className="text-saffron-500" />
}

const RelevanceBadge: React.FC<{ score?: number }> = ({ score }) => {
  if (score === undefined) return null
  const color = score > 0.7 ? '#22c55e' : score > 0.4 ? '#f59e0b' : '#ef4444'
  const label = score > 0.7 ? 'High' : score > 0.4 ? 'Medium' : 'Low'

  return (
    <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 dark:bg-navy-700/50 border border-slate-200 dark:border-navy-600">
      <motion.div
        className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
        style={{ background: color }}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      >
        {Math.round(score * 100)}
      </motion.div>
      <div>
        <p className="text-xs font-medium text-slate-900 dark:text-white">Relevance Score</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{label} match</p>
      </div>
    </div>
  )
}

const DrawerBackdrop: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => (
  <AnimatePresence>
    {isOpen && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
        onClick={onClose}
      />
    )}
  </AnimatePresence>
)

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  isOpen,
  onClose,
}) => {
  const [loading, setLoading] = useState(false)
  const [details, setDetails] = useState<any>(null)
  const [activeSection, setActiveSection] = useState<'source' | 'metadata' | 'context'>('source')
  const [copied, setCopied] = useState(false)

  const parseCiteToken = (id: string): { pubId: string; chunkId: string } | null => {
    const match = id?.match(/^cite:(.+?):(.+)$/)
    if (match) return { pubId: match[1], chunkId: match[2] }
    const parts = id?.split(':') || []
    if (parts.length >= 2) return { pubId: parts[0], chunkId: parts[1] }
    return null
  }

  const fetchCitationDetails = useCallback(async (cite: Citation) => {
    setLoading(true)
    try {
      const parsed = parseCiteToken(cite.id) || {
        pubId: cite.pub_id || '',
        chunkId: cite.chunk_id || '',
      }

      if (cite.title && cite.authors?.length) {
        setDetails({
          title: cite.title,
          year: cite.year || 0,
          authors: toStringArray(cite.authors),
          chunk_text: cite.chunk_text || `Chunk ${parsed.chunkId} content`,
          pub_id: cite.pub_id || parsed.pubId || 'unknown',
          chunk_id: cite.chunk_id || parsed.chunkId || 'unknown',
          institution: cite.research_area || 'Source institution unavailable',
          citations: cite.citation_count || 0,
          doi: cite.doi || 'Not available',
          journal: cite.journal || 'Journal unavailable',
          abstract: cite.abstract || null,
        })
        setLoading(false)
        return
      }

      if (parsed.pubId) {
        try {
          const pubData = await queryService.fetchPublications(100)
          const pub: any = pubData.publications.find((p) => p.publication_id === parsed.pubId)
          if (pub) {
            setDetails({
              title: pub.title || cite.title || `Publication ${parsed.pubId}`,
              year: pub.year || cite.year || 0,
              authors: toStringArray(cite.authors)?.length ? toStringArray(cite.authors) : ['Author data unavailable'],
              chunk_text: cite.chunk_text || `Chunk ${parsed.chunkId} content`,
              pub_id: parsed.pubId,
              chunk_id: parsed.chunkId,
              institution: pub.institution || 'Source institution unavailable',
              citations: pub.citations || 0,
              doi: pub.doi || 'Not available',
              journal: pub.venue || 'Journal unavailable',
              abstract: pub.abstract || null,
            })
            setLoading(false)
            return
          }
        } catch { /* citation fetch failed */ }
      }

      setDetails({
        title: cite.title || `Publication ${cite.pub_id || parsed.pubId || 'unknown'}`,
        year: cite.year || 2024,
        authors: toStringArray(cite.authors)?.length ? toStringArray(cite.authors) : ['Author unavailable'],
        chunk_text: cite.chunk_text || `Chunk content for ${parsed.chunkId || 'unknown'}`,
        pub_id: cite.pub_id || parsed.pubId || 'unknown',
        chunk_id: cite.chunk_id || parsed.chunkId || 'unknown',
        institution: cite.research_area || 'Source institution unavailable',
        citations: cite.citation_count || 0,
        doi: cite.doi || 'Not available',
        journal: cite.journal || 'Journal unavailable',
        abstract: cite.abstract || null,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (citation && isOpen) {
      fetchCitationDetails(citation)
    }
  }, [citation, isOpen, fetchCitationDetails])

  const handleCopy = async () => {
    if (!details) return
    const text = `${details.title}. ${details.authors.join(', ')} (${details.year}). ${details.journal}.`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <DrawerBackdrop isOpen={isOpen} onClose={onClose} />

      <AnimatePresence>
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed inset-y-0 right-0 z-50 w-full sm:w-[440px] bg-white dark:bg-navy-800 shadow-2xl border-l border-slate-200 dark:border-navy-700 flex flex-col"
        >
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 shrink-0">
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Citation Details</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Source verification and context</p>
            </div>
            <motion.button
              onClick={onClose}
              className="w-9 h-9 rounded-xl border border-slate-200 dark:border-navy-600 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-navy-700 transition-all duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <X size={16} />
            </motion.button>
          </div>

          <div className="flex-1 overflow-y-auto scrollbar-nrg">
            {loading ? (
              <div className="flex items-center justify-center h-48">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-10 h-10 rounded-full border-3 border-saffron-200 border-t-saffron-500 animate-spin" />
                  <p className="text-sm text-slate-500">Loading citation...</p>
                </div>
              </div>
            ) : details ? (
              <div className="p-6 space-y-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-saffron-50 dark:bg-saffron-900/30 text-saffron-700 dark:text-saffron-400 border border-saffron-200 dark:border-saffron-700">
                      <span className="flex items-center gap-1">
                        <FileText size={10} />
                        {details.journal}
                      </span>
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">{details.year}</span>
                  </div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white leading-snug mb-2">
                    {details.title}
                  </h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {details.authors.slice(0, 5).join(', ')}
                    {details.authors.length > 5 && ` +${details.authors.length - 5} more`}
                  </p>
                </div>

                <RelevanceBadge score={citation?.relevance_score} />

                <div className="flex gap-1 border-b border-slate-200 dark:border-navy-700">
                  {(['source', 'metadata', 'context'] as const).map((tab) => (
                    <motion.button
                      key={tab}
                      onClick={() => setActiveSection(tab)}
                      className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-all duration-200 ${
                        activeSection === tab
                          ? 'border-saffron-500 text-saffron-600 dark:text-saffron-400'
                          : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </motion.button>
                  ))}
                </div>

                {activeSection === 'source' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                        Source Excerpt
                      </p>
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-700/50 border border-slate-200 dark:border-navy-600">
                        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed italic">
                          "{details.chunk_text}"
                        </p>
                      </div>
                    </div>

                    {details.abstract && (
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                          Abstract
                        </p>
                        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                          {details.abstract}
                        </p>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeSection === 'metadata' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-3"
                  >
                    {[
                      { label: 'Publication ID', value: details.pub_id },
                      { label: 'Chunk ID', value: details.chunk_id },
                      { label: 'DOI', value: details.doi },
                      { label: 'Year', value: details.year?.toString() || 'Unknown' },
                      { label: 'Citations', value: details.citations?.toString() || '0' },
                      { label: 'Institution', value: details.institution },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex items-start justify-between py-2 border-b border-slate-100 dark:border-navy-700/50 last:border-0">
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
                        <span className="text-xs text-slate-900 dark:text-slate-100 text-right max-w-[60%] font-mono">
                          {value || 'Unavailable'}
                        </span>
                      </div>
                    ))}
                  </motion.div>
                )}

                {activeSection === 'context' && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-3"
                  >
                    <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-600">
                      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
                        Citation ID Format
                      </p>
                      <code className="text-xs text-slate-900 dark:text-slate-100 font-mono block">
                        cite:{details.pub_id}:{details.chunk_id}
                      </code>
                    </div>

                    <div className="p-4 rounded-xl border border-slate-200 dark:border-navy-600">
                      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">Source</p>
                      <p className="text-xs text-slate-900 dark:text-slate-100 flex items-center gap-1">
                        <SourceIcon source={citation?.source} />
                        {citation?.source || 'Source unavailable'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-saffron-50 dark:bg-saffron-900/20 border border-saffron-200 dark:border-saffron-700">
                      <p className="text-xs font-semibold text-saffron-700 dark:text-saffron-300 mb-1 flex items-center gap-1">
                        <Shield size={12} />
                        DPDP Notice
                      </p>
                      <p className="text-xs text-saffron-600 dark:text-saffron-400 leading-relaxed">
                        This citation is logged per DPDP Act 2023 consent framework. Source data is retained in sovereign Indian infrastructure.
                      </p>
                    </div>
                  </motion.div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-slate-400">
                <FileText size={40} className="mb-3 opacity-50" />
                <p className="text-sm">Citation details are not available for this source.</p>
              </div>
            )}
          </div>

          <div className="px-6 py-4 border-t border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 shrink-0">
            <div className="flex gap-3">
              <motion.button
                onClick={handleCopy}
                className="nrg-btn-secondary flex-1 text-xs py-2.5"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Copy size={14} className="mr-1.5" />
                {copied ? 'Copied!' : 'Copy Citation'}
              </motion.button>
              <motion.button
                onClick={onClose}
                className="nrg-btn-primary flex-1 text-xs py-2.5"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Close
              </motion.button>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </>
  )
}

export default CitationDrawer
