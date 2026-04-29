import React from 'react'
import type { PersonaRole } from '../../services/authService'

interface TierScopeBannerProps {
  role: PersonaRole
  tier: number
}

type TierCopy = {
  label: string
  scope: string
  className: string
}

const TIER_COPY: Record<PersonaRole, TierCopy> = {
  researcher: {
    label: 'Researcher',
    scope: 'Full researcher workspace with identified records where policy allows.',
    className: 'border-indigo-300 bg-indigo-50 text-indigo-950',
  },
  government: {
    label: 'Government',
    scope: 'Aggregated cohorts and state-level evidence with k-anonymity.',
    className: 'border-amber-300 bg-amber-50 text-amber-950',
  },
  industry: {
    label: 'Industry',
    scope: 'Anonymized capability and partnership opportunities.',
    className: 'border-slate-300 bg-slate-100 text-slate-900',
  },
}

export function TierScopeBanner({ role, tier }: TierScopeBannerProps) {
  const copy = TIER_COPY[role] || TIER_COPY.researcher

  return (
    <section
      data-testid="tier-banner"
      className={`rounded-lg border px-4 py-3 text-sm font-medium ${copy.className}`}
      aria-label={`${copy.label} tier scope`}
    >
      <div data-testid="tier-scope-banner">
        <span className="font-semibold">{copy.label}</span>
        <span className="mx-2 font-mono text-xs">{`T${tier}`}</span>
        <span>{copy.scope}</span>
      </div>
    </section>
  )
}

export default TierScopeBanner
