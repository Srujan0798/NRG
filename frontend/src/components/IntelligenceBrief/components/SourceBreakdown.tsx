import React from 'react'
import { t } from '../../../i18n'

interface SourceBreakdownProps {
  sources?: string[]
}

export const SourceBreakdown: React.FC<SourceBreakdownProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null

  const categories = {
    SQL: sources.filter(s => s.toLowerCase().includes('sql') || s.toLowerCase().includes('table') || s.toLowerCase().includes('pg')).length,
    RAG: sources.filter(s => s.toLowerCase().includes('rag') || s.toLowerCase().includes('vector') || s.toLowerCase().includes('qdrant')).length,
    Hybrid: 0,
  }
  categories.Hybrid = Math.min(categories.SQL, categories.RAG)

  const total = categories.SQL + categories.RAG - categories.Hybrid || 1
  const sqlPct = Math.round((categories.SQL / total) * 100)
  const ragPct = Math.round((categories.RAG / total) * 100)

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1 h-2 rounded-full bg-blue-100 overflow-hidden flex">
          <div 
            className="h-full bg-blue-500 transition-all" 
            style={{ width: `${sqlPct}%` }} 
          />
          <div 
            className="h-full bg-green-500 transition-all" 
            style={{ width: `${ragPct}%` }} 
          />
        </div>
      </div>
      <div className="flex gap-4 text-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded bg-blue-500" />
          <span className="text-blue-700 font-medium">SQL {sqlPct}%</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded bg-green-500" />
          <span className="text-green-700 font-medium">RAG {ragPct}%</span>
        </div>
      </div>
      {sources.length > 0 && (
        <details className="group">
          <summary className="text-xs text-nrg-muted cursor-pointer hover:text-nrg-text">
            {t("auto.components.IntelligenceBrief.components.SourceBreakdown.1")}{sources.length} {t("auto.components.IntelligenceBrief.components.SourceBreakdown.2")}</summary>
          <div className="mt-2 p-2 rounded-lg bg-nrg-navy-50 border border-nrg-border">
            <ul className="space-y-1">
              {sources.map((source, i) => (
                <li key={i} className="text-xs text-nrg-muted font-mono">{source}</li>
              ))}
            </ul>
          </div>
        </details>
      )}
    </div>
  )
}

export default SourceBreakdown