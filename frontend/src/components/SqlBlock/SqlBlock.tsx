import React, { useMemo, useState } from 'react'
import { FileTextIcon } from '../Icons'
import { t } from '../../i18n'

interface SqlBlockProps {
  sql: string
}

const highlightSql = (sql: string) => {
  const keywords = new Set(['SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'DESC', 'ASC', 'LIMIT', 'SUM'])
  return sql.split(/(\s+|,|\(|\)|;)/).map((part, index) => {
    const upper = part.toUpperCase()
    if (keywords.has(upper)) {
      return (
        <span key={`${part}-${index}`} className="font-semibold text-[var(--nrg-focus)]">
          {part}
        </span>
      )
    }
    return <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>
  })
}

export const SqlBlock: React.FC<SqlBlockProps> = ({ sql }) => {
  const [copied, setCopied] = useState(false)
  const highlighted = useMemo(() => highlightSql(sql), [sql])

  if (!sql) {
    return (
      <div className="rounded-lg border border-dashed border-nrg-border bg-[var(--nrg-surface-2)] p-4 text-sm text-nrg-muted">
        {t("auto.components.SqlBlock.SqlBlock.1")}</div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-nrg-border bg-[var(--nrg-surface-2)]">
      <div className="flex items-center justify-between border-b border-nrg-border px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-nrg-text">
          <FileTextIcon className="h-4 w-4 text-[var(--nrg-focus)]" />
          {t("auto.components.SqlBlock.SqlBlock.2")}</div>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard?.writeText(sql)
            setCopied(true)
            window.setTimeout(() => setCopied(false), 1600)
          }}
          className="rounded-xl border border-nrg-border px-3 py-1.5 text-xs font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre
        tabIndex={0}
        aria-label={t("auto.components.SqlBlock.SqlBlock.3")}
        className="overflow-x-auto p-4 text-sm leading-6 text-nrg-text"
      >
        <code>{highlighted}</code>
      </pre>
    </div>
  )
}

export default SqlBlock
