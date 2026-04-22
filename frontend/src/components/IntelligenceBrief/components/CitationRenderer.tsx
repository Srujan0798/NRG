import React, { useState } from 'react'
import { Citation } from '../../../services/queryService'

interface CitationChipProps {
  citation: Citation
  index: number
  onClick: () => void
}

export const CitationChip: React.FC<CitationChipProps> = ({ citation, index, onClick }) => {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="relative inline-block">
      <button
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium 
          bg-saffron-50 text-saffron-700 border border-saffron-200 
          hover:bg-saffron-100 hover:border-saffron-300 transition-all cursor-pointer"
        onClick={onClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <span className="font-bold">[{index}]</span>
        <span className="max-w-[120px] truncate">{citation.title?.split(':')[0] || 'Source'}</span>
      </button>
      
      {showTooltip && (
        <div className="absolute bottom-full left-0 mb-2 w-64 p-3 rounded-xl bg-nrg-surface border border-nrg-border shadow-nrg-card z-50">
          <p className="text-xs font-medium text-nrg-text line-clamp-2 mb-1">{citation.title || 'Unknown Source'}</p>
          <p className="text-xs text-nrg-muted">
            {citation.authors?.slice(0, 2).join(', ')}
            {citation.authors && citation.authors.length > 2 && ` +${citation.authors.length - 2}`}
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