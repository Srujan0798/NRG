import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  ChevronRight,
  ClipboardCopy,
  Eye,
  EyeOff,
  FileText,
  Filter,
  GitBranch,
  KeyRound,
  LogOut,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import type { PersonaRole } from '../services/authService'
import { queryService } from '../services/queryService'
import { Button, Card, Drawer, Input, Pill, Select, Skeleton } from '../components/ui'
import { StreamingAnswerPanel, type StreamingProofPayload } from '../components/StreamingAnswerPanel'
import HmacProof from '../components/HmacProof/HmacProof'

type SurfaceRole = PersonaRole
type Confidence = 'high' | 'medium' | 'low' | 'needs_clarification'
const cx = (...classes: Array<string | false | null | void>) => classes.filter(Boolean).join(' ')

interface ChromeProps {
  role: SurfaceRole
  tier: number
  username: string
  onLogout: () => void
  onPersonaChange?: (role: SurfaceRole) => void | Promise<void>
  onNavigate: (path: string) => void
  children: React.ReactNode
}

interface AuthSurfaceProps {
  onLogin: (username: string, password: string) => Promise<boolean>
  error?: string | null
  backendAvailable?: boolean
}

interface SurfaceRouteProps {
  role: SurfaceRole
  tier: number
  username: string
  onLogout: () => void
  onPersonaChange?: (role: SurfaceRole) => void | Promise<void>
  onNavigate: (path: string) => void
}

interface QuerySurfaceProps extends SurfaceRouteProps {
  onQuerySubmit: (query: string) => void
}

interface StatPayload {
  total_researchers?: number
  total_publications?: number
  total_institutions?: number
  tables?: number
  table_count?: number
  database?: { tables?: number; table_count?: number }
}

const ROLE_META: Record<SurfaceRole, { label: string; short: string; tierLabel: string; tone: string; scope: string; dashboardPath: string }> = {
  researcher: {
    label: 'Researcher',
    short: 'T1',
    tierLabel: 'Tier 1',
    tone: 'Researcher view',
    scope: 'Full source-backed research detail where policy allows.',
    dashboardPath: '/app/researcher',
  },
  government: {
    label: 'Government',
    short: 'T2',
    tierLabel: 'Tier 2',
    tone: 'Government view',
    scope: 'Aggregated cohort, state, and policy-level evidence.',
    dashboardPath: '/app/government',
  },
  industry: {
    label: 'Industry',
    short: 'T3',
    tierLabel: 'Tier 3',
    tone: 'Industry view',
    scope: 'Anonymized capability signals and partnership opportunities.',
    dashboardPath: '/app/industry',
  },
}

const LOGIN_DEFAULTS: Record<SurfaceRole, { username: string; password: string }> = {
  researcher: { username: 'researcher@iitgn.ac.in', password: 'Researcher@2026' },
  government: { username: 'ministry@nrg.gov.in', password: 'Ministry@2026' },
  industry: { username: 'partner@industry.in', password: 'Industry@2026' },
}

const SUGGESTIONS = [
  'Top funding agencies by total grant amount last 5 years',
  'TRL-9 innovations in clean energy',
  'Compare Gujarat and Karnataka AI output 5y',
  'Who collaborates with IIT-GN on hydrogen?',
]

const SUPPORTING_PANELS = [
  {
    title: 'Recent answers',
    body: 'Replay verified answers with the same source rows and audit event visible.',
    icon: FileText,
  },
  {
    title: 'Saved queries',
    body: 'Keep the three questions that matter for the review path one click away.',
    icon: ClipboardCopy,
  },
  {
    title: 'Knowledge map',
    body: 'Open the graph only when a relationship question needs it.',
    icon: GitBranch,
  },
]

const formatNumber = (value: number | void, fallback: string) => {
  if (!value) return fallback
  return new Intl.NumberFormat('en-IN').format(value)
}

const tierDataset = (tier: number) => {
  if (tier >= 3) return 't3'
  if (tier === 2) return 't2'
  return 't1'
}

function useTierDocument(tier: number) {
  useEffect(() => {
    const value = tierDataset(tier)
    document.documentElement.dataset.tier = value
    return () => {
      if (document.documentElement.dataset.tier === value) {
        delete document.documentElement.dataset.tier
      }
    }
  }, [tier])
}

function useStats() {
  const [stats, setStats] = useState<StatPayload | null>(null)
  useEffect(() => {
    if (typeof fetch !== 'function') {
      setStats(null)
      return void 0
    }
    let active = true
    fetch('/stats')
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        if (active) setStats(payload)
      })
      .catch(() => {
        if (active) setStats(null)
      })
    return () => {
      active = false
    }
  }, [])
  return stats
}

function HeaderChrome({ role, tier, username, onLogout, onPersonaChange, onNavigate }: Omit<ChromeProps, 'children'>) {
  const meta = ROLE_META[role]
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3">
        <button
          type="button"
          className="flex min-w-0 items-center gap-3 text-left"
          onClick={() => onNavigate('/app')}
          aria-label="Go to query home"
        >
          <span className="grid h-10 w-10 place-items-center rounded-lg border border-border bg-surface font-bold text-accent shadow-sm">N</span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-bold text-fg">National Research Graph</span>
            <span className="block truncate text-xs text-fg-muted">Data sovereignty active · Audit chain live</span>
          </span>
        </button>
        <nav className="hidden items-center gap-2 md:flex" aria-label="Primary">
          <Button variant="ghost" size="sm" onClick={() => onNavigate(meta.dashboardPath)}>Dashboard</Button>
          <Button variant="ghost" size="sm" onClick={() => onNavigate('/app')}>Search</Button>
          <Button variant="ghost" size="sm" onClick={() => onNavigate('/app/audit')}>Audit</Button>
        </nav>
        <div className="flex min-w-0 items-center gap-2">
          <label className="sr-only" htmlFor="persona-switcher">Switch persona</label>
          <select
            id="persona-switcher"
            data-testid="persona-switcher"
            value={role}
            onChange={(event) => void onPersonaChange?.(event.target.value as SurfaceRole)}
            className="hidden min-h-9 rounded-md border border-border bg-surface px-2 text-xs font-semibold text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:block"
            aria-label="Switch persona"
          >
            <option value="researcher">Researcher</option>
            <option value="government">Government</option>
            <option value="industry">Industry</option>
          </select>
          <Pill tone={tier >= 3 ? 'neutral' : tier === 2 ? 'warning' : 'info'}>{meta.short}</Pill>
          <span className="hidden max-w-44 truncate text-xs font-medium text-fg-muted sm:block">{username}</span>
          <Button variant="ghost" size="sm" onClick={onLogout} aria-label="Logout" data-testid="logout-button">
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  )
}

function Chrome(props: ChromeProps) {
  useTierDocument(props.tier)
  return (
    <div className="min-h-screen bg-bg text-fg">
      <HeaderChrome {...props} />
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-7xl px-4 py-5">
        {props.children}
      </main>
    </div>
  )
}

function QueryBox({
  value,
  onChange,
  onSubmit,
  autoFocus = false,
  compact = false,
}: {
  value: string
  onChange: (value: string) => void
  onSubmit: (value: string) => void
  autoFocus?: boolean
  compact?: boolean
}) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  useEffect(() => {
    if (autoFocus) inputRef.current?.focus()
  }, [autoFocus])
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === '/' && document.activeElement !== inputRef.current) {
        event.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <form
      className={cx('rounded-lg border border-border bg-surface p-2 shadow-md focus-within:border-accent focus-within:ring-2 focus-within:ring-ring', compact ? 'max-w-4xl' : 'mx-auto max-w-5xl')}
      onSubmit={(event) => {
        event.preventDefault()
        const trimmed = value.trim()
        if (trimmed) onSubmit(trimmed)
      }}
    >
      <div className="flex items-center gap-2">
        <Search className="ml-2 h-5 w-5 shrink-0 text-fg-muted" aria-hidden="true" />
        <input
          ref={inputRef}
          data-testid="answer-engine-query"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask about Indian research..."
          className="min-h-12 min-w-0 flex-1 bg-transparent text-lg text-fg outline-none placeholder:text-fg-subtle"
          aria-label="Ask about Indian research"
          maxLength={500}
        />
        {value ? (
          <Button type="button" variant="ghost" size="sm" onClick={() => onChange('')} aria-label="Clear query">
            Clear
          </Button>
        ) : null}
        <Button type="submit" variant="primary" size="md">
          Ask
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </form>
  )
}

function SuggestionChips({ onPick }: { onPick: (query: string) => void }) {
  return (
    <div className="mx-auto grid max-w-4xl gap-2 sm:grid-cols-2">
      {SUGGESTIONS.map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          data-testid="suggestion-chip"
          onClick={() => onPick(suggestion)}
          className="min-h-11 rounded-md border border-border bg-surface px-3 text-left text-sm font-semibold text-fg-muted transition hover:border-accent hover:text-fg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {suggestion}
        </button>
      ))}
    </div>
  )
}

function ScaleStrip() {
  const stats = useStats()
  const tableCount = stats?.tables || stats?.table_count || stats?.database?.tables || stats?.database?.table_count
  const items = [
    [formatNumber(stats?.total_researchers, '50K'), 'researchers'],
    [formatNumber(stats?.total_publications, '50K'), 'publications'],
    [formatNumber(stats?.total_institutions, '181'), 'institutions'],
    [formatNumber(tableCount, '58'), 'schema tables'],
    ['DPDP-2023', 'compliant'],
  ]
  return (
    <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-4 gap-y-2 text-center text-sm text-fg-muted">
      {items.map(([value, label]) => (
        <span key={label} className="inline-flex items-center gap-1">
          <span className="font-mono font-bold text-fg">{value}</span>
          <span>{label}</span>
        </span>
      ))}
    </div>
  )
}

export function AnswerEngineLogin({ onLogin, error, backendAvailable = true }: AuthSurfaceProps) {
  const [role, setRole] = useState<SurfaceRole>('researcher')
  const [username, setUsername] = useState(LOGIN_DEFAULTS.researcher.username)
  const [password, setPassword] = useState(LOGIN_DEFAULTS.researcher.password)
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'NRG · Sign in'
  }, [])

  useEffect(() => {
    setUsername(LOGIN_DEFAULTS[role].username)
    setPassword(LOGIN_DEFAULTS[role].password)
  }, [role])

  return (
    <main
      id="main-content"
      tabIndex={-1}
      data-testid="answer-engine-login"
      className="grid min-h-screen place-items-center bg-bg px-4 py-8 text-fg"
      onKeyDown={(event) => {
        if (event.key === 'Escape') {
          setUsername('')
          setPassword('')
        }
      }}
    >
      <div className="absolute inset-0 -z-0 bg-[radial-gradient(circle_at_top,rgb(var(--color-accent)/0.14),transparent_35%)]" />
      <Card className="relative z-10 w-full max-w-md" padding="lg">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-lg bg-fg text-bg font-bold">N</div>
          <p className="text-xs font-semibold uppercase tracking-widest text-fg-muted">IIT Gandhinagar</p>
          <h1 className="mt-2 text-2xl font-bold text-fg">National Research Graph</h1>
          <p className="mt-2 text-sm leading-6 text-fg-muted">Sovereign intelligence over India's research database</p>
        </div>

        <div className="mb-4 grid grid-cols-3 gap-2">
          {(Object.keys(ROLE_META) as SurfaceRole[]).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setRole(item)}
              aria-pressed={role === item}
              className={cx(
                'min-h-10 rounded-md border px-2 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                role === item ? 'border-accent bg-accent/10 text-accent' : 'border-border bg-surface text-fg-muted hover:border-accent',
              )}
            >
              {ROLE_META[item].label}
            </button>
          ))}
        </div>

        {!backendAvailable ? (
          <div className="mb-4 rounded-md border border-warning bg-warning/10 px-3 py-2 text-sm text-warning">
            Connection is unavailable. Check the local stack and retry.
          </div>
        ) : null}

        <form
          className="grid gap-4"
          onSubmit={async (event) => {
            event.preventDefault()
            setLocalError(null)
            if (!username.trim() || !password.trim()) {
              setLocalError('Enter your email and password to continue.')
              return
            }
            setSubmitting(true)
            try {
              await onLogin(username, password)
            } finally {
              setSubmitting(false)
            }
          }}
        >
          <Input
            label="Email"
            type="email"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            data-testid="login-username"
            autoComplete="username"
            leftSlot={<KeyRound className="h-4 w-4" />}
          />
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            data-testid="login-password"
            autoComplete="current-password"
            leftSlot={<ShieldCheck className="h-4 w-4" />}
            rightSlot={
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="grid min-h-9 min-w-9 place-items-center rounded-md text-fg-muted hover:bg-bg-subtle hover:text-fg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            }
          />
          {localError || error ? (
            <div role="alert" className="rounded-md border border-danger bg-danger/10 px-3 py-2 text-sm font-medium text-danger">
              {localError || (error?.includes('401') ? 'Email or password is incorrect' : error)}
            </div>
          ) : null}
          <Button type="submit" variant="primary" size="lg" loading={submitting} data-testid="login-submit" className="w-full">
            {submitting ? 'Signing you in...' : 'Sign in'}
          </Button>
        </form>
        <p className="mt-5 text-center text-xs text-fg-muted">No credentials? Contact your IRPC officer.</p>
      </Card>
    </main>
  )
}

export function AnswerEngineHome({ role, tier, username, onLogout, onPersonaChange, onNavigate, onQuerySubmit }: QuerySurfaceProps) {
  const [query, setQuery] = useState('')
  const meta = ROLE_META[role]
  useEffect(() => {
    document.title = 'NRG · Ask'
  }, [])
  return (
    <Chrome role={role} tier={tier} username={username} onLogout={onLogout} onPersonaChange={onPersonaChange} onNavigate={onNavigate}>
      <section data-testid="answer-engine-hero" className="grid min-h-[calc(100vh-8rem)] place-items-center py-8">
        <div className="w-full space-y-8 text-center">
          <div className="mx-auto max-w-3xl">
            <Pill tone={tier >= 3 ? 'neutral' : tier === 2 ? 'warning' : 'info'}>{meta.tierLabel} · {meta.tone}</Pill>
            <h1 className="mt-5 text-balance text-4xl font-bold tracking-tight text-fg md:text-6xl">
              What would you like to know about India's research ecosystem?
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-fg-muted">
              Sovereign intelligence over India's research database
            </p>
          </div>
          <QueryBox value={query} onChange={setQuery} onSubmit={onQuerySubmit} autoFocus />
          <p className="text-xs font-medium text-fg-muted">Press / to focus</p>
          <SuggestionChips onPick={(suggestion) => {
            setQuery(suggestion)
            onQuerySubmit(suggestion)
          }} />
          <ScaleStrip />
        </div>
      </section>
    </Chrome>
  )
}

export function AnswerEngineDashboard({ role, tier, username, onLogout, onPersonaChange, onNavigate, onQuerySubmit }: QuerySurfaceProps) {
  const [query, setQuery] = useState('')
  const meta = ROLE_META[role]
  useEffect(() => {
    document.title = `NRG · ${meta.label}`
  }, [meta.label])
  return (
    <Chrome role={role} tier={tier} username={username} onLogout={onLogout} onPersonaChange={onPersonaChange} onNavigate={onNavigate}>
      <section data-testid="tier-dashboard" className="space-y-5">
        <Card data-testid="tier-banner" className="border-accent/40 bg-[linear-gradient(135deg,rgb(var(--color-bg-elevated)),rgb(var(--color-bg-subtle)))]" padding="lg">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <Pill tone={tier >= 3 ? 'neutral' : tier === 2 ? 'warning' : 'info'}>{meta.tierLabel}</Pill>
              <h1 className="mt-4 text-3xl font-bold text-fg md:text-5xl">{meta.tone}</h1>
              <p className="mt-3 text-base leading-7 text-fg-muted">{meta.scope}</p>
            </div>
            <Button variant="secondary" onClick={() => onNavigate('/app/audit')}>Open audit list</Button>
          </div>
          <div className="mt-6">
            <QueryBox value={query} onChange={setQuery} onSubmit={onQuerySubmit} compact />
          </div>
        </Card>

        <div className="grid gap-4 md:grid-cols-3">
          {SUPPORTING_PANELS.map((panel) => {
            const Icon = panel.icon
            return (
              <Card key={panel.title} data-testid="supporting-panel" interactive>
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-accent/10 text-accent">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="text-base font-bold text-fg">{panel.title}</h2>
                <p className="mt-2 text-sm leading-6 text-fg-muted">{panel.body}</p>
              </Card>
            )
          })}
        </div>
      </section>
    </Chrome>
  )
}

export function AnswerEngineAnswer({ role, tier, username, onLogout, onPersonaChange, onNavigate }: SurfaceRouteProps) {
  const [drawer, setDrawer] = useState<'source' | 'audit' | 'citation' | null>(null)
  const [followUp, setFollowUp] = useState('')
  const [query, setQuery] = useState(() => sessionStorage.getItem('nrg.lastQuery') || '')
  const [blockedQuery, setBlockedQuery] = useState(() => sessionStorage.getItem('nrg.blockedQuery'))
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null)
  const [proof, setProof] = useState<StreamingProofPayload | null>(null)

  useEffect(() => {
    document.title = 'NRG · Answer'
  }, [])

  const submitAnswerQuery = (next: string) => {
    const trimmed = next.trim()
    if (!trimmed) return

    sessionStorage.setItem('nrg.lastQuery', trimmed)
    setProof(null)
    setSelectedCitation(null)
    setDrawer(null)

    if (/\b(aadhaar|pan|passport|bank account|gstin)\b/i.test(trimmed)) {
      sessionStorage.setItem('nrg.blockedQuery', trimmed)
      setBlockedQuery(trimmed)
      setQuery('')
      setFollowUp('')
      onNavigate('/app/answer/blocked')
      return
    }

    sessionStorage.removeItem('nrg.blockedQuery')
    setBlockedQuery(null)
    setQuery(trimmed)
    setFollowUp('')
    onNavigate('/app/answer/latest')
  }

  const isVerified = Boolean(proof)
  const fullText = proof?.response || ''
  const sql = proof?.sqlQuery || ''
  const retrievedCount = proof?.rowsReturned || 0
  const citations = proof?.citations || []
  const auditEventId = proof?.auditEventId || null
  const signatureBytes = auditEventId ? 26 : null
  const confidence: Confidence = !query ? 'low' : proof?.confidence || 'medium'
  const confidenceTone: 'success' | 'warning' | 'neutral' = confidence === 'high' ? 'success' : confidence === 'medium' ? 'warning' : 'neutral'
  const confidenceLabel = confidence === 'needs_clarification' ? 'needs clarification' : confidence

  const citationMap = useMemo(() => {
    const map: Record<string, Record<string, any>> = {}
    citations.forEach((c) => { map[c.id] = c })
    return map
  }, [citations])

  return (
    <Chrome role={role} tier={tier} username={username} onLogout={onLogout} onPersonaChange={onPersonaChange} onNavigate={onNavigate}>
      <section className="space-y-4" data-testid="answer-route">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button variant="ghost" onClick={() => onNavigate('/app')}><ArrowLeft className="h-4 w-4" />Back</Button>
          <div className="flex items-center gap-2">
            <Pill tone={confidenceTone}>{!query ? 'no query' : `confidence: ${confidenceLabel}`}</Pill>
          </div>
        </div>

        {blockedQuery ? (
          <Card data-testid="prompt-blocked" padding="lg" className="border-warning/50 bg-warning/10">
            <h1 className="text-2xl font-bold text-fg">Sensitive prompt blocked</h1>
            <p className="mt-3 text-sm leading-6 text-fg-muted">
              The query "{blockedQuery}" asks for restricted personal identifiers. NRG cannot process or display Aadhaar, PAN, passport, bank account, GSTIN, phone, or email lists.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" className="rounded-md border border-border bg-surface px-3 py-2 text-sm font-semibold text-fg">Show privacy-safe aggregate counts by state</button>
              <button type="button" className="rounded-md border border-border bg-surface px-3 py-2 text-sm font-semibold text-fg">Summarize research capacity without personal identifiers</button>
            </div>
          </Card>
        ) : !query ? (
          <Card padding="lg">
            <p className="text-sm text-fg-muted">No query submitted. <button type="button" onClick={() => onNavigate('/app')} className="text-accent underline">Go back</button> and enter a question.</p>
          </Card>
        ) : (
        <Card padding="lg" className="space-y-4">
          <h1 className="text-2xl font-bold text-fg">{query}</h1>
          <StreamingAnswerPanel
            query={query}
            onCitationClick={(citation) => {
              setSelectedCitation(citation.id)
              setDrawer('citation')
            }}
            onProofOpen={() => {
              setDrawer('audit')
            }}
            onProofChange={setProof}
          />
          {isVerified && (
            <div className="flex flex-wrap gap-2 border-t border-border pt-4">
              <Button variant="secondary" data-testid="answer-route-copy-answer-button" onClick={() => navigator.clipboard?.writeText(fullText)}>Copy answer</Button>
              <Button variant="secondary" data-testid="answer-route-source-data-toggle" onClick={() => setDrawer('source')}>View source data {retrievedCount > 0 && `(${retrievedCount} rows)`}</Button>
              <Button variant="secondary" data-testid="answer-route-audit-event-toggle" onClick={() => setDrawer('audit')}>View audit event</Button>
            </div>
          )}
          {isVerified && (
            <section data-testid="side-by-side-panel" className="grid gap-3 rounded-lg border border-border bg-bg-subtle p-4 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-fg-muted">Tier 1</p>
                <p className="mt-1 text-sm font-semibold text-fg">Researcher view keeps source-level evidence, citations, SQL, and audit proof visible.</p>
              </div>
              <div data-testid="what-changed-annotation" className="rounded-md border border-warning/40 bg-warning/10 p-3">
                <p className="text-xs font-semibold uppercase tracking-widest text-warning">Access restricted</p>
                <p className="mt-1 text-sm font-medium text-fg-muted">Tier 3 removes personal detail and shows only aggregate, partnership-safe evidence.</p>
              </div>
            </section>
          )}
          <div className="pt-2">
            <QueryBox
              value={followUp}
              onChange={setFollowUp}
              onSubmit={submitAnswerQuery}
              compact
            />
          </div>
        </Card>
        )}
      </section>

      <Drawer open={drawer === 'source'} title="Source data" onClose={() => setDrawer(null)} testId="source-data-drawer">
        <div data-testid="source-data-panel" className="space-y-4">
          {sql ? (
            <Card>
              <p className="mb-2 text-sm font-semibold text-fg">SQL query</p>
              <code className="mt-2 block overflow-auto rounded-md bg-bg-subtle p-3 font-mono text-xs text-fg-muted">
                {sql}
              </code>
            </Card>
          ) : (
            <Card>
              <p className="text-sm text-fg-muted">SQL will appear here once the query executes.</p>
            </Card>
          )}
          <Card className="overflow-auto">
            {retrievedCount > 0 ? (
              <table className="min-w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-widest text-fg-muted">
                  <tr>
                    <th className="border-b border-border px-3 py-2">#</th>
                    <th className="border-b border-border px-3 py-2">Retrieved rows</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border-b border-border px-3 py-2 text-fg-muted">1</td>
                    <td className="border-b border-border px-3 py-2 font-mono text-fg-muted">{retrievedCount.toLocaleString('en-IN')} rows retrieved</td>
                  </tr>
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-fg-muted">Results will appear here once the query executes.</p>
            )}
          </Card>
        </div>
      </Drawer>

      <Drawer open={drawer === 'audit'} title="Audit event" onClose={() => setDrawer(null)} testId="audit-event-drawer">
        <div className="space-y-4">
        {auditEventId && <HmacProof auditEventId={auditEventId} />}
        <dl data-testid="audit-event-panel" className="grid gap-3 text-sm">
          <div><dt className="font-semibold text-fg">Event ID</dt><dd className="font-mono text-fg-muted">{auditEventId || 'pending'}</dd></div>
          <div><dt className="font-semibold text-fg">Query</dt><dd className="text-fg-muted">{query}</dd></div>
          <div><dt className="font-semibold text-fg">Retrieved</dt><dd className="font-mono text-fg-muted">{retrievedCount.toLocaleString('en-IN')} rows</dd></div>
          <div><dt className="font-semibold text-fg">Citations</dt><dd className="font-mono text-fg-muted">{citations.length}</dd></div>
          {signatureBytes && <div><dt className="font-semibold text-fg">Signature bytes</dt><dd className="font-mono text-fg-muted">{signatureBytes}</dd></div>}
          <div><dt className="font-semibold text-fg">Verification</dt><dd className={isVerified ? 'text-success' : 'text-fg-muted'}>{isVerified ? 'Verified' : 'Pending'}</dd></div>
          {auditEventId && (
            <div className="pt-2">
              <Button variant="secondary" onClick={() => queryService.verifyAuditEvent(auditEventId).then(() => {})}>
                Verify on chain
              </Button>
            </div>
          )}
        </dl>
        </div>
      </Drawer>

      <Drawer open={drawer === 'citation'} title="Citation details" onClose={() => setDrawer(null)} testId="citation-drawer">
        {selectedCitation && citationMap[selectedCitation] ? (
          <div className="space-y-3 text-sm">
            <p className="font-semibold text-fg">{citationMap[selectedCitation].title || citationMap[selectedCitation].pub_id}</p>
            {citationMap[selectedCitation].authors && (
              <p className="text-fg-muted">Authors: {Array.isArray(citationMap[selectedCitation].authors) ? citationMap[selectedCitation].authors.join(', ') : citationMap[selectedCitation].authors}</p>
            )}
            {citationMap[selectedCitation].year && <p className="text-fg-muted">Year: {citationMap[selectedCitation].year}</p>}
            {citationMap[selectedCitation].chunk_text && (
              <p className="rounded-md bg-bg-subtle p-3 text-fg-muted">{citationMap[selectedCitation].chunk_text}</p>
            )}
            <p className="font-mono text-xs text-fg-muted">pub_id: {citationMap[selectedCitation].pub_id}</p>
            {citationMap[selectedCitation].audit_event_id && (
              <HmacProof auditEventId={citationMap[selectedCitation].audit_event_id} />
            )}
          </div>
        ) : (
          <p className="text-sm text-fg-muted">Select a citation from the answer above.</p>
        )}
      </Drawer>
    </Chrome>
  )
}

export function AnswerEngineAudit({ role, tier, username, onLogout, onPersonaChange, onNavigate }: SurfaceRouteProps) {
  const [filter, setFilter] = useState<'all' | 'researcher' | 'government' | 'industry'>('all')
  const [selected, setSelected] = useState<string | null>(null)
  const [events, setEvents] = useState<any[]>([])
  const [chainStatus, setChainStatus] = useState<'intact' | 'pending' | 'broken'>('intact')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    document.title = 'NRG · Audit'
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    queryService.listAuditEvents(80).then((result) => {
      if (!cancelled) {
        setEvents(result.events || [])
        setChainStatus(result.chain_status || 'intact')
        setLoading(false)
      }
    }).catch(() => {
      if (!cancelled) setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const visibleRows = filter === 'all' ? events : events.filter((row) => row.persona === filter)

  return (
    <Chrome role={role} tier={tier} username={username} onLogout={onLogout} onPersonaChange={onPersonaChange} onNavigate={onNavigate}>
      <section className="space-y-4" data-testid="audit-list">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <Pill tone={chainStatus === 'intact' ? 'success' : chainStatus === 'pending' ? 'warning' : 'danger'}>
              Chain {chainStatus}
            </Pill>
            <h1 className="mt-3 text-3xl font-bold text-fg">Audit trail</h1>
            <p className="mt-2 text-sm text-fg-muted">Every answer, citation, and tier switch is inspectable.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Select
              label="Filter by user"
              value={filter}
              onChange={(event) => setFilter(event.target.value as typeof filter)}
            >
              <option value="all">All personas</option>
              <option value="researcher">Researcher</option>
              <option value="government">Government</option>
              <option value="industry">Industry</option>
            </Select>
          </div>
        </div>
        <Card className="overflow-hidden p-0">
          <div className="flex items-center gap-2 border-b border-border px-4 py-3 text-xs font-semibold uppercase tracking-widest text-fg-muted">
            <Filter className="h-4 w-4" />
            Filter by user · persona · time · outcome
          </div>
          <div className="max-h-[70vh] overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Skeleton className="h-64 w-full" />
              </div>
            ) : visibleRows.length === 0 ? (
              <div className="py-12 text-center text-sm text-fg-muted">No audit events found.</div>
            ) : (
              visibleRows.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  data-testid="audit-row"
                  onClick={() => setSelected(row.id)}
                  className="grid w-full grid-cols-[minmax(0,1fr)_auto] gap-3 border-b border-border px-4 py-3 text-left transition hover:bg-bg-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-mono text-sm font-semibold text-fg">{row.id}</span>
                    <span className="mt-1 block truncate text-xs text-fg-muted">
                      {row.action} · {row.persona} · {new Date(row.timestamp).toLocaleString('en-IN')}
                    </span>
                  </span>
                  <Pill tone={row.integrity_status === 'intact' ? 'success' : row.integrity_status === 'broken' ? 'danger' : 'warning'}>
                    {row.integrity_status || row.status || 'success'}
                  </Pill>
                </button>
              ))
            )}
          </div>
        </Card>
      </section>
      <Drawer open={Boolean(selected)} title="Audit event metadata" onClose={() => setSelected(null)} testId="audit-event-drawer">
        {selected ? (() => {
          const event = events.find((e) => e.id === selected)
          return event ? (
            <div className="space-y-4">
            <HmacProof auditEventId={selected} />
            <dl className="grid gap-3 text-sm">
              <div><dt className="font-semibold text-fg">Event ID</dt><dd className="font-mono text-fg-muted">{event.id}</dd></div>
              <div><dt className="font-semibold text-fg">HMAC</dt><dd className="font-mono text-fg-muted">{event.hmac}</dd></div>
              <div><dt className="font-semibold text-fg">Timestamp</dt><dd className="text-fg-muted">{new Date(event.timestamp).toLocaleString('en-IN')}</dd></div>
              <div><dt className="font-semibold text-fg">Actor</dt><dd className="text-fg-muted">{event.actor || event.user_id || 'unknown'}</dd></div>
              <div><dt className="font-semibold text-fg">Action</dt><dd className="text-fg-muted">{event.action}</dd></div>
              <div><dt className="font-semibold text-fg">Persona</dt><dd className="text-fg-muted">{event.persona}</dd></div>
              <div><dt className="font-semibold text-fg">Tier</dt><dd className="text-fg-muted">{event.tier}</dd></div>
              <div><dt className="font-semibold text-fg">Integrity</dt><dd className={event.integrity_status === 'intact' ? 'text-success' : 'text-danger'}>{event.integrity_status}</dd></div>
              {event.query && <div><dt className="font-semibold text-fg">Query</dt><dd className="text-fg-muted">{event.query}</dd></div>}
              {event.evidence_count != null && <div><dt className="font-semibold text-fg">Evidence count</dt><dd className="font-mono text-fg-muted">{event.evidence_count}</dd></div>}
              <div className="pt-2">
                <Button variant="secondary" onClick={() => queryService.verifyAuditEvent(selected)}>Verify on chain</Button>
              </div>
            </dl>
            </div>
          ) : (
            <p className="text-sm text-fg-muted">Event not found.</p>
          )
        })() : null}
      </Drawer>
    </Chrome>
  )
}

export function EmptyBlockedState({ type = 'empty' }: { type?: 'empty' | 'error' | 'blocked' }) {
  const copy = {
    empty: ['No matching rows found.', 'Try broadening the time range or using a broader research area.'],
    error: ['We could not retrieve results for this query.', 'Retry or ask a simpler version.'],
    blocked: ['This prompt asks for restricted personal data.', 'Try an aggregate version such as funding by state or institution type.'],
  }[type]
  return (
    <Card className="text-center">
      <Sparkles className="mx-auto h-6 w-6 text-accent" />
      <h2 className="mt-3 text-lg font-bold text-fg">{copy[0]}</h2>
      <p className="mt-2 text-sm text-fg-muted">{copy[1]}</p>
    </Card>
  )
}

export function AnswerEngineScreenSkeleton() {
  return (
    <div className="min-h-screen bg-bg p-4">
      <Skeleton className="h-12" />
      <Skeleton className="mt-4 h-80" />
    </div>
  )
}
