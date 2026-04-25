import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronDown, Download, Users } from 'lucide-react'

interface DataTableProps {
  title: string
  titleHi: string
  columns: { key: string; label: string; align?: 'left' | 'right' }[]
  data: Record<string, any>[]
  pageSize?: number
}

export const DataTable: React.FC<DataTableProps> = ({
  title,
  titleHi,
  columns,
  data,
  pageSize = 10,
}) => {
  const [page, setPage] = useState(0)
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const sortedData = [...data].sort((a, b) => {
    if (!sortKey) return 0
    const aVal = a[sortKey]
    const bVal = b[sortKey]
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDir === 'asc' ? aVal - bVal : bVal - aVal
    }
    return sortDir === 'asc'
      ? String(aVal).localeCompare(String(bVal))
      : String(bVal).localeCompare(String(aVal))
  })

  const paginatedData = sortedData.slice(page * pageSize, (page + 1) * pageSize)
  const totalPages = Math.ceil(data.length / pageSize)

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  return (
    <motion.div
      className="rounded-2xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-700 shadow-md overflow-hidden"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="px-5 py-4 bg-slate-50 dark:bg-navy-700/50 border-b border-slate-200 dark:border-navy-700 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
          <p className="text-xs font-devanagari text-slate-500 dark:text-slate-400">{titleHi}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Showing {paginatedData.length} of {data.length}
          </span>
          <button className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-navy-600 text-slate-400">
            <Download size={14} />
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-navy-700/30">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={`px-5 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-navy-700 ${
                    col.align === 'right' ? 'text-right' : 'text-left'
                  }`}
                >
                  <button
                    onClick={() => handleSort(col.key)}
                    className="flex items-center gap-1 hover:text-saffron-500 transition-colors"
                  >
                    {col.label}
                    {sortKey === col.key && (
                      <ChevronDown
                        size={12}
                        className={`transition-transform ${sortDir === 'asc' ? 'rotate-180' : ''}`}
                      />
                    )}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, i) => (
              <motion.tr
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.03 }}
                className="border-b border-slate-100 dark:border-navy-700/50 hover:bg-saffron-50/50 dark:hover:bg-navy-700/30 transition-colors"
              >
                {columns.map(col => (
                  <td
                    key={col.key}
                    className={`px-5 py-3 text-sm text-slate-700 dark:text-slate-300 ${
                      col.align === 'right' ? 'text-right font-mono' : ''
                    }`}
                  >
                    {col.align === 'right'
                      ? typeof row[col.key] === 'number'
                        ? row[col.key].toLocaleString('en-IN')
                        : row[col.key]
                      : row[col.key]}
                  </td>
                ))}
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-5 py-3 bg-slate-50 dark:bg-navy-700/50 border-t border-slate-200 dark:border-navy-700 flex items-center justify-between">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-navy-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-200 dark:border-navy-600 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </motion.div>
  )
}

interface ResearcherTableProps {
  title?: string
  titleHi?: string
  researchers: {
    id: string
    name: string
    institution: string
    area: string
    publications: number
    citations: number
    hIndex: number
  }[]
}

export const AnonymizedResearcherTable: React.FC<ResearcherTableProps> = ({
  title = 'Researcher Network',
  titleHi = 'शोधकर्ता नेटवर्क',
  researchers,
}) => (
  <motion.div
    className="rounded-2xl bg-white dark:bg-navy-800 border border-slate-200 dark:border-navy-700 shadow-md overflow-hidden"
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
  >
    <div className="px-5 py-4 bg-slate-50 dark:bg-navy-700/50 border-b border-slate-200 dark:border-navy-700">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users size={16} className="text-saffron-600" />
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
            <p className="text-xs font-devanagari text-slate-500">{titleHi}</p>
          </div>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {researchers.length} researchers · anonymized
        </span>
      </div>
    </div>

    <div className="divide-y divide-slate-100 dark:divide-navy-700/50">
      {researchers.map((r, i) => (
        <motion.div
          key={r.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className="px-5 py-3 flex items-center gap-4 hover:bg-slate-50 dark:hover:bg-navy-700/30 transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-saffron-100 dark:bg-saffron-900/30 text-saffron-600 dark:text-saffron-400 flex items-center justify-center text-xs font-bold">
            {r.name[0]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
              Researcher {r.name}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
              {r.institution} · {r.area}
            </p>
          </div>
          <div className="flex items-center gap-6 text-xs">
            <div className="text-right">
              <p className="font-semibold text-slate-700 dark:text-slate-300">{r.publications}</p>
              <p className="text-slate-400">papers</p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-slate-700 dark:text-slate-300">{r.citations}</p>
              <p className="text-slate-400">citations</p>
            </div>
            <div className="text-right">
              <p className="font-semibold text-saffron-600 dark:text-saffron-400">h{r.hIndex}</p>
              <p className="text-slate-400">h-index</p>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  </motion.div>
)

export default DataTable
