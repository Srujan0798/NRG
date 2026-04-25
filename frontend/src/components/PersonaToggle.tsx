import React, { useState } from 'react'
import { authService, PersonaRole } from '../services/authService'
import { useAuth } from '../hooks/useAuth'

const PERSONAS: Array<{ role: PersonaRole; label: string; shortLabel: string; username: string; password: string; color: string }> = [
  { role: 'researcher', label: 'Researcher', shortLabel: 'R', username: 'researcher_user', password: 'researcher-pass', color: '#1E40AF' },
  { role: 'government', label: 'Government', shortLabel: 'G', username: 'gov_user', password: 'government-pass', color: '#065F46' },
  { role: 'industry', label: 'Industry', shortLabel: 'I', username: 'industry_user', password: 'industry-pass', color: '#7C2D12' },
]

export function PersonaToggle() {
  const { user, login } = useAuth()
  const [switchingRole, setSwitchingRole] = useState<PersonaRole | null>(null)
  const [switchError, setSwitchError] = useState<string | null>(null)

  const switchPersona = async (role: PersonaRole) => {
    if (role === user?.role || switchingRole) return
    const persona = PERSONAS.find((item) => item.role === role)
    if (!persona) return

    setSwitchingRole(role)
    setSwitchError(null)
    try {
      const switched = await login(persona.username, persona.password)
      if (!switched) {
        setSwitchError('Persona switch needs the API server.')
      }
    } catch {
      const currentSession = authService.getStoredSession()
      if (currentSession) {
        authService.saveSession({
          ...currentSession,
          user: {
            ...currentSession.user,
            role: persona.role,
            tier: persona.role === 'researcher' ? 1 : persona.role === 'government' ? 2 : 3,
            username: persona.username,
          },
        })
        window.location.reload()
      } else {
        setSwitchError('Persona switch needs an active session.')
      }
    } finally {
      setSwitchingRole(null)
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div
        role="tablist"
        aria-label="Switch demo persona"
        className="grid min-h-[40px] grid-cols-3 overflow-hidden rounded-full border border-nrg-border bg-[var(--nrg-surface)] p-1 shadow-sm"
      >
        {PERSONAS.map((persona) => {
          const active = user?.role === persona.role
          const switching = switchingRole === persona.role
          return (
            <button
              key={persona.role}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => void switchPersona(persona.role)}
              disabled={Boolean(switchingRole)}
              className={`min-h-[32px] min-w-[42px] rounded-full px-3 text-[11px] font-semibold uppercase tracking-[0.08em] transition sm:min-w-[112px] ${
                active
                  ? 'text-white shadow-sm'
                  : 'text-nrg-muted hover:bg-slate-100 hover:text-nrg-text dark:hover:bg-navy-700'
              } disabled:cursor-wait disabled:opacity-70`}
              style={active ? { background: persona.color } : undefined}
            >
              <span className="sm:hidden">{switching ? '...' : persona.shortLabel}</span>
              <span className="hidden sm:inline">{switching ? 'Switching...' : persona.label}</span>
            </button>
          )
        })}
      </div>
      {switchError && (
        <p className="max-w-[260px] text-right text-xs text-rose-600" role="status">
          {switchError}
        </p>
      )}
    </div>
  )
}

export default PersonaToggle
