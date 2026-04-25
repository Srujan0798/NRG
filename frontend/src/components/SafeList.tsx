import React, { ReactNode } from 'react'
import { toStringArray } from '../types/api'
import { t } from '../i18n'

interface SafeListProps<T> {
  value: T extends string ? string : T extends string[] ? string[] : T extends (string | string[]) ? string | string[] | null | undefined : T
  renderItem: (item: string, index: number) => ReactNode
  keyExtractor?: (item: string, index: number) => string
  separator?: ReactNode
  fallback?: ReactNode
  className?: string
  emptyClassName?: string
}

function isListish(value: unknown): value is string | string[] | null | undefined {
  if (value == null) return false
  if (typeof value === 'string') return true
  if (Array.isArray(value)) return true
  return false
}

export function SafeList<T>({
  value,
  renderItem,
  keyExtractor = (item, i) => item ?? String(i),
  separator,
  fallback = null,
  className,
  emptyClassName,
}: SafeListProps<T>): ReactNode {
  if (!isListish(value)) return fallback

  const items = toStringArray(value as string | string[] | null | undefined)

  if (items.length === 0) {
    return emptyClassName ? <div className={emptyClassName}>{fallback}</div> : fallback
  }

  const rendered = items.map((item, index) => (
    <React.Fragment key={keyExtractor(item, index)}>
      {renderItem(item, index)}
      {separator && index < items.length - 1 && separator}
    </React.Fragment>
  ))

  return className ? <div className={className}>{rendered}</div> : rendered
}

interface SafeAuthorsProps {
  authors: string | string[] | null | undefined
  renderAvatar?: (name: string, index: number) => ReactNode
  maxDisplay?: number
  fallback?: ReactNode
  separator?: string
}

export function SafeAuthors({
  authors,
  maxDisplay,
  fallback = null,
  separator = ', ',
}: SafeAuthorsProps): ReactNode {
  const items = toStringArray(authors)
  if (items.length === 0) return fallback

  const display = maxDisplay ? items.slice(0, maxDisplay) : items
  const remaining = items.length - display.length

  return (
    <>
      {display.map((name, i) => (
        <span key={name ?? String(i)}>
          {i > 0 && <span className="mx-0.5 opacity-50">{separator}</span>}
          {name.trim()}
        </span>
      ))}
      {remaining > 0 && (
        <span className="text-slate-400 dark:text-slate-500"> +{remaining} {t("auto.components.SafeList.1")}</span>
      )}
    </>
  )
}