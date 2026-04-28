import React, { useEffect, useState } from 'react'
import { AtomIcon, Building2Icon, BuildingIcon, LogInIcon, UserIcon } from './Icons'
import { t } from '../i18n'

type PersonaKey = 'researcher' | 'government' | 'industry'

const PERSONA_LABELS: Record<PersonaKey, { en: string; hi: string; tier: string; desc: string }> = {
  researcher: {
    en: 'Researcher',
    hi: 'अनुसंधानकर्ता',
    tier: 'Tier 1',
    desc: 'Access publications, citations, and knowledge graphs across national research databases.'
  },
  government: {
    en: 'Government',
    hi: 'सरकार',
    tier: 'Tier 2',
    desc: 'Aggregate analytics, policy insights, and cross-institutional research trends.'
  },
  industry: {
    en: 'Industry',
    hi: 'उद्योग',
    tier: 'Tier 3',
    desc: 'Discover academic partnerships, anonymized research capacity, and R&D collaboration.'
  },
}

const PERSONA_CREDENTIALS: Record<PersonaKey, { username: string; password: string; accent: string }> = {
  researcher: {
    username: 'researcher@iitgn.ac.in',
    password: 'Researcher@2026',
    accent: 'var(--nrg-chart-5)',
  },
  government: {
    username: 'ministry@nrg.gov.in',
    password: 'Ministry@2026',
    accent: 'var(--nrg-chart-2)',
  },
  industry: {
    username: 'partner@industry.in',
    password: 'Industry@2026',
    accent: 'var(--nrg-chart-3)',
  },
}

const PERSONA_ICON: Record<PersonaKey, React.FC<React.SVGProps<SVGSVGElement>>> = {
  researcher: AtomIcon,
  government: BuildingIcon,
  industry: Building2Icon,
}

const PLATFORM_METRICS = [
  { label: 'Researchers', value: '50,000' },
  { label: 'Publications', value: '50,000' },
  { label: 'Institutions', value: '181' },
  { label: 'Grant Corpus', value: '₹274Cr' },
]

const TRUST_MARKERS = [
  'DPDP controls active',
  'Audit chain valid',
  'Tier-shaped responses',
]

interface LoginProps {
  onLogin: (username: string, password: string) => Promise<boolean>
  error?: string | null
  backendAvailable?: boolean
}

const AshokaLogo: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 60 60" className={className} aria-hidden="true">
    <circle cx="30" cy="30" r="28" fill="none" stroke="var(--nrg-chart-1)" strokeWidth="1.5" opacity="0.4"/>
    <circle cx="30" cy="30" r="20" fill="none" stroke="var(--nrg-chart-1)" strokeWidth="1" opacity="0.3"/>
    <circle cx="30" cy="30" r="12" fill="none" stroke="var(--nrg-chart-1)" strokeWidth="0.75" opacity="0.2"/>
    {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((angle) => {
      const rad = (angle * Math.PI) / 180
      const x1 = 30 + 12 * Math.cos(rad)
      const y1 = 30 + 12 * Math.sin(rad)
      const x2 = 30 + 28 * Math.cos(rad)
      const y2 = 30 + 28 * Math.sin(rad)
      return <line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--nrg-chart-1)" strokeWidth="0.75" opacity="0.35"/>
    })}
    {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => {
      const rad = (angle * Math.PI) / 180
      const x1 = 30 + 20 * Math.cos(rad)
      const y1 = 30 + 20 * Math.sin(rad)
      const x2 = 30 + 28 * Math.cos(rad)
      const y2 = 30 + 28 * Math.sin(rad)
      return <line key={`diagonal-${angle}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--nrg-chart-4)" strokeWidth="0.5" opacity="0.3"/>
    })}
  </svg>
)

const Login: React.FC<LoginProps> = ({ onLogin, error, backendAvailable = true }) => {
  const [selectedPersona, setSelectedPersona] = useState<PersonaKey>('researcher')
  const [username, setUsername] = useState('researcher@iitgn.ac.in')
  const [password, setPassword] = useState('Researcher@2026')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [focusedField, setFocusedField] = useState<'username' | 'password' | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})
  const [localMessage, setLocalMessage] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'NRG · Sign In'
  }, [])

  const applyPersona = (persona: PersonaKey) => {
    setSelectedPersona(persona)
    setUsername(PERSONA_CREDENTIALS[persona].username)
    setPassword(PERSONA_CREDENTIALS[persona].password)
    setFieldErrors({})
    setLocalMessage(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const nextErrors: { username?: string; password?: string } = {}
    if (!username.trim()) nextErrors.username = 'Enter your email'
    if (!password.trim()) nextErrors.password = 'Enter your password'
    setFieldErrors(nextErrors)
    setLocalMessage(null)
    if (Object.keys(nextErrors).length > 0) return

    setIsLoading(true)
    try {
      await onLogin(username, password)
    } finally {
      setIsLoading(false)
    }
  }

  const accentColor = PERSONA_CREDENTIALS[selectedPersona].accent

  return (
    <div className="min-h-screen bg-[#f7f8f4] text-slate-950">
      {!backendAvailable && (
        <div className="w-full bg-red-700 text-white text-center py-2 px-4 text-sm font-medium flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {t("auto.components.Login.1")}
        </div>
      )}
      {error && (
        <div className="w-full bg-red-50 border-b border-red-200 text-red-700 text-center py-2 px-4 text-sm">
          {error}
        </div>
      )}

      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-5 py-5 sm:px-8 lg:px-10">
          <header className="flex flex-col gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="relative h-14 w-14 shrink-0">
                <AshokaLogo className="h-14 w-14" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-sm font-bold text-[#ff8b4a]">
                    न
                  </div>
                </div>
              </div>
              <div>
                <p className="font-devanagari text-xl font-bold leading-tight text-slate-950">राष्ट्रीय गवेषण मंच</p>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">National Research Graph</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-600">
              {TRUST_MARKERS.map((marker) => (
                <span key={marker} className="rounded-full border border-slate-200 bg-white px-3 py-1 shadow-sm">
                  {marker}
                </span>
              ))}
            </div>
          </header>

          <section className="grid flex-1 gap-6 py-6 lg:grid-cols-[minmax(0,1fr)_420px] lg:items-stretch">
            <div className="flex min-w-0 flex-col gap-6">
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:p-8">
                <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-600">
                  <span className="h-2 w-2 rounded-full bg-emerald-600" />
                  Sovereign research intelligence console
                </div>
                <h2 className="max-w-4xl text-3xl font-bold leading-tight text-slate-950 sm:text-4xl lg:text-5xl">
                  Verified research, funding, patent, and readiness intelligence in one controlled workspace.
                </h2>
                <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
                  Role-bound access for researchers, government reviewers, and industry partners. Every response is shaped by tier policy and tied to audit evidence.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                {PLATFORM_METRICS.map((metric) => (
                  <div key={metric.label} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                    <p className="text-2xl font-bold text-slate-950">{metric.value}</p>
                    <p className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{metric.label}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                {(['researcher', 'government', 'industry'] as PersonaKey[]).map((key) => {
                  const isActive = selectedPersona === key
                  const info = PERSONA_LABELS[key]
                  const creds = PERSONA_CREDENTIALS[key]
                  const PersonaIcon = PERSONA_ICON[key]
                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => applyPersona(key)}
                      disabled={isLoading}
                      aria-label={`Select ${info.en} persona`}
                      aria-pressed={isActive}
                      data-testid={`persona-${key}`}
                      className={`
                        rounded-lg border bg-white p-4 text-left shadow-sm transition
                        ${isActive ? 'border-slate-950 ring-2 ring-slate-950/10' : 'border-slate-200 hover:border-slate-400'}
                      `}
                    >
                      <div className="mb-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="flex h-9 w-9 items-center justify-center rounded-md" style={{ background: `${creds.accent}18`, color: creds.accent }}>
                            <PersonaIcon className="h-4 w-4" />
                          </span>
                          <span className="font-semibold text-slate-950">{info.en}</span>
                        </div>
                        <span className="rounded-full bg-slate-100 px-2 py-1 font-mono text-[11px] text-slate-500">{info.tier}</span>
                      </div>
                      <p className="text-sm leading-6 text-slate-600">{info.desc}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:p-7">
              <div className="mb-6 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-950 text-white">
                  <LogInIcon className="h-5 w-5" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-950">Sign in</h1>
                  <p className="text-sm text-slate-500">Access is bound to your selected tier.</p>
                </div>
              </div>

              <div className="mb-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-950">
                    {PERSONA_LABELS[selectedPersona].hi}
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="text-sm text-slate-600">{PERSONA_LABELS[selectedPersona].en}</span>
                  <span className="ml-auto rounded-full bg-white px-2 py-1 font-mono text-[11px] text-slate-500">
                    {PERSONA_LABELS[selectedPersona].tier}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  Current workspace credentials are pre-filled for this role.
                </p>
              </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="block text-sm font-medium text-slate-900 mb-2">Email</span>
              <div className="relative">
                <div
                  className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-200"
                  style={{ color: focusedField === 'username' ? accentColor : 'var(--nrg-muted)' }}
                >
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  data-testid="login-username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value)
                    setFieldErrors((prev) => ({ ...prev, username: undefined }))
                  }}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11"
                  autoComplete="username"
                  placeholder="you@institution.ac.in"
                  aria-invalid={Boolean(fieldErrors.username)}
                  aria-describedby={fieldErrors.username ? 'username-error' : undefined}
                  style={{ borderColor: focusedField === 'username' ? accentColor : undefined }}
                />
              </div>
              {fieldErrors.username && (
                <p id="username-error" className="mt-1 text-xs text-rose-600">{fieldErrors.username}</p>
              )}
            </label>

            <label className="block">
              <span className="block text-sm font-medium text-slate-900 mb-2">{t("auto.components.Login.13")}</span>
              <div className="relative">
                <div
                  className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-200"
                  style={{ color: focusedField === 'password' ? accentColor : 'var(--nrg-muted)' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  data-testid="login-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setFieldErrors((prev) => ({ ...prev, password: undefined }))
                  }}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11 pr-20"
                  autoComplete="current-password"
                  placeholder={t("auto.components.Login.14")}
                  aria-invalid={Boolean(fieldErrors.password)}
                  aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                  style={{ borderColor: focusedField === 'password' ? accentColor : undefined }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-3 top-1/2 min-h-9 -translate-y-1/2 rounded-md px-2 text-xs font-semibold text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {fieldErrors.password && (
                <p id="password-error" className="mt-1 text-xs text-rose-600">{fieldErrors.password}</p>
              )}
            </label>

            {(localMessage || error) ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {localMessage || error}
              </div>
            ) : null}

            <button
              type="submit"
              data-testid="login-submit"
              disabled={isLoading}
              aria-busy={isLoading}
              className="nrg-btn-primary w-full text-base py-3"
            >
              {isLoading ? (
                  <span className="flex items-center gap-2">
                  <span className="nrg-ashoka-spinner nrg-ashoka-spinner--sm" />
                  Signing you in...</span>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-200 text-center">
            <button
              type="button"
              onClick={() => setLocalMessage('Please contact the NRG administrator to reset your password.')}
              className="mb-3 text-sm font-medium text-slate-700 hover:text-slate-950 transition-colors"
            >
              {t("auto.components.Login.16")}</button>
            <p className="text-xs text-slate-500">
              Kong Gateway · JWT RS256 · HMAC audit binding
            </p>
          </div>
            </aside>
          </section>

          <footer className="border-t border-slate-200 py-4 text-xs text-slate-500">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span>Gov of India · DST · IIT Gandhinagar</span>
              <span>Frontend local preview · API health checked separately</span>
            </div>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default Login
