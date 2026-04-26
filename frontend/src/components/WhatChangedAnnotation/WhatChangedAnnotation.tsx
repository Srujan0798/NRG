import React from 'react'
import { ShieldCheck } from 'lucide-react'

const COPY = {
  heading: 'What changed?',
  body: 'Researcher view can include named evidence and researcher-level context. Industry view is restricted to aggregated institutional signals, anonymized counts, and collaboration-safe fields.',
  label: 'Access policy applied',
}

export const WhatChangedAnnotation: React.FC = () => (
  <aside
    data-testid="what-changed-annotation"
    className="rounded-lg border border-[var(--nrg-warning)] bg-[var(--nrg-warning-soft)] p-4 text-sm text-nrg-text"
  >
    <div className="flex items-start gap-3">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--nrg-surface-1)] text-[var(--nrg-warning)]">
        <ShieldCheck size={16} aria-hidden="true" />
      </span>
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-[var(--nrg-warning)]">{COPY.label}</p>
        <h2 className="mt-1 text-base font-semibold text-nrg-text">{COPY.heading}</h2>
        <p className="mt-2 leading-6 text-nrg-muted">{COPY.body}</p>
      </div>
    </div>
  </aside>
)

export default WhatChangedAnnotation
