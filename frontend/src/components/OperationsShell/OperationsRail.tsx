import React from 'react'
import type { PersonaRole } from '../../services/authService'

interface OperationsRailProps {
  role: PersonaRole
  username: string
}

const RAIL_COPY = {
  productDevanagari: 'राष्ट्रीय गवेषण मंच',
  productName: 'National Research Graph',
  signedInAs: 'Signed in as',
  auditHealthTitle: 'Audit chain healthy',
  auditHealthBody: 'Answer proof is available in the inspector.',
  navigationLabel: 'Critical path navigation',
}

const NAV_ITEMS = [
  { href: '/app', label: 'Ask' },
  { href: '/app/publications', label: 'Publications' },
  { href: '/app/audit', label: 'Audit' },
  { href: '/app/settings', label: 'Settings' },
]

export function OperationsRail({ role, username }: OperationsRailProps) {
  return (
    <aside className="border-r border-nrg-border bg-[var(--nrg-surface)] px-4 py-5 lg:min-h-screen">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-950 text-sm font-bold text-[var(--nrg-saffron-400)]">
          न
        </div>
        <div>
          <p className="font-devanagari text-base font-bold text-nrg-text">{RAIL_COPY.productDevanagari}</p>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-nrg-muted">{RAIL_COPY.productName}</p>
        </div>
      </div>
      <div className="mt-6 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">{RAIL_COPY.signedInAs}</p>
        <p className="mt-1 text-sm font-semibold capitalize text-nrg-text">{role}</p>
        <p className="mt-1 truncate text-xs text-nrg-muted">{username}</p>
      </div>
      <nav className="mt-6 grid gap-1" aria-label={RAIL_COPY.navigationLabel}>
        {NAV_ITEMS.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm font-medium text-nrg-muted transition hover:bg-[var(--nrg-surface-2)] hover:text-nrg-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--nrg-focus)]"
          >
            {item.label}
          </a>
        ))}
      </nav>
      <div className="mt-6 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-nrg-muted">
        <span className="font-semibold text-emerald-700">{RAIL_COPY.auditHealthTitle}</span>
        <span className="mt-1 block">{RAIL_COPY.auditHealthBody}</span>
      </div>
    </aside>
  )
}

export default OperationsRail
