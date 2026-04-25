import React from 'react'
import { QueryProvenance } from '../../../services/queryService'
import { t } from '../../../i18n'

interface ProvenanceBadgeProps {
  provenance?: QueryProvenance
  retrievalSources?: string[]
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ provenance, retrievalSources }) => {
  if (!provenance && !retrievalSources) return null

  const sourceType = (): { label: string; color: string; bg: string } => {
    if (!retrievalSources) return { label: 'Unknown', color: 'text-gray-700', bg: 'bg-gray-100' }
    
    const hasSQL = retrievalSources.some(s => s.toLowerCase().includes('sql') || s.toLowerCase().includes('table'))
    const hasRAG = retrievalSources.some(s => s.toLowerCase().includes('rag') || s.toLowerCase().includes('vector'))
    
    if (hasSQL && hasRAG) return { label: 'Hybrid', color: 'text-purple-700', bg: 'bg-purple-50 border-purple-200' }
    if (hasSQL) return { label: 'SQL', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' }
    if (hasRAG) return { label: 'RAG', color: 'text-green-700', bg: 'bg-green-50 border-green-200' }
    return { label: 'Unknown', color: 'text-gray-700', bg: 'bg-gray-100' }
  }

  const source = sourceType()

  return (
    <div className="flex flex-wrap gap-2">
      {provenance?.planner && (
        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-nrg-navy-50 text-nrg-navy-700 border border-nrg-navy-100">
          {provenance.planner} {t("auto.components.IntelligenceBrief.components.ProvenanceBadge.1")}</span>
      )}
      <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${source.bg} ${source.color}`}>
        {source.label}
      </span>
      <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
        provenance?.cloud_synthesis_used
          ? 'bg-amber-50 text-amber-700 border-amber-200'
          : 'bg-nrg-navy-50 text-nrg-navy-700 border-nrg-navy-100'
      }`}>
        {provenance?.cloud_synthesis_used ? '☁️ Cloud Synthesis' : '📴 Local Model'}
      </span>
      {provenance?.synth && (
        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
          {provenance.synth}
        </span>
      )}
    </div>
  )
}

export default ProvenanceBadge