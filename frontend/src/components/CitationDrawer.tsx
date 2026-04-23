import React, { useState, useEffect } from 'react'
import { Citation } from '../services/queryService'
import { queryService } from '../services/queryService'
import { toStringArray } from '../types/api'

interface CitationDrawerProps {
  citation: Citation | null
  isOpen: boolean
  onClose: () => void
  responseText?: string
}

const DrawerBackdrop: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  if (!isOpen) return null
  return (
    <div
      className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 transition-opacity duration-300"
      onClick={onClose}
    />
  )
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  isOpen,
  onClose,
  responseText,
}) => {
  const [loading, setLoading] = useState(false)
  const [details, setDetails] = useState<any>(null)
  const [activeSection, setActiveSection] = useState<'source' | 'metadata' | 'context'>('source')

  useEffect(() => {
    if (citation && isOpen) {
      fetchCitationDetails(citation)
    }
  }, [citation, isOpen])

  const parseCiteToken = (id: string): { pubId: string; chunkId: string } | null => {
    const match = id?.match(/^cite:(.+?):(.+)$/)
    if (match) return { pubId: match[1], chunkId: match[2] }
    const parts = id?.split(':') || []
    if (parts.length >= 2) return { pubId: parts[0], chunkId: parts[1] }
    return null
  }

  const fetchCitationDetails = async (cite: Citation) => {
    setLoading(true)
    try {
      const parsed = parseCiteToken(cite.id) || {
        pubId: cite.pub_id || '',
        chunkId: cite.chunk_id || '',
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
              institution: pub.institution || 'Unknown Institution',
              citations: pub.citations || 0,
              doi: pub.doi || 'Not available',
              journal: pub.venue || 'Unknown Journal',
              abstract: pub.abstract || null,
            })
            return
          }
        } catch {}
      }

      setDetails({
        title: cite.title || `Publication ${cite.pub_id || parsed.pubId || 'unknown'}`,
        year: cite.year || 2024,
        authors: toStringArray(cite.authors)?.length ? toStringArray(cite.authors) : ['Unknown Author'],
        chunk_text: cite.chunk_text || `Chunk content for ${parsed.chunkId || 'unknown'}`,
        pub_id: cite.pub_id || parsed.pubId || 'unknown',
        chunk_id: cite.chunk_id || parsed.chunkId || 'unknown',
        institution: 'Unknown Institution',
        citations: 0,
        doi: 'Not available',
        journal: 'Unknown Journal',
        abstract: null,
      })
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen || !citation) return null

  return (
    <>
      <DrawerBackdrop isOpen={isOpen} onClose={onClose} />

      <div
        className={`
          fixed inset-y-0 right-0 z-50 w-full sm:w-[440px]
          bg-nrg-surface shadow-2xl border-l border-nrg-border
          transform transition-transform duration-350 ease-[cubic-bezier(0.16,1,0.3,1)]
          flex flex-col
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-nrg-border bg-nrg-surface shrink-0">
          <div>
            <h3 className="text-base font-semibold text-nrg-text">Citation Details</h3>
            <p className="text-xs text-nrg-muted mt-0.5">Source verification and context</p>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-xl border border-nrg-border flex items-center justify-center text-nrg-muted hover:text-nrg-text hover:bg-nrg-navy-50 transition-all duration-200"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto scrollbar-nrg">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="nrg-ashoka-spinner" />
            </div>
          ) : details ? (
            <div className="p-6 space-y-6">
              {/* Publication Title + Authors */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-saffron-50 text-saffron-700 border border-saffron-200">
                    {details.journal}
                  </span>
                  <span className="text-xs text-nrg-muted">{details.year}</span>
                </div>
                <h2 className="text-lg font-semibold text-nrg-text leading-snug mb-2">{details.title}</h2>
                <p className="text-sm text-nrg-muted leading-relaxed">
                  {details.authors.slice(0, 5).join(', ')}
                  {details.authors.length > 5 && ` +${details.authors.length - 5} more`}
                </p>
              </div>

              {/* Relevance Score Badge */}
              {citation.relevance_score !== undefined && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-nrg-navy-50 border border-nrg-border">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                    style={{ background: citation.relevance_score > 0.7 ? '#10b981' : citation.relevance_score > 0.4 ? '#f59e0b' : '#ef4444' }}
                  >
                    {Math.round(citation.relevance_score * 100)}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-nrg-text">Relevance Score</p>
                    <p className="text-xs text-nrg-muted">Semantic similarity to your query</p>
                  </div>
                </div>
              )}

              {/* Tab Navigation */}
              <div className="flex gap-1 border-b border-nrg-border">
                {(['source', 'metadata', 'context'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveSection(tab)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-all duration-200 ${
                      activeSection === tab
                        ? 'border-saffron-500 text-saffron-600'
                        : 'border-transparent text-nrg-muted hover:text-nrg-text'
                    }`}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              {/* Source Tab */}
              {activeSection === 'source' && (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-nrg-muted mb-2">Source Excerpt</p>
                    <div className="p-4 rounded-xl bg-nrg-navy-50 border border-nrg-border">
                      <p className="text-sm text-nrg-text leading-relaxed italic">
                        "{details.chunk_text}"
                      </p>
                    </div>
                  </div>

                  {details.abstract && (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-nrg-muted mb-2">Abstract</p>
                      <p className="text-sm text-nrg-muted leading-relaxed">{details.abstract}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Metadata Tab */}
              {activeSection === 'metadata' && (
                <div className="space-y-3">
                  {[
                    { label: 'Publication ID', value: details.pub_id },
                    { label: 'Chunk ID', value: details.chunk_id },
                    { label: 'DOI', value: details.doi },
                    { label: 'Year', value: details.year?.toString() || 'Unknown' },
                    { label: 'Citations', value: details.citations?.toString() || '0' },
                    { label: 'Institution', value: details.institution },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex items-start justify-between py-2 border-b border-nrg-border/50 last:border-0">
                      <span className="text-xs font-medium text-nrg-muted">{label}</span>
                      <span className="text-xs text-nrg-text text-right max-w-[60%] font-mono">{value || 'N/A'}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Context Tab */}
              {activeSection === 'context' && (
                <div className="space-y-3">
                  <div className="p-4 rounded-xl border border-nrg-border">
                    <p className="text-xs font-semibold text-nrg-muted mb-2">Citation ID Format</p>
                    <code className="text-xs text-nrg-text font-mono block">
                      cite:{details.pub_id}:{details.chunk_id}
                    </code>
                  </div>
                  <div className="p-4 rounded-xl border border-nrg-border">
                    <p className="text-xs font-semibold text-nrg-muted mb-2">Source</p>
                    <p className="text-xs text-nrg-text">{citation.source || 'Unknown source'}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-saffron-50 border border-saffron-200">
                    <p className="text-xs font-semibold text-saffron-700 mb-1">DPDP Notice</p>
                    <p className="text-xs text-saffron-600 leading-relaxed">
                      This citation is logged per DPDP Act 2023 consent framework. Source data is retained in sovereign Indian infrastructure.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-nrg-muted">
              <span className="text-2xl mb-2">📭</span>
              <p className="text-sm">No citation details available</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-nrg-border bg-nrg-surface shrink-0">
          <div className="flex gap-3">
            <button className="nrg-btn-secondary flex-1 text-xs py-2">
              Export Citation
            </button>
            <button
              onClick={onClose}
              className="nrg-btn-primary flex-1 text-xs py-2"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  )
}