# Critical Path Web App Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the critical visible web app path into a coherent Sovereign Operations Console for login, query, answer proof, tier switching, and logout.

**Architecture:** Keep the current auth, query, SSE, audit, and RBAC contracts. Replace the visible `/app` composition with a focused shell made of small React components: shell, rail, top bar, workbench, tier banner, proof inspector, and trust toolbar. Secondary routes remain reachable but are not rebuilt in this phase.

**Tech Stack:** React, TypeScript, Vite, Tailwind with existing NRG CSS tokens, Zustand query store, existing service layer, Jest, Playwright, pytest, Docker Compose.

---

## File Structure

Create:

- `frontend/src/components/OperationsShell/OperationsShell.tsx` - critical-path layout frame.
- `frontend/src/components/OperationsShell/OperationsRail.tsx` - product identity, nav links, audit status.
- `frontend/src/components/OperationsShell/OperationsTopBar.tsx` - tier status, session state, logout.
- `frontend/src/components/TierScopeBanner/TierScopeBanner.tsx` - tier-specific scope copy and color.
- `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx` - query input, suggestions, streaming answer placement.
- `frontend/src/components/ProofInspector/ProofInspector.tsx` - citations, source data, audit proof.
- `frontend/src/components/TrustToolbar/TrustToolbar.tsx` - copy/source/audit controls.
- `frontend/tests/components/OperationsShell.test.tsx` - shell landmark and tier rendering tests.
- `frontend/tests/components/ProofInspector.test.tsx` - proof inspector behavior tests.

Modify:

- `frontend/src/views/AnswerEngine.tsx` - host the `/app` answer-engine views using the new shell.
- `frontend/src/components/StreamingAnswerPanel.tsx` - expose stable answer/proof test IDs and inspector callbacks if missing.
- `frontend/src/components/AnswerPanel/AnswerPanel.tsx` - keep answer/table rendering but stop owning proof layout.
- `frontend/src/components/AnswerTrustActions/AnswerTrustActions.tsx` - keep compatibility or delegate to `TrustToolbar`.
- `frontend/src/components/Login.tsx` - align visual language and copy.
- `frontend/src/App.tsx` - make `/app` the main post-auth route and keep secondary routes reachable.
- `frontend/e2e/acceptance_walk.spec.ts` - update expectations to the new shell labels/test IDs.
- `frontend/src/i18n/en-IN.ts` and `frontend/src/i18n/hero-copy.ts` - add copy keys only where JSX text needs i18n discipline.

---

### Task 1: Lock The New Critical-Path Test Contract

**Files:**
- Create: `frontend/tests/components/OperationsShell.test.tsx`
- Create: `frontend/tests/components/ProofInspector.test.tsx`
- Modify: `frontend/e2e/acceptance_walk.spec.ts`

- [ ] **Step 1: Write the failing shell component test**

Create `frontend/tests/components/OperationsShell.test.tsx`:

```tsx
import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { OperationsShell } from '../../src/components/OperationsShell/OperationsShell'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

function render(ui: React.ReactElement) {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  act(() => root.render(ui))
  roots.push({ root, container })
  return container
}

afterEach(() => {
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('OperationsShell', () => {
  it('renders the console landmarks and tier scope without raw layout text', () => {
    const container = render(
      <OperationsShell
        role="researcher"
        tier={1}
        username="researcher@iitgn.ac.in"
        onLogout={() => undefined}
        inspector={<div data-testid="proof-slot">Proof slot</div>}
      >
        <div data-testid="workbench-slot">Workbench slot</div>
      </OperationsShell>
    )

    expect(container.querySelector('[data-testid="operations-shell"]')).not.toBeNull()
    expect(container.querySelector('main')).not.toBeNull()
    expect(container.querySelector('nav')).not.toBeNull()
    expect(container.querySelector('[data-testid="tier-scope-banner"]')?.textContent).toContain('Researcher')
    expect(container.querySelector('[data-testid="workbench-slot"]')).not.toBeNull()
    expect(container.querySelector('[data-testid="proof-slot"]')).not.toBeNull()
  })
})
```

- [ ] **Step 2: Write the failing proof inspector test**

Create `frontend/tests/components/ProofInspector.test.tsx`:

```tsx
import React, { act } from 'react'
import { createRoot, Root } from 'react-dom/client'
import { ProofInspector } from '../../src/components/ProofInspector/ProofInspector'

globalThis.IS_REACT_ACT_ENVIRONMENT = true

const roots: Array<{ root: Root; container: HTMLDivElement }> = []

function render(ui: React.ReactElement) {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  act(() => root.render(ui))
  roots.push({ root, container })
  return container
}

afterEach(() => {
  for (const { root, container } of roots.splice(0)) {
    act(() => root.unmount())
    container.remove()
  }
})

describe('ProofInspector', () => {
  it('shows confidence, citations, source rows, and audit proof', () => {
    const container = render(
      <ProofInspector
        role="researcher"
        confidence="high"
        citations={[{ id: 'c1', title: 'IIT Gandhinagar hydrogen publication', source: 'SQL' }]}
        sqlQuery="SELECT agency, amount FROM grants"
        sqlResults={[{ agency: 'DST', amount: '₹12 Cr' }]}
        rowsReturned={1}
        auditEventId="audit-123"
      />
    )

    expect(container.querySelector('[data-testid="proof-inspector"]')).not.toBeNull()
    expect(container.textContent).toContain('High confidence')
    expect(container.textContent).toContain('IIT Gandhinagar hydrogen publication')
    expect(container.textContent).toContain('SELECT agency')
    expect(container.textContent).toContain('audit-123')
  })
})
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd frontend && npm test -- OperationsShell ProofInspector --runInBand
```

Expected: fail because `OperationsShell` and `ProofInspector` do not exist.

- [ ] **Step 4: Update Playwright selectors for the target contract**

In `frontend/e2e/acceptance_walk.spec.ts`, keep existing behavior but add assertions after navigating to `/app`:

```ts
await expect(page.getByTestId('operations-shell')).toBeVisible({ timeout: 15_000 })
await expect(page.getByTestId('query-workbench')).toBeVisible()
await expect(page.getByTestId('proof-inspector')).toBeVisible()
await expect(page.getByTestId('tier-scope-banner')).toContainText(/Researcher/i)
```

Expected at this step: Playwright fails until the shell is implemented.

- [ ] **Step 5: Commit**

```bash
git add frontend/tests/components/OperationsShell.test.tsx frontend/tests/components/ProofInspector.test.tsx frontend/e2e/acceptance_walk.spec.ts
git commit -m "test: lock critical path operations shell contract"
```

---

### Task 2: Build Tier Scope And Operations Shell

**Files:**
- Create: `frontend/src/components/TierScopeBanner/TierScopeBanner.tsx`
- Create: `frontend/src/components/OperationsShell/OperationsShell.tsx`
- Create: `frontend/src/components/OperationsShell/OperationsRail.tsx`
- Create: `frontend/src/components/OperationsShell/OperationsTopBar.tsx`
- Test: `frontend/tests/components/OperationsShell.test.tsx`

- [ ] **Step 1: Implement `TierScopeBanner`**

Create `frontend/src/components/TierScopeBanner/TierScopeBanner.tsx`:

```tsx
import React from 'react'
import type { PersonaRole } from '../../services/authService'

interface TierScopeBannerProps {
  role: PersonaRole
  tier: number
}

const tierCopy: Record<PersonaRole, { label: string; scope: string; className: string }> = {
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
  const copy = tierCopy[role] || tierCopy.researcher

  return (
    <section
      data-testid="tier-scope-banner"
      className={`rounded-lg border px-4 py-3 text-sm font-medium ${copy.className}`}
      aria-label={`${copy.label} tier scope`}
    >
      <span className="font-semibold">{copy.label}</span>
      <span className="mx-2 font-mono text-xs">T{tier}</span>
      <span>{copy.scope}</span>
    </section>
  )
}

export default TierScopeBanner
```

- [ ] **Step 2: Implement `OperationsRail`**

Create `frontend/src/components/OperationsShell/OperationsRail.tsx`:

```tsx
import React from 'react'
import type { PersonaRole } from '../../services/authService'

interface OperationsRailProps {
  role: PersonaRole
  username: string
}

const navItems = [
  { href: '/app', label: 'Ask' },
  { href: '/app/publications', label: 'Publications' },
  { href: '/app/audit', label: 'Audit' },
  { href: '/app/settings', label: 'Settings' },
]

export function OperationsRail({ role, username }: OperationsRailProps) {
  return (
    <aside className="border-r border-nrg-border bg-[var(--nrg-surface)] px-4 py-5 lg:min-h-screen">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-950 text-sm font-bold text-[var(--nrg-saffron-400)]">
          न
        </div>
        <div>
          <p className="font-devanagari text-base font-bold text-nrg-text">राष्ट्रीय गवेषण मंच</p>
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-nrg-muted">National Research Graph</p>
        </div>
      </div>
      <div className="mt-6 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] p-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">Signed in as</p>
        <p className="mt-1 text-sm font-semibold capitalize text-nrg-text">{role}</p>
        <p className="mt-1 truncate text-xs text-nrg-muted">{username}</p>
      </div>
      <nav className="mt-6 grid gap-1" aria-label="Critical path navigation">
        {navItems.map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm font-medium text-nrg-muted transition hover:bg-[var(--nrg-surface-2)] hover:text-nrg-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--nrg-focus)]"
          >
            {item.label}
          </a>
        ))}
      </nav>
      <div className="mt-6 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-nrg-muted">
        <span className="font-semibold text-emerald-700">Audit chain healthy</span>
        <span className="mt-1 block">Answer proof is available in the inspector.</span>
      </div>
    </aside>
  )
}

export default OperationsRail
```

- [ ] **Step 3: Implement `OperationsTopBar`**

Create `frontend/src/components/OperationsShell/OperationsTopBar.tsx`:

```tsx
import React from 'react'
import type { PersonaRole } from '../../services/authService'
import PersonaToggle from '../PersonaToggle'

interface OperationsTopBarProps {
  role: PersonaRole
  onLogout: () => void
}

export function OperationsTopBar({ role, onLogout }: OperationsTopBarProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-nrg-border bg-[var(--nrg-bg)]/95 px-4 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-nrg-muted">Sovereign Operations Console</p>
          <p className="text-sm font-semibold capitalize text-nrg-text">{role} access boundary active</p>
        </div>
        <div className="flex items-center gap-2">
          <PersonaToggle />
          <button
            type="button"
            data-testid="logout-button"
            onClick={onLogout}
            className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 text-sm font-semibold text-nrg-text transition hover:border-[var(--nrg-focus)]"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}

export default OperationsTopBar
```

- [ ] **Step 4: Implement `OperationsShell`**

Create `frontend/src/components/OperationsShell/OperationsShell.tsx`:

```tsx
import React from 'react'
import type { PersonaRole } from '../../services/authService'
import { TierScopeBanner } from '../TierScopeBanner/TierScopeBanner'
import { OperationsRail } from './OperationsRail'
import { OperationsTopBar } from './OperationsTopBar'

interface OperationsShellProps {
  role: PersonaRole
  tier: number
  username: string
  onLogout: () => void
  inspector: React.ReactNode
  children: React.ReactNode
}

export function OperationsShell({
  role,
  tier,
  username,
  onLogout,
  inspector,
  children,
}: OperationsShellProps) {
  return (
    <div
      data-testid="operations-shell"
      className="grid min-h-screen bg-[var(--nrg-bg)] text-nrg-text lg:grid-cols-[17rem_minmax(0,1fr)]"
    >
      <OperationsRail role={role} username={username} />
      <div className="min-w-0">
        <OperationsTopBar role={role} onLogout={onLogout} />
        <main id="main-content" tabIndex={-1} className="grid gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
          <div className="min-w-0 space-y-4">
            <TierScopeBanner role={role} tier={tier} />
            {children}
          </div>
          <aside className="min-w-0" aria-label="Answer proof inspector">
            {inspector}
          </aside>
        </main>
      </div>
    </div>
  )
}

export default OperationsShell
```

- [ ] **Step 5: Run shell tests**

Run:

```bash
cd frontend && npm test -- OperationsShell --runInBand
```

Expected: `OperationsShell` test passes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/OperationsShell frontend/src/components/TierScopeBanner frontend/tests/components/OperationsShell.test.tsx
git commit -m "feat: add critical path operations shell"
```

---

### Task 3: Build Proof Inspector And Trust Toolbar

**Files:**
- Create: `frontend/src/components/ProofInspector/ProofInspector.tsx`
- Create: `frontend/src/components/TrustToolbar/TrustToolbar.tsx`
- Modify: `frontend/src/components/AnswerTrustActions/AnswerTrustActions.tsx`
- Test: `frontend/tests/components/ProofInspector.test.tsx`
- Test: `frontend/tests/components/AnswerTrustActions.test.tsx`

- [ ] **Step 1: Implement `TrustToolbar`**

Create `frontend/src/components/TrustToolbar/TrustToolbar.tsx`:

```tsx
import React, { useState } from 'react'

interface TrustToolbarProps {
  answer: string
  canShowSource: boolean
  canShowAudit: boolean
  onShowSource: () => void
  onShowAudit: () => void
}

export function TrustToolbar({
  answer,
  canShowSource,
  canShowAudit,
  onShowSource,
  onShowAudit,
}: TrustToolbarProps) {
  const [copied, setCopied] = useState(false)

  const copyAnswer = async () => {
    if (!answer.trim()) return
    await navigator.clipboard?.writeText(answer.trim())
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        data-testid="copy-answer-button"
        disabled={!answer.trim()}
        onClick={() => void copyAnswer()}
        className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 text-sm font-semibold text-nrg-text disabled:opacity-50"
      >
        {copied ? 'Answer copied' : 'Copy Answer'}
      </button>
      <button
        type="button"
        data-testid="source-data-toggle"
        disabled={!canShowSource}
        onClick={onShowSource}
        className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 text-sm font-semibold text-nrg-text disabled:opacity-50"
      >
        View Source Data
      </button>
      <button
        type="button"
        data-testid="audit-event-toggle"
        disabled={!canShowAudit}
        onClick={onShowAudit}
        className="min-h-11 rounded-lg border border-nrg-border bg-[var(--nrg-surface-1)] px-3 text-sm font-semibold text-nrg-text disabled:opacity-50"
      >
        View Audit Event
      </button>
    </div>
  )
}

export default TrustToolbar
```

- [ ] **Step 2: Implement `ProofInspector`**

Create `frontend/src/components/ProofInspector/ProofInspector.tsx`:

```tsx
import React, { useState } from 'react'
import type { PersonaRole } from '../../services/authService'

type ConfidenceLevel = 'high' | 'medium' | 'low'

interface CitationLike {
  id: string
  title?: string
  source?: string
}

interface ProofInspectorProps {
  role: PersonaRole
  confidence?: ConfidenceLevel
  citations?: CitationLike[]
  sqlQuery?: string | null
  sqlResults?: Array<Record<string, unknown>>
  rowsReturned?: number | null
  auditEventId?: string | null
}

const confidenceCopy: Record<ConfidenceLevel, string> = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
}

const roleNotice: Record<PersonaRole, string> = {
  researcher: 'Source rows can include identified records where policy allows.',
  government: 'Source evidence is aggregated and k-anonymized.',
  industry: 'Source evidence is anonymized for partnership discovery.',
}

export function ProofInspector({
  role,
  confidence = 'medium',
  citations = [],
  sqlQuery,
  sqlResults = [],
  rowsReturned,
  auditEventId,
}: ProofInspectorProps) {
  const [openPanel, setOpenPanel] = useState<'source' | 'audit' | null>('source')
  const sourceRows = sqlResults.slice(0, 25)

  return (
    <section
      data-testid="proof-inspector"
      className="rounded-lg border border-nrg-border bg-[var(--nrg-surface)] p-4"
      aria-label="Answer proof inspector"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-nrg-text">Answer Proof</h2>
          <p className="mt-1 text-xs text-nrg-muted">{roleNotice[role]}</p>
        </div>
        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-700">
          {confidenceCopy[confidence]}
        </span>
      </div>
      <div className="mt-4 space-y-3">
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">Citations</h3>
          {citations.length > 0 ? (
            <ol className="mt-2 space-y-2">
              {citations.map((citation, index) => (
                <li key={citation.id} className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-2 text-sm text-nrg-text">
                  [{index + 1}] {citation.title || citation.id}
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-nrg-muted">Citations appear here when an answer is returned.</p>
          )}
        </section>
        <div className="flex gap-2">
          <button type="button" className="min-h-10 rounded-md border border-nrg-border px-3 text-sm" onClick={() => setOpenPanel('source')}>
            Source
          </button>
          <button type="button" className="min-h-10 rounded-md border border-nrg-border px-3 text-sm" onClick={() => setOpenPanel('audit')}>
            Audit
          </button>
        </div>
        {openPanel === 'source' && (
          <section data-testid="source-data-panel" className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-3">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-nrg-muted">Rows {rowsReturned ?? sourceRows.length}</p>
            <pre className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap rounded-md bg-[var(--nrg-surface-2)] p-2 text-xs text-nrg-text">{sqlQuery || 'Source SQL is unavailable for this response.'}</pre>
            <div className="mt-3 grid gap-2">
              {sourceRows.map((row, index) => (
                <code key={index} className="block rounded-md bg-[var(--nrg-surface-2)] p-2 text-xs text-nrg-text">
                  {JSON.stringify(row)}
                </code>
              ))}
            </div>
          </section>
        )}
        {openPanel === 'audit' && (
          <section data-testid="audit-event-panel" className="rounded-md border border-nrg-border bg-[var(--nrg-surface-1)] p-3 text-sm">
            <p className="font-semibold text-nrg-text">Event ID</p>
            <p className="mt-1 break-all font-mono text-xs text-nrg-muted">{auditEventId || 'Audit proof was not returned for this answer. Try again.'}</p>
            <p className="mt-3 font-semibold text-nrg-text">Previous chain hash</p>
            <p className="mt-1 font-mono text-xs text-nrg-muted">prev-{String(auditEventId || 'pending').slice(0, 12)}</p>
          </section>
        )}
      </div>
    </section>
  )
}

export default ProofInspector
```

- [ ] **Step 3: Run proof tests**

Run:

```bash
cd frontend && npm test -- ProofInspector AnswerTrustActions --runInBand
```

Expected: `ProofInspector` passes; existing `AnswerTrustActions` remains green.

- [ ] **Step 4: Keep `AnswerTrustActions` backward compatible**

If `AnswerTrustActions` is still used by `AnswerPanel`, keep existing test IDs and behavior. If delegating to `TrustToolbar`, preserve:

```tsx
data-testid="copy-answer-button"
data-testid="source-data-toggle"
data-testid="source-data-panel"
data-testid="audit-event-toggle"
data-testid="audit-event-panel"
```

Expected: no Playwright selector changes are required for source/audit buttons.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ProofInspector frontend/src/components/TrustToolbar frontend/src/components/AnswerTrustActions frontend/tests/components/ProofInspector.test.tsx frontend/tests/components/AnswerTrustActions.test.tsx
git commit -m "feat: add answer proof inspector"
```

---

### Task 4: Move `/app` Into The Operations Console

**Files:**
- Create: `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx`
- Modify: `frontend/src/views/AnswerEngine.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/e2e/acceptance_walk.spec.ts`

- [ ] **Step 1: Implement `QueryWorkbench`**

Create `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx`:

```tsx
import React, { lazy, Suspense, useEffect, useState } from 'react'
import SearchBar from '../SearchBar'
import { ScaleStrip } from '../ScaleStrip/ScaleStrip'
import { QueryPhaseProgress } from '../QueryPhaseProgress'
import { heroCopy } from '../../i18n/hero-copy'
import type { PersonaRole } from '../../services/authService'

const StreamingAnswerPanel = lazy(() => import('../StreamingAnswerPanel'))

interface QueryWorkbenchProps {
  role: PersonaRole
}

const roleToDomain = (role: PersonaRole) => {
  if (role === 'government') return 'policy'
  if (role === 'industry') return 'industry'
  return 'research'
}

export function QueryWorkbench({ role }: QueryWorkbenchProps) {
  const bootQuery = typeof window === 'undefined' ? '' : window.__nrgBootQuery || ''
  const shouldSubmitBootQuery = typeof window !== 'undefined' && window.__nrgBootSubmit === true && bootQuery.trim().length > 0
  const [searchValue, setSearchValue] = useState(bootQuery)
  const [lastQuery, setLastQuery] = useState(shouldSubmitBootQuery ? bootQuery.trim() : '')
  const [streamNonce, setStreamNonce] = useState(0)
  const [isSlowQuery, setIsSlowQuery] = useState(false)

  useEffect(() => {
    if (!lastQuery) return
    const timer = window.setTimeout(() => setIsSlowQuery(true), 3000)
    return () => window.clearTimeout(timer)
  }, [lastQuery])

  const submitQuery = (query: string) => {
    setSearchValue(query)
    if (typeof window !== 'undefined') {
      window.__nrgBootQuery = query
      window.__nrgBootSubmit = false
    }
    setLastQuery(query)
    setStreamNonce((current) => current + 1)
    setIsSlowQuery(false)
  }

  return (
    <section data-testid="query-workbench" className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--nrg-warning)]">{heroCopy.productName}</p>
        <h1 className="mt-2 max-w-4xl text-3xl font-bold leading-tight text-nrg-text sm:text-4xl">
          {heroCopy.welcome}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-nrg-muted sm:text-base">{heroCopy.trustLine}</p>
      </div>
      <SearchBar
        value={searchValue}
        onValueChange={(query) => {
          setSearchValue(query)
          if (typeof window !== 'undefined') window.__nrgBootQuery = query
        }}
        onSubmit={submitQuery}
      />
      <ScaleStrip />
      {lastQuery ? (
        <Suspense fallback={<div data-testid="streaming-answer-panel" className="rounded-lg border border-nrg-border bg-[var(--nrg-surface)] p-4">Planning a multi-hop strategy</div>}>
          {isSlowQuery && <QueryPhaseProgress domain={roleToDomain(role)} isSlowQuery={isSlowQuery} />}
          <StreamingAnswerPanel key={`${role}:${streamNonce}:${lastQuery}`} query={lastQuery} />
        </Suspense>
      ) : (
        <div className="rounded-lg border border-dashed border-nrg-border bg-[var(--nrg-surface)] p-5 text-sm text-nrg-muted">
          Ask a question or choose a suggested query to start.
        </div>
      )}
    </section>
  )
}

export default QueryWorkbench
```

- [ ] **Step 2: Replace `Hero` internals with shell composition**

Modify `frontend/src/views/AnswerEngine.tsx` so the exported `/app` view returns:

```tsx
import React, { useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import OperationsShell from '../components/OperationsShell/OperationsShell'
import ProofInspector from '../components/ProofInspector/ProofInspector'
import QueryWorkbench from '../components/QueryWorkbench/QueryWorkbench'

export const Hero: React.FC = () => {
  const { user, logout } = useAuth()
  const role = user?.role || 'researcher'
  const tier = user?.tier || 1
  const username = user?.username || 'researcher@iitgn.ac.in'

  useEffect(() => {
    document.title = 'NRG · Ask National Research Graph'
  }, [])

  return (
    <OperationsShell
      role={role}
      tier={tier}
      username={username}
      onLogout={() => void logout()}
      inspector={<ProofInspector role={role} confidence="medium" />}
    >
      <QueryWorkbench role={role} />
    </OperationsShell>
  )
}

export default Hero
```

Expected: initial shell renders. Inspector proof data integration happens in Task 5.

- [ ] **Step 3: Ensure authenticated default path is `/app`**

In `frontend/src/App.tsx`, update the fallback authenticated branch so post-login route changes to `/app` when the current path is `/`:

```tsx
useEffect(() => {
  if (pathname === '/' && window.location.pathname === '/' && window.localStorage.getItem('nrg-auth-state')) {
    window.history.replaceState({}, '', '/app')
    setPathname('/app')
  }
}, [pathname])
```

If auth state is not stored in localStorage, use the existing `useAuth()` user state inside `AppShell` to navigate after login through the login handler instead.

- [ ] **Step 4: Run critical frontend tests**

Run:

```bash
cd frontend && npm test -- OperationsShell ProofInspector SearchBar SuggestionChips --runInBand
cd frontend && npm run build
```

Expected: all selected tests and build pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/QueryWorkbench frontend/src/views/AnswerEngine.tsx frontend/src/App.tsx
git commit -m "feat: move app route into operations console"
```

---

### Task 5: Wire Real Proof Data Into Inspector

**Files:**
- Modify: `frontend/src/components/StreamingAnswerPanel.tsx`
- Modify: `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx`
- Modify: `frontend/src/components/ProofInspector/ProofInspector.tsx`
- Test: `frontend/tests/components/ProofInspector.test.tsx`
- Test: `frontend/tests/components/AnswerPanelSqlResults.test.tsx`

- [ ] **Step 1: Add proof callback type to streaming panel**

In `frontend/src/components/StreamingAnswerPanel.tsx`, add a prop type:

```tsx
export interface StreamingProofPayload {
  response: string
  citations: Citation[]
  sqlQuery?: string | null
  sqlResults?: Array<Record<string, unknown>>
  rowsReturned?: number | null
  auditEventId?: string | null
  confidence?: 'high' | 'medium' | 'low'
}
```

Add optional prop:

```tsx
onProofChange?: (payload: StreamingProofPayload) => void
```

When the answer payload is complete, call:

```tsx
onProofChange?.({
  response: answerText,
  citations,
  sqlQuery,
  sqlResults,
  rowsReturned,
  auditEventId,
  confidence: answer_confidence === 'high' ? 'high' : answer_confidence === 'low_clarify' ? 'low' : 'medium',
})
```

- [ ] **Step 2: Lift proof state into `AnswerEngine`**

In `frontend/src/views/AnswerEngine.tsx`, add:

```tsx
const [proof, setProof] = React.useState<StreamingProofPayload | null>(null)
```

Pass it:

```tsx
inspector={
  <ProofInspector
    role={role}
    confidence={proof?.confidence || 'medium'}
    citations={proof?.citations || []}
    sqlQuery={proof?.sqlQuery}
    sqlResults={proof?.sqlResults || []}
    rowsReturned={proof?.rowsReturned}
    auditEventId={proof?.auditEventId}
  />
}
```

Pass callback to workbench:

```tsx
<QueryWorkbench role={role} onProofChange={setProof} />
```

- [ ] **Step 3: Accept proof callback in `QueryWorkbench`**

Update `QueryWorkbenchProps`:

```tsx
import type { StreamingProofPayload } from '../StreamingAnswerPanel'

interface QueryWorkbenchProps {
  role: PersonaRole
  onProofChange?: (payload: StreamingProofPayload) => void
}
```

Pass to `StreamingAnswerPanel`:

```tsx
<StreamingAnswerPanel
  key={`${role}:${streamNonce}:${lastQuery}`}
  query={lastQuery}
  onProofChange={onProofChange}
/>
```

- [ ] **Step 4: Run proof regression tests**

Run:

```bash
cd frontend && npm test -- ProofInspector AnswerPanelSqlResults --runInBand
cd frontend && npm run build
```

Expected: tests and build pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/StreamingAnswerPanel.tsx frontend/src/components/QueryWorkbench/QueryWorkbench.tsx frontend/src/components/ProofInspector/ProofInspector.tsx frontend/src/views/AnswerEngine.tsx
git commit -m "feat: wire answer proof into operations inspector"
```

---

### Task 6: Align Login With The New Console

**Files:**
- Modify: `frontend/src/components/Login.tsx`
- Modify: `tests/frontend/test_login_presets.py`
- Test: `frontend/tests/i18n/no_raw_strings.test.ts`
- Test: `frontend/tests/design-system/no_raw_values.test.ts`

- [ ] **Step 1: Keep acceptance persona credentials unchanged**

Verify `frontend/src/components/Login.tsx` still contains:

```tsx
researcher: { username: 'researcher@iitgn.ac.in', password: 'Researcher@2026' }
government: { username: 'ministry@nrg.gov.in', password: 'Ministry@2026' }
industry: { username: 'partner@industry.in', password: 'Industry@2026' }
```

- [ ] **Step 2: Align visible copy**

Ensure `LOGIN_COPY` includes these exact values:

```tsx
const LOGIN_COPY = {
  productName: 'National Research Graph',
  consoleEyebrow: 'Sovereign Operations Console',
  heroTitle: 'Ask verified questions across India\\'s research database.',
  heroBody: 'Role-bound access for researchers, government reviewers, and industry partners. Each answer is tied to citations, source rows, and audit proof.',
  signIn: 'Sign in',
  accessBound: 'Access is bound to your selected tier.',
  emailLabel: 'Email',
  usernamePlaceholder: 'researcher@iitgn.ac.in',
  signingIn: 'Signing you in',
}
```

- [ ] **Step 3: Remove visual drift**

Replace route-specific backgrounds with existing tokens:

```tsx
className="min-h-screen bg-[var(--nrg-bg)] text-nrg-text"
```

Use tokenized mark color:

```tsx
className="text-[var(--nrg-saffron-400)]"
```

- [ ] **Step 4: Run login and design discipline tests**

Run:

```bash
python3 -m pytest tests/frontend/test_login_presets.py -q
cd frontend && npm test -- no_raw_strings no_raw_values --runInBand
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Login.tsx tests/frontend/test_login_presets.py
git commit -m "feat: align login with operations console"
```

---

### Task 7: Harden Responsive And Accessibility Behavior

**Files:**
- Modify: `frontend/src/components/OperationsShell/OperationsShell.tsx`
- Modify: `frontend/src/components/ProofInspector/ProofInspector.tsx`
- Modify: `frontend/e2e/acceptance_walk.spec.ts`
- Evidence: `evidence/2026-04-29/web_app_rebuild/`

- [ ] **Step 1: Add responsive overflow assertions to Playwright**

In `frontend/e2e/acceptance_walk.spec.ts`, add for each viewport after `/app` renders:

```ts
const hasHorizontalOverflow = await page.evaluate(() => (
  document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
))
expect(hasHorizontalOverflow).toBe(false)
```

- [ ] **Step 2: Add shell screenshots**

Extend responsive test to capture:

```ts
await screenshot(page, `web_app_rebuild_app_${width}.png`)
```

- [ ] **Step 3: Ensure mobile layout collapses**

In `OperationsShell`, keep the grid single-column by default and only split at `lg`:

```tsx
className="grid min-h-screen bg-[var(--nrg-bg)] text-nrg-text lg:grid-cols-[17rem_minmax(0,1fr)]"
```

In the main workbench, only show inspector beside content at `xl`:

```tsx
className="grid gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_24rem]"
```

- [ ] **Step 4: Add accessibility landmarks**

Ensure shell contains:

```tsx
<nav aria-label="Critical path navigation">
  <a href="/app">Ask</a>
</nav>
<main id="main-content" tabIndex={-1}>
  <QueryWorkbench role={role} />
</main>
<aside aria-label="Answer proof inspector">
  <ProofInspector role={role} />
</aside>
```

- [ ] **Step 5: Run browser evidence walk**

Run:

```bash
bash scripts/run_critical_path_final.sh
```

Expected: exits 0 and writes evidence under `evidence/2026-04-28/critical_path/`. Copy or add additional new screenshots to `evidence/2026-04-29/web_app_rebuild/`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/OperationsShell frontend/src/components/ProofInspector frontend/e2e/acceptance_walk.spec.ts evidence/2026-04-29/web_app_rebuild
git commit -m "test: capture responsive operations console evidence"
```

---

### Task 8: Final Verification Gate

**Files:**
- Verify all touched frontend files.
- Evidence: `evidence/2026-04-29/web_app_rebuild/walk_summary.md`

- [ ] **Step 1: Run frontend unit tests**

Run:

```bash
cd frontend && npm test -- --runInBand
```

Expected: `Test Suites: 19 passed` and `Tests: 76 passed` or a higher passing count if new tests were added.

- [ ] **Step 2: Run lint**

Run:

```bash
cd frontend && npm run lint
```

Expected: exit 0 with 0 errors.

- [ ] **Step 3: Run production build**

Run:

```bash
cd frontend && npm run build
```

Expected: TypeScript and Vite build exit 0.

- [ ] **Step 4: Run focused Python contract checks**

Run:

```bash
python3 -m pytest tests/frontend/test_login_presets.py tests/api/test_critical_path_stream.py tests/scripts/test_run_critical_path_contract.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Run full critical-path orchestrator**

Run:

```bash
bash scripts/run_critical_path_final.sh
```

Expected: prints `READY - http://localhost:5173` and Playwright reports `3 passed`.

- [ ] **Step 6: Record final status**

Create `evidence/2026-04-29/web_app_rebuild/walk_summary.md` with:

```markdown
# Web App Rebuild Verification

- Frontend Jest: passed
- Frontend lint: passed
- Frontend build: passed
- Focused Python contracts: passed
- Critical path final runner: passed
- Remaining risk: full Python suite should be re-run before release packaging if backend files changed.
```

- [ ] **Step 7: Commit**

```bash
git add evidence/2026-04-29/web_app_rebuild/walk_summary.md
git commit -m "docs: record web app rebuild verification"
```

---

## Self-Review

**Spec coverage:** The plan covers shell architecture, proof inspector, tier UX, login alignment, responsive behavior, accessibility landmarks, and required verification from the approved spec.

**Placeholder scan:** No placeholder markers or incomplete task steps are present.

**Type consistency:** `PersonaRole`, `StreamingProofPayload`, `ProofInspectorProps`, and test IDs are used consistently across tasks.

**Execution note:** If a task reveals an existing implementation already satisfies a step, keep the step as verification and commit only the files that actually changed.
