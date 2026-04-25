import React, { useEffect, useState } from 'react'
import { LogInIcon, UserIcon } from './Icons'

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
    username: 'researcher_user',
    password: 'researcher-pass',
    accent: 'var(--nrg-chart-5)',
  },
  government: {
    username: 'gov_user',
    password: 'government-pass',
    accent: 'var(--nrg-chart-2)',
  },
  industry: {
    username: 'industry_user',
    password: 'industry-pass',
    accent: 'var(--nrg-chart-3)',
  },
}

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
  const [username, setUsername] = useState('researcher_user')
  const [password, setPassword] = useState('researcher-pass')
  const [isLoading, setIsLoading] = useState(false)
  const [focusedField, setFocusedField] = useState<'username' | 'password' | null>(null)
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({})
  const [localMessage, setLocalMessage] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'Sign In | National Research Graph'
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
    if (!username.trim()) nextErrors.username = 'Enter your username'
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
    <div className="nrg-app-canvas min-h-screen">
      {/* Backend unavailable banner */}
      {!backendAvailable && (
        <div className="w-full bg-red-600 text-white text-center py-2 px-4 text-sm font-medium flex items-center justify-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Backend server unreachable — check your connection or API server status
        </div>
      )}
      {error && (
        <div className="w-full bg-red-600/10 border-b border-red-600/30 text-red-400 text-center py-2 px-4 text-sm">
          {error}
        </div>
      )}
      <div className="flex min-h-screen flex-col lg:flex-row">
        {/* Left Panel — Branding */}
        <div className="relative flex-1 flex flex-col justify-between p-6 sm:p-10 lg:p-16 overflow-hidden min-w-0 lg:min-w-[28.125rem] bg-[var(--nrg-founder-ink)] text-white lg:rounded-r-[2rem] shadow-2xl">
        <div className="absolute inset-0 pointer-events-none">
          <svg className="absolute inset-0 w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--nrg-white)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-10 lg:mb-12">
            <div className="relative">
              <AshokaLogo className="w-14 h-14 animate-spin-slow" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 rounded-full bg-nrg-navy-900 flex items-center justify-center">
                  <span className="text-nrg-saffron-400 font-bold font-display text-sm">न</span>
                </div>
              </div>
            </div>
            <div>
                <h1 className="text-2xl font-bold text-white font-devanagari tracking-wide">
                  राष्ट्रीय गवेषण मंच
                </h1>
              <p className="text-slate-300 text-sm tracking-widest uppercase">National Research Graph</p>
            </div>
          </div>

          <div className="mb-8 lg:mb-10">
              <h2 className="text-4xl lg:text-5xl font-display font-bold text-white leading-tight mb-4">
                Sovereign Intelligence<br />
                <span className="text-nrg-saffron-400">for India's Research</span>
              </h2>
            <p className="text-slate-300 text-lg max-w-lg leading-relaxed">
              A secure, AI-powered platform connecting 5,615 researchers, 12,000 publications, and 181 institutions — engineered for government, academia, and industry.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:gap-4">
            {(['researcher', 'government', 'industry'] as PersonaKey[]).map((key) => {
              const isActive = selectedPersona === key
              const info = PERSONA_LABELS[key]
              const creds = PERSONA_CREDENTIALS[key]
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => applyPersona(key)}
                  className={`
                    relative min-h-[8.25rem] rounded-xl p-4 text-left transition-all duration-300 border overflow-hidden
                    ${isActive
                      ? 'border-2 shadow-xl bg-white/10'
                      : 'border-white/10 bg-white/[0.06] hover:border-white/25 hover:bg-white/[0.1]'
                    }
                  `}
                  style={isActive ? { borderColor: creds.accent } : {}}
                >
                  {isActive && (
                    <div className="absolute inset-0 rounded-xl" style={{ background: `${creds.accent}24` }} />
                  )}
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="w-6 h-6 rounded-full flex items-center justify-center"
                      style={{ background: isActive ? creds.accent : 'rgba(255,255,255,0.1)' }}
                    >
                      <span className="text-white text-xs">
                        {key === 'researcher' ? '🔬' : key === 'government' ? '🏛️' : '🏢'}
                      </span>
                    </div>
                    <span className="text-white font-semibold text-sm">{info.en}</span>
                    <span className="text-white/40 text-xs ml-auto font-mono">{info.tier}</span>
                  </div>
                  <p className="text-white/70 text-xs leading-relaxed line-clamp-3">{info.desc}</p>
                  {isActive && (
                    <div
                      className="absolute bottom-0 left-0 right-0 h-0.5 rounded-b-2xl"
                      style={{ background: creds.accent }}
                    />
                  )}
                </button>
              )
            })}
          </div>
        </div>

          <div className="relative z-10 mt-8 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-slate-300 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-nrg-ashoka-500 animate-pulse" />
              <span>Encrypted · Sovereign · DPDP-Compliant</span>
            </div>
          <span className="hidden sm:inline text-white/20">|</span>
          <span>Gov of India · DST · IIT Gandhinagar</span>
        </div>
      </div>

      {/* Right Panel — Login Form */}
        <div className="w-full lg:w-[31.25rem] bg-[var(--nrg-surface)]/95 backdrop-blur-xl border-l border-nrg-border flex flex-col justify-center p-6 sm:p-10 lg:p-16 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-nrg-saffron-500 via-nrg-gold-500 to-nrg-navy-400 opacity-70" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-8">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: `${accentColor}15` }}
            >
              <LogInIcon className="w-5 h-5" style={{ color: accentColor }} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-nrg-text">Sign in</h2>
              <p className="text-nrg-muted text-sm">Authenticate to access the platform</p>
            </div>
          </div>

          <div className="mb-8 p-4 rounded-xl bg-nrg-navy-50 border border-nrg-navy-100 dark:bg-navy-800 dark:border-navy-700">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold text-nrg-navy-700 dark:text-slate-100">
                {PERSONA_LABELS[selectedPersona].hi}
              </span>
              <span className="text-nrg-muted text-sm">·</span>
              <span className="text-sm text-nrg-muted">{PERSONA_LABELS[selectedPersona].en}</span>
            </div>
            <p className="text-xs text-nrg-muted">
              Authenticate with your seeded credentials for this workspace.
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="block text-sm font-medium text-nrg-text mb-2">Username</span>
              <div className="relative">
                <div
                  className="absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-200"
                  style={{ color: focusedField === 'username' ? accentColor : 'var(--nrg-muted)' }}
                >
                  <UserIcon className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value)
                    setFieldErrors((prev) => ({ ...prev, username: undefined }))
                  }}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11"
                  autoComplete="username"
                  placeholder="Enter username"
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
              <span className="block text-sm font-medium text-nrg-text mb-2">Password</span>
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
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setFieldErrors((prev) => ({ ...prev, password: undefined }))
                  }}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11"
                  autoComplete="current-password"
                  placeholder="Enter password"
                  aria-invalid={Boolean(fieldErrors.password)}
                  aria-describedby={fieldErrors.password ? 'password-error' : undefined}
                  style={{ borderColor: focusedField === 'password' ? accentColor : undefined }}
                />
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
              disabled={isLoading}
              className="nrg-btn-primary w-full text-base py-3"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="nrg-ashoka-spinner" style={{ width: 18, height: 18, borderWidth: 2 }} />
                  Authenticating...
                </span>
              ) : (
                `Continue as ${PERSONA_LABELS[selectedPersona].en}`
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-nrg-border text-center">
            <button
              type="button"
              onClick={() => setLocalMessage('Please contact the NRG administrator to reset your password.')}
              className="mb-3 text-sm font-medium text-nrg-navy-500 hover:text-nrg-saffron-500 transition-colors"
            >
              Forgot password?
            </button>
            <p className="text-xs text-nrg-muted">
              Secured by Kong API Gateway · JWT Bearer Tokens · RS256
            </p>
        </div>
      </div>
        </div>
      </div>
    </div>
  )
}

export default Login
