import React, { useMemo, useState } from 'react'
import { ChevronDown, Download, FileText } from 'lucide-react'
import { t } from '../../i18n'

interface WorkspaceTableProps {
  caption: string
  headers: string[]
  rows: string[][]
  exportFilename?: string
}

export const WorkspaceTable: React.FC<WorkspaceTableProps> = ({
  caption,
  headers,
  rows,
  exportFilename = 'nrg-workspace-table.csv',
}) => {
  const [sortIndex, setSortIndex] = useState(0)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  const sortedRows = useMemo(
    () =>
      [...rows].sort((leftRow, rightRow) => {
        const left = leftRow[sortIndex] || ''
        const right = rightRow[sortIndex] || ''
        const comparison = left.localeCompare(right, 'en-IN', { numeric: true, sensitivity: 'base' })
        return sortDirection === 'asc' ? comparison : -comparison
      }),
    [rows, sortDirection, sortIndex],
  )

  function downloadCsv(filename: string, rows: Array<Record<string, unknown>>): void {
    if (!rows.length) return
    const hdrs = Object.keys(rows[0])
    const csv = [
      hdrs.join(','),
      ...rows.map((row) =>
        hdrs.map((header) => `"${String(row[header] ?? '').replace(/"/g, '""')}"`).join(','),
      ),
    ].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = window.document.createElement('a')
    anchor.href = url
    anchor.download = filename
    anchor.click()
    URL.revokeObjectURL(url)
  }

  function downloadTableCsv(name: string, hdrs: string[], sorted: string[][]): void {
    const records = sorted.map((row) =>
      hdrs.reduce<Record<string, string>>((record, header, index) => {
        record[header] = row[index] || ''
        return record
      }, {}),
    )
    downloadCsv(name, records)
  }

  function exportPdf(): void {
    window.print()
  }

  if (!rows.length) {
    return (
      <div className="rounded-2xl border border-dashed border-nrg-border bg-[var(--glass-bg)] p-6 text-sm text-nrg-muted">
        {t('productionWorkspace.common.noRows')}
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-nrg-border bg-[var(--nrg-surface)] shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-nrg-border bg-[var(--glass-bg)] px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">{caption}</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => downloadTableCsv(exportFilename, headers, sortedRows)}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-nrg-border bg-[var(--nrg-surface)] px-3 py-1.5 text-xs font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
          >
            <Download size={14} aria-hidden="true" />
            {t('productionWorkspace.common.exportCsv')}
          </button>
          <button
            type="button"
            onClick={exportPdf}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-nrg-border bg-[var(--nrg-surface)] px-3 py-1.5 text-xs font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
          >
            <FileText size={14} aria-hidden="true" />
            {t('productionWorkspace.common.exportPdf')}
          </button>
        </div>
      </div>
      <div className="space-y-3 border-t border-nrg-border/60 p-4 md:hidden" data-testid="workspace-table-cards">
        {sortedRows.map((row, rowIndex) => (
          <article
            key={`${row.join('|')}-card-${rowIndex}`}
            className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] p-4"
          >
            {headers.map((header, cellIndex) => (
              <div
                key={`${header}-${cellIndex}`}
                className="grid grid-cols-[minmax(6rem,0.8fr)_1fr] gap-3 border-b border-nrg-border/40 py-2 last:border-b-0"
              >
                <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">{header}</dt>
                <dd className="min-w-0 break-words text-sm font-medium text-nrg-text">
                  {row[cellIndex] || t('productionWorkspace.common.notAvailable')}
                </dd>
              </div>
            ))}
          </article>
        ))}
      </div>
      <div className="hidden max-w-full overflow-x-auto md:block">
        <table className="min-w-full text-left text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead className="bg-[var(--glass-bg)] text-xs uppercase tracking-[0.12em] text-nrg-muted">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={header}
                  scope="col"
                  className="border-b border-nrg-border px-4 py-3 font-semibold"
                  aria-sort={
                    sortIndex === index ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'
                  }
                >
                  <button
                    type="button"
                    onClick={() => {
                      if (sortIndex === index) {
                        setSortDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
                      } else {
                        setSortIndex(index)
                        setSortDirection('asc')
                      }
                    }}
                    className="inline-flex min-h-8 items-center gap-1 rounded-md text-left transition hover:text-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
                    aria-label={t('productionWorkspace.common.sortBy', { header })}
                  >
                    {header}
                    {sortIndex === index && (
                      <ChevronDown
                        size={12}
                        className={`transition-transform ${sortDirection === 'asc' ? 'rotate-180' : ''}`}
                        aria-hidden="true"
                      />
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, rowIndex) => (
              <tr key={`${row.join('|')}-${rowIndex}`} className="hover:bg-saffron-500/5">
                {row.map((cell, cellIndex) => (
                  <td
                    key={`${cell}-${cellIndex}`}
                    className="border-b border-nrg-border/40 px-4 py-3 text-nrg-text"
                  >
                    {cell || t('productionWorkspace.common.notAvailable')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
