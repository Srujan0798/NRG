import React, { useState } from 'react'
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
    accent: '#6366f1',
  },
  government: {
    username: 'gov_user',
    password: 'government-pass',
    accent: '#2563eb',
  },
  industry: {
    username: 'industry_user',
    password: 'industry-pass',
    accent: '#10b981',
  },
}

interface LoginProps {
  onLogin: (username: string, password: string) => Promise<boolean>
  error?: string | null
  backendAvailable?: boolean
}

const AshokaLogo: React.FC<{ className?: string }> = ({ className }) => (
  <svg viewBox="0 0 60 60" className={className} aria-hidden="true">
    <circle cx="30" cy="30" r="28" fill="none" stroke="#ff6b35" strokeWidth="1.5" opacity="0.4"/>
    <circle cx="30" cy="30" r="20" fill="none" stroke="#ff6b35" strokeWidth="1" opacity="0.3"/>
    <circle cx="30" cy="30" r="12" fill="none" stroke="#ff6b35" strokeWidth="0.75" opacity="0.2"/>
    {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((angle) => {
      const rad = (angle * Math.PI) / 180
      const x1 = 30 + 12 * Math.cos(rad)
      const y1 = 30 + 12 * Math.sin(rad)
      const x2 = 30 + 28 * Math.cos(rad)
      const y2 = 30 + 28 * Math.sin(rad)
      return <line key={angle} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#ff6b35" strokeWidth="0.75" opacity="0.35"/>
    })}
    {[0, 45, 90, 135, 180, 225, 270, 315].map((angle) => {
      const rad = (angle * Math.PI) / 180
      const x1 = 30 + 20 * Math.cos(rad)
      const y1 = 30 + 20 * Math.sin(rad)
      const x2 = 30 + 28 * Math.cos(rad)
      const y2 = 30 + 28 * Math.sin(rad)
      return <line key={`diagonal-${angle}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#c49538" strokeWidth="0.5" opacity="0.3"/>
    })}
  </svg>
)

const Login: React.FC<LoginProps> = ({ onLogin, error, backendAvailable = true }) => {
  const [selectedPersona, setSelectedPersona] = useState<PersonaKey>('researcher')
  const [username, setUsername] = useState('researcher_user')
  const [password, setPassword] = useState('researcher-pass')
  const [isLoading, setIsLoading] = useState(false)
  const [focusedField, setFocusedField] = useState<'username' | 'password' | null>(null)

  const applyPersona = (persona: PersonaKey) => {
    setSelectedPersona(persona)
    setUsername(PERSONA_CREDENTIALS[persona].username)
    setPassword(PERSONA_CREDENTIALS[persona].password)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await onLogin(username, password)
    } finally {
      setIsLoading(false)
    }
  }

  const accentColor = PERSONA_CREDENTIALS[selectedPersona].accent

  return (
    <div className="min-h-screen bg-nrg-navy-900 flex flex-col lg:flex-row">
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
      {/* Left Panel — Branding */}
      <div className="relative flex-1 flex flex-col justify-between p-10 lg:p-16 overflow-hidden min-w-0 lg:min-w-[450px]">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 right-0 w-96 h-96 rounded-full bg-nrg-saffron-500/5 blur-3xl" />
          <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full bg-nrg-navy-400/10 blur-3xl" />
          <svg className="absolute inset-0 w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#ffffff" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-12">
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
              <p className="text-nrg-navy-200 text-sm tracking-widest uppercase">National Research Graph</p>
            </div>
          </div>

          <div className="mb-10">
            <h2 className="text-4xl lg:text-5xl font-display font-bold text-white leading-tight mb-4">
              Sovereign Intelligence<br />
              <span className="text-nrg-saffron-400">for India's Research</span>
            </h2>
            <p className="text-nrg-navy-200 text-lg max-w-lg leading-relaxed">
              A secure, AI-powered platform connecting 5,615 researchers, 12,000 publications, and 181 institutions — engineered for government, academia, and industry.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
                    relative rounded-2xl p-4 text-left transition-all duration-300 border overflow-hidden
                    ${isActive
                      ? 'border-2 shadow-xl'
                      : 'border-white/5 bg-white/5 hover:border-white/10 hover:bg-white/8'
                    }
                  `}
                  style={isActive ? { borderColor: creds.accent } : {}}
                >
                  {isActive && (
                    <div
                      className="absolute inset-0 opacity-5 rounded-2xl"
                      style={{ background: creds.accent }}
                    />
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
                  <p className="text-white/50 text-xs leading-relaxed line-clamp-2">{info.desc}</p>
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

        <div className="relative z-10 flex items-center gap-4 text-nrg-navy-300 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-nrg-ashoka-500 animate-pulse" />
            <span>Encrypted · Sovereign · DPDP-Compliant</span>
          </div>
          <span className="text-white/10">|</span>
          <span>Gov of India · DST · IIT Gandhinagar</span>
        </div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="w-full lg:w-[480px] bg-nrg-surface flex flex-col justify-center p-10 lg:p-16 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-96 h-96 rounded-full bg-nrg-saffron-500/3 blur-3xl" />
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

          <div className="mb-8 p-4 rounded-xl bg-nrg-navy-50 border border-nrg-navy-100">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold text-nrg-navy-700">
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
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11"
                  autoComplete="username"
                  style={{ borderColor: focusedField === 'username' ? accentColor : undefined }}
                />
              </div>
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
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  className="nrg-input pl-11"
                  autoComplete="current-password"
                  style={{ borderColor: focusedField === 'password' ? accentColor : undefined }}
                />
              </div>
            </label>

            {error ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 flex items-center gap-2">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                {error}
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
            <p className="text-xs text-nrg-muted">
              Secured by Kong API Gateway · JWT Bearer Tokens · RS256
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login