import React from 'react'
import { ShieldAlert } from 'lucide-react'

interface PromptBlockedProps {
  reason?: string
  onEdit?: () => void
}

const COPY = {
  title: 'Sensitive query blocked',
  body: 'This query contains sensitive information that cannot be processed.',
  edit: 'Edit query',
}

export const PromptBlocked: React.FC<PromptBlockedProps> = ({ reason = COPY.body, onEdit }) => (
  <section
    data-testid="prompt-blocked"
    className="rounded-lg border border-[var(--nrg-danger)] bg-[var(--nrg-danger-soft)] p-4 text-sm text-nrg-text"
    role="status"
  >
    <div className="flex items-start gap-3">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--nrg-surface-1)] text-[var(--nrg-danger)]">
        <ShieldAlert size={18} aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="text-base font-bold text-nrg-text">{COPY.title}</h2>
        <p className="mt-1 leading-6 text-nrg-muted">{reason}</p>
        {onEdit && (
          <button
            type="button"
            onClick={onEdit}
            className="mt-3 min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-4 py-2 text-sm font-bold text-nrg-text"
          >
            {COPY.edit}
          </button>
        )}
      </div>
    </div>
  </section>
)

export default PromptBlocked
