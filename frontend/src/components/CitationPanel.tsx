import React from 'react'
import { FileTextIcon } from './Icons'
import { Citation } from '../services/queryService'
import { toStringArray } from '../types/api'

interface CitationPanelProps {
  citations: Citation[]
  className?: string
}

const CitationPanel: React.FC<CitationPanelProps> = ({ citations, className = '' }) => {
  if (!citations || citations.length === 0) {
    return null
  }

  return (
    <div className={`bg-gray-50 rounded-lg p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
        <FileTextIcon className="w-4 h-4 mr-2" />
        Sources & References
      </h3>
      
      <div className="space-y-3">
        {citations.map((citation, index) => (
          <div key={citation.id} className="text-sm">
            <div className="font-medium text-gray-900">
              {citation.title}
            </div>
            
            <div className="text-gray-600 mt-1">
              {toStringArray(citation.authors)?.join(', ')}
              {citation.year && ` • ${citation.year}`}
            </div>
            
            <div className="text-xs text-gray-500 mt-1">
              Source: {citation.source}
              {citation.relevance_score && (
                <span className="ml-2 text-blue-600">
                  {Math.round(citation.relevance_score * 100)}% relevant
                </span>
              )}
            </div>
            
            {index < citations.length - 1 && (
              <hr className="my-2 border-gray-200" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default CitationPanel
