import React, { useState, useEffect } from 'react';
import { XIcon } from './Icons';
import { Citation } from '../services/queryService';
import { queryService } from '../services/queryService';

interface CitationDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
  responseText?: string;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  isOpen,
  onClose,
  responseText,
}) => {
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState<any>(null);

  useEffect(() => {
    if (citation && isOpen) {
      fetchCitationDetails(citation);
    }
  }, [citation, isOpen]);

  const parseCiteToken = (id: string): { pubId: string; chunkId: string } | null => {
    const match = id?.match(/^cite:(.+?):(.+)$/);
    if (match) return { pubId: match[1], chunkId: match[2] };
    const parts = id?.split(':') || [];
    if (parts.length >= 2) return { pubId: parts[0], chunkId: parts[1] };
    return null;
  };

  const extractInlineCitations = (text: string): Citation[] => {
    const regex = /\[cite:([^:]+):([^\]]+)\]/g;
    const citations: Citation[] = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      citations.push({
        id: `cite:${match[1]}:${match[2]}`,
        source: 'inline',
        pub_id: match[1],
        chunk_id: match[2],
        title: '',
        authors: [],
        year: 0,
        relevance_score: 0,
      });
    }
    return citations;
  };

  const fetchCitationDetails = async (cite: Citation) => {
    setLoading(true);
    try {
      const parsed = parseCiteToken(cite.id) || {
        pubId: cite.pub_id || '',
        chunkId: cite.chunk_id || '',
      };

      if (parsed.pubId) {
        try {
          const pubData = await queryService.fetchPublications(100);
          const pub = pubData.publications.find((p) => p.publication_id === parsed.pubId);
          if (pub) {
            setDetails({
              title: pub.title || cite.title || `Publication ${parsed.pubId}`,
              year: pub.year || cite.year || 0,
              authors: cite.authors?.length ? cite.authors : ['Author data unavailable'],
              chunk_text: cite.chunk_text || `Chunk ${parsed.chunkId} content`,
              pub_id: parsed.pubId,
              chunk_id: parsed.chunkId,
            });
            return;
          }
        } catch {
          // API fetch failed, fall through to citation data
        }
      }

      setDetails({
        title: cite.title || `Publication ${cite.pub_id || parsed.pubId || 'unknown'}`,
        year: cite.year || 2024,
        authors: cite.authors?.length ? cite.authors : ['Unknown Author'],
        chunk_text: cite.chunk_text || `Chunk content for ${parsed.chunkId || 'unknown'}`,
        pub_id: cite.pub_id || parsed.pubId || 'unknown',
        chunk_id: cite.chunk_id || parsed.chunkId || 'unknown',
      });
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-96 bg-white shadow-2xl border-l border-gray-200 transform transition-transform duration-300 ease-in-out">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Citation Details</h3>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-gray-100 transition"
        >
          <XIcon className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
          </div>
        ) : details ? (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Publication
              </h4>
              <p className="mt-1 text-base font-semibold text-gray-900">
                {details.title}
              </p>
              <p className="text-sm text-gray-600">
                {details.year} • {details.authors.join(', ')}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Excerpt
              </h4>
              <div className="mt-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700 italic">
                  "{details.chunk_text}"
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Citation IDs
              </h4>
              <div className="mt-2 space-y-1 text-xs text-gray-500 font-mono">
                <p>Publication: {details.pub_id}</p>
                <p>Chunk: {details.chunk_id}</p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">No citation details available</p>
        )}
      </div>
    </div>
  );
};
