import React from 'react'
import WhatChangedAnnotation from '../WhatChangedAnnotation/WhatChangedAnnotation'

interface SideBySideAnswer {
  title: string
  persona: 'researcher' | 'government' | 'industry'
  answer: string
  fields: string[]
}

interface SideBySidePanelProps {
  left?: SideBySideAnswer
  right?: SideBySideAnswer
}

const COPY = {
  heading: 'Persona comparison',
  restricted: 'Access restricted',
}

const DEFAULT_LEFT: SideBySideAnswer = {
  title: 'Tier 1 Researcher',
  persona: 'researcher',
  answer: 'Shows named research groups, citations, grants, and source-level context for verified academic use.',
  fields: ['Researcher names', 'Grant amounts', 'Citation chunks', 'Institution context'],
}

const DEFAULT_RIGHT: SideBySideAnswer = {
  title: 'Tier 3 Industry',
  persona: 'industry',
  answer: 'Shows aggregate opportunity signals while withholding personal researcher details and sensitive identifiers.',
  fields: ['Aggregated institutes', 'Anonymized counts', 'Safe collaboration areas', 'No personal details'],
}

const PersonaCard: React.FC<{ item: SideBySideAnswer }> = ({ item }) => (
  <article className="rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-4 shadow-sm">
    <div className="flex items-center justify-between gap-3">
      <h3 className="text-sm font-bold text-nrg-text">{item.title}</h3>
      {item.persona === 'industry' && (
        <span className="rounded-full border border-[var(--nrg-warning)] bg-[var(--nrg-warning-soft)] px-3 py-1 text-xs font-semibold text-[var(--nrg-warning)]">
          {COPY.restricted}
        </span>
      )}
    </div>
    <p className="mt-3 text-sm leading-6 text-nrg-muted">{item.answer}</p>
    <ul className="mt-4 grid gap-2">
      {item.fields.map((field) => (
        <li key={field} className="rounded-md border border-nrg-border bg-[var(--nrg-surface-2)] px-3 py-2 text-xs font-medium text-nrg-text">
          {field}
        </li>
      ))}
    </ul>
  </article>
)

export const SideBySidePanel: React.FC<SideBySidePanelProps> = ({
  left = DEFAULT_LEFT,
  right = DEFAULT_RIGHT,
}) => (
  <section data-testid="side-by-side-panel" className="space-y-4">
    <div className="flex items-center justify-between gap-3">
      <h2 className="text-base font-semibold text-nrg-text">{COPY.heading}</h2>
    </div>
    <div className="grid gap-4 lg:grid-cols-2">
      <PersonaCard item={left} />
      <PersonaCard item={right} />
    </div>
    <WhatChangedAnnotation />
  </section>
)

export default SideBySidePanel
