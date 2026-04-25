import React, { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown, X } from 'lucide-react'
import { PersonaRole } from '../../services/authService'
import { t } from '../../i18n'

export interface PersonaSheetOption {
  role: PersonaRole
  label: string
  shortLabel: string
  color: string
}

interface PersonaSheetProps {
  personas: PersonaSheetOption[]
  activeRole?: PersonaRole
  switchingRole: PersonaRole | null
  switchError: string | null
  onSwitch: (role: PersonaRole) => void
}

export function PersonaSheet({
  personas,
  activeRole,
  switchingRole,
  switchError,
  onSwitch,
}: PersonaSheetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const activePersona = personas.find((persona) => persona.role === activeRole) ?? personas[0]

  useEffect(() => {
    if (!isOpen) return undefined

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  const handleSwitch = (role: PersonaRole) => {
    onSwitch(role)
    setIsOpen(false)
  }

  return (
    <div className="w-full">
      <button
        type="button"
        data-testid="mobile-persona-trigger"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        aria-label={t('auto.components.PersonaSheet.2')}
        onClick={() => setIsOpen(true)}
        className="flex min-h-11 w-full items-center justify-between gap-3 rounded-full border border-nrg-border bg-[var(--nrg-surface)] px-3 py-2 text-sm font-semibold text-nrg-text shadow-sm"
      >
        <span className="flex min-w-0 items-center gap-2">
          <span
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ background: activePersona.color }}
          >
            {activePersona.shortLabel}
          </span>
          <span className="truncate">{activePersona.label}</span>
        </span>
        <ChevronDown size={16} aria-hidden="true" className="shrink-0 text-nrg-muted" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.button
              type="button"
              aria-label={t('auto.components.PersonaSheet.4')}
              className="fixed inset-0 z-50 bg-black/40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label={t('auto.components.PersonaSheet.1')}
              className="fixed inset-x-0 bottom-0 z-50 max-h-[85vh] overflow-y-auto rounded-t-2xl border border-nrg-border bg-[var(--nrg-surface)] p-4 shadow-2xl"
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', stiffness: 360, damping: 34 }}
            >
              <div className="mb-4 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">
                    {t('auto.components.PersonaSheet.3')}
                  </p>
                  <h2 className="truncate text-lg font-semibold text-nrg-text">
                    {t('auto.components.PersonaSheet.1')}
                  </h2>
                </div>
                <button
                  type="button"
                  aria-label={t('auto.components.PersonaSheet.4')}
                  onClick={() => setIsOpen(false)}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-nrg-border text-nrg-muted transition hover:text-nrg-text"
                >
                  <X size={18} aria-hidden="true" />
                </button>
              </div>

              <div className="grid gap-2">
                {personas.map((persona) => {
                  const active = persona.role === activeRole
                  const switching = persona.role === switchingRole
                  return (
                    <button
                      key={persona.role}
                      type="button"
                      aria-current={active ? 'true' : undefined}
                      disabled={Boolean(switchingRole)}
                      onClick={() => handleSwitch(persona.role)}
                      className={`flex min-h-14 items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition ${
                        active
                          ? 'border-[var(--nrg-focus)] bg-[var(--nrg-focus-soft)] text-nrg-text'
                          : 'border-nrg-border bg-[var(--nrg-surface-1)] text-nrg-muted hover:text-nrg-text'
                      } disabled:cursor-wait disabled:opacity-70`}
                    >
                      <span className="flex min-w-0 items-center gap-3">
                        <span
                          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                          style={{ background: persona.color }}
                        >
                          {persona.shortLabel}
                        </span>
                        <span className="truncate text-sm font-semibold">{persona.label}</span>
                      </span>
                      <span className="text-xs font-semibold uppercase tracking-[0.08em] text-nrg-muted">
                        {switching ? t('auto.components.PersonaSheet.5') : active ? t('auto.components.PersonaSheet.6') : ''}
                      </span>
                    </button>
                  )
                })}
              </div>

              {switchError && (
                <p className="mt-3 rounded-lg border border-[var(--nrg-warning)] bg-[var(--nrg-warning-soft)] p-3 text-sm font-medium text-[var(--nrg-warning)]" role="status">
                  {switchError}
                </p>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PersonaSheet
