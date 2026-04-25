import React, { useState, useMemo } from 'react'
import { t } from '../../../i18n'

interface TabularViewProps {
  headers: string[]
  rows: string[][]
  sortable?: boolean
  paginated?: boolean
}

export const TabularView: React.FC<TabularViewProps> = ({ 
  headers, 
  rows, 
  sortable = false,
  paginated = false 
}) => {
  const [sortColumn, setSortColumn] = useState<number | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(0)
  const pageSize = 10

  const sortedRows = useMemo(() => {
    if (sortColumn === null) return rows
    return [...rows].sort((a, b) => {
      const aVal = a[sortColumn] || ''
      const bVal = b[sortColumn] || ''
      const cmp = aVal.localeCompare(bVal, undefined, { numeric: true })
      return sortDirection === 'asc' ? cmp : -cmp
    })
  }, [rows, sortColumn, sortDirection])

  const paginatedRows = paginated 
    ? sortedRows.slice(page * pageSize, (page + 1) * pageSize)
    : sortedRows
  const totalPages = Math.ceil(sortedRows.length / pageSize)

  const handleSort = (colIndex: number) => {
    if (!sortable) return
    if (sortColumn === colIndex) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(colIndex)
      setSortDirection('asc')
    }
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-xl border border-nrg-border">
        <table className="min-w-full text-sm">
          <thead className="bg-nrg-navy-50">
            <tr>
              {headers.map((h, i) => (
                <th 
                  key={i} 
                  className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-nrg-muted border-b border-nrg-border ${
                    sortable ? 'cursor-pointer hover:bg-nrg-navy-100 transition-colors' : ''
                  }`}
                  onClick={() => handleSort(i)}
                >
                  <div className="flex items-center gap-2">
                    {h}
                    {sortable && sortColumn === i && (
                      <span className="text-saffron-500">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.map((row, ri) => (
              <tr key={ri} className="hover:bg-nrg-navy-50/50 transition-colors">
                {row.map((cell, ci) => (
                  <td key={ci} className="px-4 py-3 text-sm text-nrg-text border-b border-nrg-border/50">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {paginated && totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-nrg-muted">
          <span>{t("auto.components.IntelligenceBrief.components.TabularView.1")}{page * pageSize + 1}-{Math.min((page + 1) * pageSize, sortedRows.length)} of {sortedRows.length}</span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-2 py-1 rounded border border-nrg-border hover:bg-nrg-navy-50 disabled:opacity-50"
            >
              {t("auto.components.IntelligenceBrief.components.TabularView.2")}</button>
            <span className="px-2 py-1">{t("auto.components.IntelligenceBrief.components.TabularView.3")}{page + 1}/{totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="px-2 py-1 rounded border border-nrg-border hover:bg-nrg-navy-50 disabled:opacity-50"
            >
              {t("auto.components.IntelligenceBrief.components.TabularView.4")}</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default TabularView