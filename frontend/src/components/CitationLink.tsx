import React from 'react';
import type { Citation } from '../services/queryService';

interface CitationLinkProps {
  citation: Citation;
  index: number;
  onClick?: (citation: Citation) => void;
}

export function CitationLink({ citation, index, onClick }: CitationLinkProps) {
  const trustScore = citation.relevance_score ?? citation.enriched ? (citation.citation_count ? Math.min(citation.citation_count / 100, 1) : 0.5) : 0;

  const trustColor = trustScore >= 0.7 ? 'var(--nrg-chart-3)' : trustScore >= 0.4 ? 'var(--nrg-warning)' : 'var(--nrg-danger)';

  return (
    <button
      onClick={() => onClick?.(citation)}
      className="inline-flex items-center gap-1 mx-0.5 px-1 py-0.5 rounded text-saffron-600 dark:text-saffron-400 hover:bg-saffron-50 dark:hover:bg-saffron-900/30 transition-colors font-medium text-xs align-baseline"
      title={`${citation.title || citation.pub_id || 'Citation'} — Click for details`}
      data-testid={`citation-link-${index}`}
    >
      <span
        className="inline-flex items-center justify-center w-4 h-4 rounded-full text-white text-[0.625rem] font-bold shrink-0"
        style={{ background: trustColor }}
      >
        {index}
      </span>
      {citation.title && (
        <span className="hidden">{citation.title}</span>
      )}
    </button>
  );
}