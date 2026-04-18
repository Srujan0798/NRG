import React, { useState } from 'react'
import { Building2Icon, BuildingIcon, LogInIcon, UserIcon } from './Icons'

type PersonaPreset = {
  label: string
  username: string
  password: string
  icon: React.ReactNode
}

const PERSONA_PRESETS: Record<'researcher' | 'government' | 'industry', PersonaPreset> = {
  researcher: {
    label: 'Researcher',
    username: 'researcher_user',
    password: 'researcher-demo-2026',
    icon: <UserIcon className="h-5 w-5" />
  },
  government: {
    label: 'Government',
    username: 'gov_user',
    password: 'government-demo-2026',
    icon: <Building2Icon className="h-5 w-5" />
  },
  industry: {
    label: 'Industry',
    username: 'industry_user',
    password: 'industry-demo-2026',
    icon: <BuildingIcon className="h-5 w-5" />
  }
}

interface LoginProps {
  onLogin: (username: string, password: string) => Promise<boolean>
  error?: string | null
}

const Login: React.FC<LoginProps> = ({ onLogin, error }) => {
  const [selectedPersona, setSelectedPersona] = useState<'researcher' | 'government' | 'industry'>('researcher')
  const [username, setUsername] = useState(PERSONA_PRESETS.researcher.username)
  const [password, setPassword] = useState(PERSONA_PRESETS.researcher.password)
  const [isLoading, setIsLoading] = useState(false)

  const applyPersona = (persona: 'researcher' | 'government' | 'industry') => {
    setSelectedPersona(persona)
    setUsername(PERSONA_PRESETS[persona].username)
    setPassword(PERSONA_PRESETS[persona].password)
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setIsLoading(true)
    try {
      await onLogin(username, password)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-12 text-white">
      <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.25),_transparent_35%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(30,41,59,0.94))] p-10 shadow-2xl">
          <p className="mb-4 text-sm uppercase tracking-[0.3em] text-cyan-300">National Research Graph</p>
          <h1 className="max-w-2xl text-4xl font-semibold leading-tight text-white">
            Kong-backed access for researchers, ministries, and industry partners.
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-slate-300">
            Each persona now signs in against the real JWT API, queries through Kong on port `8000`,
            and sees data scoped to its assigned access tier.
          </p>

          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {Object.entries(PERSONA_PRESETS).map(([persona, preset]) => {
              const isActive = selectedPersona === persona
              return (
                <button
                  key={persona}
                  type="button"
                  onClick={() => applyPersona(persona as keyof typeof PERSONA_PRESETS)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    isActive
                      ? 'border-cyan-300 bg-cyan-300/10 shadow-lg shadow-cyan-500/10'
                      : 'border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10'
                  }`}
                  aria-label={`Select ${preset.label} persona`}
                >
                  <div className="mb-3 flex items-center gap-3 text-cyan-200">
                    {preset.icon}
                    <span className="font-medium">{preset.label}</span>
                  </div>
                  <div className="space-y-1 text-sm text-slate-300">
                    <p>{preset.username}</p>
                    <p>{preset.password}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </section>

        <section className="rounded-3xl border border-white/10 bg-white p-8 text-slate-900 shadow-2xl">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-100 text-cyan-700">
              <LogInIcon className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold">Sign in</h2>
              <p className="text-sm text-slate-500">Use a seeded persona account to enter the platform.</p>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Username</span>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                autoComplete="username"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-100"
                autoComplete="current-password"
              />
            </label>

            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-2xl bg-slate-950 px-4 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 hover:enabled:bg-slate-800"
            >
              {isLoading ? 'Signing in...' : `Continue as ${PERSONA_PRESETS[selectedPersona].label}`}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}

export default Login
