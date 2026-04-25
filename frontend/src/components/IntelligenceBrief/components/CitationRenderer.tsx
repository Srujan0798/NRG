import React, { useState } from 'react'
import { Citation } from '../../../services/queryService'
import { toStringArray } from '../../../types/api'

interface CitationChipProps {
  citation: Citation
  index: number
  onClick: () => void
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, index, onClick }) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const authorList = toStringArray(citation.authors)
  const displayAuthors = authorList?.slice(0, 2).join(', ')
  const extraCount = (authorList?.length ?? 0) - 2

  return (
    <div className="relative inline-block">
      <button
        className="inline-flex min-h-8 items-center gap-1 rounded-md border border-saffron-200 bg-saffron-50 px-2.5 py-1 text-xs font-semibold text-saffron-700 transition-all hover:-translate-y-0.5 hover:bg-saffron-600 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        onClick={onClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        aria-label={`Open citation ${index}: ${citation.title || citation.pub_id || 'source'}`}
      >
        <span className="font-bold">[{index}]</span>
        <span className="max-w-32 truncate">{citation.title?.split(':')[0] || 'Source'}</span>
      </button>

      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 w-64 p-3 rounded-xl bg-nrg-surface border border-nrg-border shadow-nrg-card z-50">
          <p className="text-xs font-medium text-nrg-text line-clamp-2 mb-1">{citation.title || 'Source title unavailable'}</p>
          <p className="text-xs text-nrg-muted">
            {displayAuthors}
            {extraCount > 0 && ` +${extraCount}`}
          </p>
          {citation.year && <p className="text-xs text-nrg-muted mt-0.5">{citation.year}</p>}
          <p className="text-xs text-saffron-600 mt-1.5 pt-1.5 border-t border-nrg-border">Click to view full details</p>
        </div>
      )}
    </div>
  )
}

interface CitationListProps {
  citations: Citation[]
  onCitationClick: (citation: Citation) => void
}

export const CitationList: React.FC<CitationListProps> = ({ citations, onCitationClick }) => {
  return (
    <div className="space-y-2">
      {citations.map((citation, index) => (
        <CitationChip
          key={citation.id || `${citation.pub_id}-${citation.chunk_id}`}
          citation={citation}
          index={index + 1}
          onClick={() => onCitationClick(citation)}
        />
      ))}
    </div>
  )
}

export default CitationChip
