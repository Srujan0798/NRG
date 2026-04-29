import React from 'react'
import type { PersonaRole } from '../../services/authService'
import { TierScopeBanner } from '../TierScopeBanner/TierScopeBanner'
import { OperationsRail } from './OperationsRail'
import { OperationsTopBar } from './OperationsTopBar'

interface OperationsShellProps {
  role: PersonaRole
  tier: number
  username: string
  onLogout: () => void
  inspector: React.ReactNode
  children: React.ReactNode
}

const SHELL_COPY = {
  proofInspectorLabel: 'Answer proof inspector',
}

export function OperationsShell({
  role,
  tier,
  username,
  onLogout,
  inspector,
  children,
}: OperationsShellProps) {
  return (
    <div
      data-testid="operations-shell"
      className="grid min-h-screen bg-[var(--nrg-bg)] text-nrg-text lg:grid-cols-[17rem_minmax(0,1fr)]"
    >
      <OperationsRail role={role} username={username} />
      <div className="min-w-0">
        <OperationsTopBar role={role} onLogout={onLogout} />
        <main id="main-content" tabIndex={-1} className="grid gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
          <div className="min-w-0 space-y-4">
            <TierScopeBanner role={role} tier={tier} />
            {children}
          </div>
          <aside className="min-w-0" aria-label={SHELL_COPY.proofInspectorLabel}>
            {inspector}
          </aside>
        </main>
      </div>
    </div>
  )
}

export default OperationsShell
