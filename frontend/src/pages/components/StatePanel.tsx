import React from 'react'
import { Lock } from 'lucide-react'
import { AuthUser } from '../../services/authService'
import { t } from '../../i18n'

interface StatePanelProps {
  status: 'idle' | 'loading' | 'loaded' | 'error'
  onRetry: () => void
  message?: string
}

export const StatePanel: React.FC<StatePanelProps> = ({ status, onRetry, message }) => {
  if (status === 'loaded') return null

  const isLoading = status === 'loading' || status === 'idle'
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] p-6" role="status" aria-busy="true">
        <p className="text-sm font-semibold text-nrg-text">{t('productionWorkspace.common.loading')}</p>
        <p className="mt-1 text-sm text-nrg-muted">{t('productionWorkspace.common.loadingBody')}</p>
        <div className="mt-5 space-y-3" aria-hidden="true">
          <div className="h-3 w-4/5 rounded-full bg-gradient-to-r from-slate-200 via-white to-slate-200 bg-[length:200%_100%] motion-safe:animate-pulse" />
          <div className="h-3 w-2/3 rounded-full bg-gradient-to-r from-slate-200 via-white to-slate-200 bg-[length:200%_100%] motion-safe:animate-pulse" />
          <div className="grid gap-3 md:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div key={item} className="h-16 rounded-xl border border-nrg-border bg-[var(--nrg-surface)]" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-nrg-border bg-[var(--glass-bg)] p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-nrg-text">{t('productionWorkspace.common.errorTitle')}</p>
          <p className="mt-1 text-sm text-nrg-muted">{message || t('productionWorkspace.common.errorBody')}</p>
        </div>
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-nrg-border bg-[var(--nrg-surface)] px-4 py-2 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)] focus:outline-none focus:ring-2 focus:ring-[var(--nrg-focus)]"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {t('productionWorkspace.common.retry')}
        </button>
      </div>
    </div>
  )
}

interface RestrictedPanelProps {
  user: AuthUser
  titleKey?: string
  bodyKey?: string
}

export const RestrictedPanel: React.FC<RestrictedPanelProps> = ({
  user,
  titleKey = 'productionWorkspace.researchers.restrictedTitle',
  bodyKey = 'productionWorkspace.researchers.restrictedBody',
}) => (
  <section className="rounded-3xl border border-nrg-border bg-[var(--nrg-surface)] p-8 shadow-sm">
    <div className="flex max-w-3xl flex-col gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--glass-bg)] text-nrg-text">
        <Lock size={22} aria-hidden="true" />
      </div>
      <div>
        <h2 className="text-2xl font-bold text-nrg-text">{t(titleKey)}</h2>
        <p className="mt-2 text-sm leading-6 text-nrg-muted">{t(bodyKey, { role: user.role })}</p>
      </div>
    </div>
  </section>
)
