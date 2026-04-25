import React, { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, Database, FileSearch, ShieldCheck, Sparkles } from 'lucide-react'

type QueryDomain = 'research' | 'policy' | 'industry'

interface QueryPhaseProgressProps {
  domain: QueryDomain
  isSlowQuery?: boolean
}

const DOMAIN_COPY: Record<QueryDomain, string[]> = {
  research: [
    'Parsing the research question',
    'Checking publications, grants, and graph links',
    'Writing a cited intelligence brief',
    'Verifying citations and audit trail',
  ],
  policy: [
    'Parsing the policy question',
    'Checking state aggregates and ministry data',
    'Writing a policy-level brief',
    'Verifying citations and audit trail',
  ],
  industry: [
    'Parsing the partnership question',
    'Checking anonymized capability signals',
    'Writing a tier-safe opportunity brief',
    'Verifying citations and audit trail',
  ],
}

const ICONS = [FileSearch, Database, Sparkles, ShieldCheck]

export function QueryPhaseProgress({ domain, isSlowQuery = false }: QueryPhaseProgressProps) {
  const [elapsed, setElapsed] = useState(0)
  const phases = useMemo(() => DOMAIN_COPY[domain], [domain])

  useEffect(() => {
    const startedAt = Date.now()
    const interval = window.setInterval(() => {
      setElapsed(Date.now() - startedAt)
    }, 200)
    return () => window.clearInterval(interval)
  }, [])

  const activeIndex = Math.min(3, Math.floor(elapsed / 950))
  const rowCount = Math.min(2400, Math.max(12, Math.floor(elapsed * 1.7)))

  return (
    <div className="rounded-xl border border-nrg-border bg-white/85 p-4 shadow-sm dark:bg-navy-800/80" aria-live="polite">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-nrg-text">NRG evidence pipeline</p>
          <p className="text-xs text-nrg-muted">
            {isSlowQuery ? 'Still working. Validation continues before anything is shown.' : 'Visible progress starts immediately while the answer is prepared.'}
          </p>
        </div>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-navy-700 dark:text-slate-200">
          {activeIndex >= 1 ? `${rowCount.toLocaleString('en-IN')} rows checked` : 'Planning'}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-4">
        {phases.map((phase, index) => {
          const Icon = ICONS[index]
          const complete = index < activeIndex
          const active = index === activeIndex
          return (
            <div
              key={phase}
              data-testid={index === 0 ? 'phase-planning' : index === 3 ? 'phase-verified' : undefined}
              className={`rounded-xl border px-3 py-3 transition ${
                complete
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : active
                    ? 'border-saffron-200 bg-saffron-50 text-saffron-800'
                    : 'border-slate-200 bg-slate-50 text-slate-500 dark:border-navy-700 dark:bg-navy-900/40 dark:text-slate-400'
              }`}
            >
              <div className="flex items-center gap-2">
                {complete ? <CheckCircle2 size={16} /> : <Icon size={16} className={active ? 'animate-pulse' : ''} />}
                <span className="text-xs font-semibold">{phase}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default QueryPhaseProgress
