import React, { useState, useRef, useCallback } from 'react'
import { authService, PersonaRole } from '../services/authService'
import { useAuth } from '../hooks/useAuth'
import { t } from '../i18n'
import PersonaSheet from './PersonaSheet/PersonaSheet'
import { emitTelemetry } from '../lib/telemetry'
import { useQueryStore } from '../stores/queryStore'

const PERSONAS: Array<{ role: PersonaRole; label: string; shortLabel: string; username: string; password: string; color: string }> = [
  { role: 'researcher', label: 'Researcher', shortLabel: 'R', username: 'researcher@iitgn.ac.in', password: 'Researcher@2026', color: 'var(--nrg-tier-1)' },
  { role: 'government', label: 'Government', shortLabel: 'G', username: 'ministry@nrg.gov.in', password: 'Ministry@2026', color: 'var(--nrg-tier-2)' },
  { role: 'industry', label: 'Industry', shortLabel: 'I', username: 'partner@industry.in', password: 'Industry@2026', color: 'var(--nrg-tier-3)' },
]

export function PersonaToggle() {
  const { user, login } = useAuth()
  const [switchingRole, setSwitchingRole] = useState<PersonaRole | null>(null)
  const [switchError, setSwitchError] = useState<string | null>(null)
  const tabListRef = useRef<HTMLDivElement>(null)

  const switchPersona = useCallback(async (role: PersonaRole) => {
    if (role === user?.role || switchingRole) return
    const persona = PERSONAS.find((item) => item.role === role)
    if (!persona) return
    const queryStore = useQueryStore.getState()

    emitTelemetry('persona.switched', {
      from: user?.role || 'anonymous',
      to: role,
      last_query_id: queryStore.history[0]?.id || null,
    })
    queryStore.switchPersona({
      from: user?.role || 'anonymous',
      to: role,
      lastQuery: queryStore.currentQuery || queryStore.history[0]?.query,
    })
    setSwitchingRole(role)
    setSwitchError(null)
    try {
      const switched = await login(persona.username, persona.password)
      if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        url.searchParams.set('persona', role)
        window.history.replaceState({}, '', url)
      }
      if (!switched) {
        await authService.switchPersona(role)
        window.location.reload()
      }
    } catch {
      await authService.switchPersona(role)
      window.location.reload()
    } finally {
      setSwitchingRole(null)
    }
  }, [login, switchingRole, user?.role])

  const handleTabKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    const currentIndex = PERSONAS.findIndex(p => p.role === user?.role)
    if (currentIndex === -1) return
    let nextIndex = currentIndex
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      nextIndex = (currentIndex + 1) % PERSONAS.length
      e.preventDefault()
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      nextIndex = (currentIndex - 1 + PERSONAS.length) % PERSONAS.length
      e.preventDefault()
    } else if (e.key === 'Home') {
      nextIndex = 0
      e.preventDefault()
    } else if (e.key === 'End') {
      nextIndex = PERSONAS.length - 1
      e.preventDefault()
    }
    if (nextIndex !== currentIndex) {
      const nextRole = PERSONAS[nextIndex].role
      const buttons = tabListRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')
      buttons?.[nextIndex]?.focus()
      void switchPersona(nextRole)
    }
  }, [switchPersona, user?.role])

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="w-full sm:hidden">
        <PersonaSheet
          personas={PERSONAS}
          activeRole={user?.role}
          switchingRole={switchingRole}
          switchError={switchError}
          onSwitch={switchPersona}
        />
      </div>
      <div
        ref={tabListRef}
        role="tablist"
        aria-label={t("auto.components.PersonaToggle.1")}
        className="hidden min-h-10 grid-cols-3 overflow-hidden rounded-full border border-nrg-border bg-[var(--nrg-surface)] p-1 shadow-sm sm:grid"
        onKeyDown={handleTabKeyDown}
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
              tabIndex={active ? 0 : -1}
              onClick={() => void switchPersona(persona.role)}
              disabled={Boolean(switchingRole)}
              className={`min-h-8 min-w-11 rounded-full px-3 text-[0.6875rem] font-semibold uppercase tracking-[0.08em] transition sm:min-w-28 ${
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
        <p className="max-w-64 text-right text-xs text-rose-600" role="status">
          {switchError}
        </p>
      )}
    </div>
  )
}

export default PersonaToggle
