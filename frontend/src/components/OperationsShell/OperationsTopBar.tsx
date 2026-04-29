import React from 'react'
import type { PersonaRole } from '../../services/authService'
import PersonaToggle from '../PersonaToggle'

interface OperationsTopBarProps {
  role: PersonaRole
  onLogout: () => void
}

const TOP_BAR_COPY = {
  eyebrow: 'Sovereign Operations Console',
  accessBoundarySuffix: 'access boundary active',
  logout: 'Logout',
}

export function OperationsTopBar({ role, onLogout }: OperationsTopBarProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-nrg-border bg-[color-mix(in_srgb,var(--nrg-bg)_95%,transparent)] px-4 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">{TOP_BAR_COPY.eyebrow}</p>
          <p className="text-sm font-semibold capitalize text-nrg-text">
            {role} {TOP_BAR_COPY.accessBoundarySuffix}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <PersonaToggle />
          <button
            type="button"
            data-testid="logout-button"
            onClick={onLogout}
            className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          >
            {TOP_BAR_COPY.logout}
          </button>
        </div>
      </div>
    </header>
  )
}

export default OperationsTopBar
