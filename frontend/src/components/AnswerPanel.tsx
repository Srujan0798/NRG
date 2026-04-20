import React, { useState, useCallback } from 'react';
import { CitationDrawer } from './CitationDrawer';
import { Citation, GraphNode, QueryProvenance, QueryWarning } from '../services/queryService';
import { parseCitations } from '../utils/parseCitations';

interface AnswerPanelProps {
  response: string;
  citations: Citation[];
  provenance?: QueryProvenance;
  warnings?: QueryWarning[];
  onNodeClick?: (node: GraphNode) => void;
}

export const AnswerPanel: React.FC<AnswerPanelProps> = ({
  response,
  citations,
  provenance,
  warnings,
}) => {
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleCitationClick = (citation: Citation) => {
    setSelectedCitation(citation);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedCitation(null);
  };

  const parsed = useCallback(() => parseCitations(response, citations), [response, citations]);
  const parsedResult = parsed();
  const parsedParts = parsedResult.segments;
  const orderedCitations = parsedResult.orderedCitations;

  return (
    <div className="space-y-4">
      {/* Provenance Badge */}
      {provenance && (
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
            Planner: {provenance.planner || 'unknown'}
          </span>
          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
            Synth: {provenance.synth || 'unknown'}
          </span>
          {provenance.verifier && (
            <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
              Verifier: {provenance.verifier}
            </span>
          )}
          <span className={`px-2 py-1 rounded-full ${
            provenance.cloud_synthesis_used
              ? 'bg-amber-100 text-amber-800'
              : 'bg-slate-100 text-slate-700'
          }`}>
            Cloud: {provenance.cloud_synthesis_used ? 'used' : 'not used'}
          </span>
        </div>
      )}

      {/* Main Response */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
        <div className="prose prose-slate max-w-none">
          {parsedParts.map((part, index) => {
            if (part.type === 'text') {
              return <span key={index}>{part.content}</span>;
            }
            
            return (
              <sup
                key={index}
                className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium mx-0.5"
                onClick={() => part.citation && handleCitationClick(part.citation)}
                title={part.citation?.title || 'Citation'}
              >
                [{part.citationNumber || '?'}]
              </sup>
            );
          })}
        </div>

        {/* Citations List */}
        {orderedCitations.length > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">References</h4>
            <ol className="space-y-2 text-sm text-gray-600">
              {orderedCitations.map((citation, index) => (
                <li
                  key={citation.id}
                  className="cursor-pointer hover:text-blue-600"
                  onClick={() => handleCitationClick(citation)}
                >
                  [{index + 1}] {citation.title || 'Unknown'} 
                  {citation.year && `(${citation.year})`}
                  {citation.authors && ` - ${citation.authors.slice(0, 2).join(', ')}`}
                  {citation.relevance_score && (
                    <span className="text-gray-400 ml-2">
                      relevance: {(citation.relevance_score * 100).toFixed(0)}%
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">Warnings</h4>
          <ul className="text-sm text-yellow-700 space-y-1">
            {warnings.map((warning, index) => (
              <li key={index}>
                {warning.skill && <span className="font-medium">{warning.skill}: </span>}
                {warning.node && <span className="font-medium">{warning.node}: </span>}
                {warning.message || warning.error_type || 'Warning'}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Citation Drawer */}
      <CitationDrawer
        citation={selectedCitation}
        isOpen={drawerOpen}
        onClose={handleCloseDrawer}
      />
    </div>
  );
};
