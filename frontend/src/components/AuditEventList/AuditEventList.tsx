import React from 'react'
import { List, RowComponentProps } from 'react-window'
import { AuditEventRecord } from '../../services/queryService'

interface AuditEventListProps {
  events: AuditEventRecord[]
  onSelect: (event: AuditEventRecord) => void
}

interface RowProps {
  events: AuditEventRecord[]
  onSelect: (event: AuditEventRecord) => void
}

const COPY = {
  empty: 'No audit events yet',
  verified: 'intact',
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return timestamp
  return date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
}

const AuditRow = ({ index, style, events, onSelect, ariaAttributes }: RowComponentProps<RowProps>) => {
  const event = events[index]
  if (!event) return null

  return (
    <div style={style} {...ariaAttributes} className="px-1 py-1">
      <button
        type="button"
        data-testid="audit-event-row"
        onClick={() => onSelect(event)}
        className="grid min-h-20 w-full gap-2 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-3 text-left transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)] sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_auto]"
      >
        <span>
          <span className="block text-sm font-semibold text-nrg-text">{event.action}</span>
          <span className="mt-1 block truncate font-mono text-xs text-nrg-muted">{event.hmac}</span>
        </span>
        <span className="text-xs text-nrg-muted">
          <span className="block font-semibold text-nrg-text">{event.actor || event.user_id || event.persona}</span>
          <span>{formatTime(event.timestamp)}</span>
        </span>
        <span className="self-start rounded-full border border-[var(--nrg-success)] bg-[var(--nrg-success-soft)] px-3 py-1 text-xs font-bold uppercase tracking-wider text-[var(--nrg-success)]">
          {event.integrity_status || COPY.verified}
        </span>
      </button>
    </div>
  )
}

export const AuditEventList: React.FC<AuditEventListProps> = ({ events, onSelect }) => {
  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-nrg-border bg-[var(--nrg-surface-1)] p-8 text-center text-sm text-nrg-muted">
        {COPY.empty}
      </div>
    )
  }

  return (
    <div data-testid="audit-event-list" data-virtualized="react-window" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface)] p-2">
      <List
        rowCount={events.length}
        rowHeight={96}
        rowProps={{ events, onSelect }}
        rowComponent={AuditRow}
        overscanCount={6}
        style={{ height: 'min(38rem, 68vh)', width: '100%' }}
      />
    </div>
  )
}

export default AuditEventList
