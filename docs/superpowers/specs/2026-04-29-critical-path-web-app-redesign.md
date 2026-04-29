# Critical Path Web App Redesign

**Date:** 2026-04-29  
**Status:** Approved direction; awaiting implementation plan  
**Scope:** Critical user path only: login, authenticated workbench, query, streaming answer, proof inspection, tier switch, logout  
**Source rules:** `.claude/rules/ux/protocol.md`, `.claude/rules/frontend.md`, `.agents/AGENTS.md`, `.agents/skills/frontend-design/SKILL.md`, `.claude/skills/design-system/SKILL.md`, `.claude/skills/frontend-react-best-practices/SKILL.md`

## Goal

Rebuild the visible web app around a single production workbench that makes the first 90 seconds feel fast, knowledgeable, and trustworthy. The user logs in, asks a question, sees progress immediately, receives a readable answer, verifies citations/source/audit proof, switches tier, and logs out without seeing broken state, raw JSON, stack traces, or visual drift.

## Product Direction

The app becomes a **Sovereign Operations Console**. It is not a marketing landing page. The first authenticated screen is the actual command surface for querying India's research database.

The visual language should be institutional and operational:

- Calm, dense, and scan-friendly rather than decorative.
- A restrained national palette using existing NRG tokens, not one-off hex values.
- Strong contrast between the central query surface and the right-side proof inspector.
- Visible tier identity in every state: T1 indigo, T2 amber, T3 slate.
- Minimal motion under 200 ms, disabled when reduced motion is requested.
- Cards only for repeated data items, drawers, and bounded tools; no nested decorative card stacks.

## Non-Goals

- Do not rewrite backend query, auth, audit, or RBAC systems unless the UI contract exposes a concrete defect.
- Do not rebuild secondary routes first. `/app/publications`, `/app/researchers`, `/app/reports`, `/app/industry`, `/app/settings`, `/app/audit`, and `/founder` must remain reachable, but they are not the design driver for this phase.
- Do not introduce a new routing framework.
- Do not add a new global state library.
- Do not import heavy UI kits.
- Do not use remote font CDNs.

## Current Problems To Solve

The frontend currently works but feels split across unrelated surfaces:

- `Login.tsx` has a different page composition from `/app`.
- Persona dashboards and the `/app` query surface compete for first-screen ownership.
- Answer trust actions exist, but proof is visually secondary instead of built into the main workbench.
- Tier switching works, but the visible output boundary is not strong enough.
- Design tokens exist, yet component styling still depends on scattered Tailwind patterns and route-specific layouts.
- The same acceptance path is implemented across many files, making defects harder to isolate.

## Target Flow

1. User opens `http://localhost:5173`.
2. If unauthenticated, `Login.tsx` shows a clean institutional sign-in screen with three acceptance persona presets.
3. On sign-in, the user lands at `/app`, not a persona-specific dead end.
4. `/app` renders the Sovereign Operations Console:
   - Left rail: product identity, persona, navigation, audit health.
   - Top bar: current tier scope, session status, logout.
   - Center workbench: query composer, suggestions, phase rail, answer.
   - Right inspector: confidence, citations, source data, audit event.
5. A suggestion chip fills and submits the query.
6. SSE phases are visible within 200 ms and stay visible until answer arrival.
7. Answer renders as prose plus structured tables when data is tabular.
8. User opens source data and audit event in the inspector without leaving context.
9. Persona toggle re-issues the last query under the new JWT and makes the changed tier boundary obvious.
10. PII-blocked prompt shows a human refusal and safe rephrasing choices.
11. Logout clears auth state and returns to login.

## Information Architecture

### Authenticated Shell

Create one workbench shell for the critical path. Existing dashboard routes can reuse it later, but the first phase only wraps `/app`.

```
┌──────────────────────────────────────────────────────────────┐
│ Top Bar: tier scope · chain status · session · logout         │
├───────────────┬─────────────────────────────┬────────────────┤
│ Left Rail     │ Center Workbench            │ Proof Inspector│
│ Product       │ Query composer              │ Confidence     │
│ Persona       │ Suggestion chips            │ Citations      │
│ Navigation    │ Phase rail                  │ Source data    │
│ Audit health  │ Answer panel                │ Audit event    │
└───────────────┴─────────────────────────────┴────────────────┘
```

At 375 px:

- Left rail collapses into a top strip.
- Persona toggle becomes a sheet button.
- Proof inspector becomes a full-screen drawer.
- Query composer remains first interactive element after the top strip.
- No horizontal page scroll.

### Route Behavior

| Route | Behavior |
|---|---|
| `/` | If authenticated, route to `/app`; otherwise show login. |
| `/app` | Sovereign Operations Console. |
| Persona dashboards | Keep current route fallback during transition; do not make them the post-login default. |
| `/app/audit/event/:id` | Continue to show deep audit detail when opened from inspector. |
| Secondary workspace routes | Keep reachable from shell navigation; style can be harmonized after critical path lands. |

## Component Architecture

### New Components

| Component | File | Responsibility |
|---|---|---|
| `OperationsShell` | `frontend/src/components/OperationsShell/OperationsShell.tsx` | Owns critical-path layout: left rail, top bar, main workbench, inspector slot. |
| `OperationsRail` | `frontend/src/components/OperationsShell/OperationsRail.tsx` | Product identity, persona summary, route links, audit health. |
| `OperationsTopBar` | `frontend/src/components/OperationsShell/OperationsTopBar.tsx` | Tier scope, session status, logout, compact mobile controls. |
| `QueryWorkbench` | `frontend/src/components/QueryWorkbench/QueryWorkbench.tsx` | Query input, suggestions, phase progress, answer placement. |
| `ProofInspector` | `frontend/src/components/ProofInspector/ProofInspector.tsx` | Confidence, citations, source data, audit event, drawer behavior. |
| `TierScopeBanner` | `frontend/src/components/TierScopeBanner/TierScopeBanner.tsx` | Tier-specific scope copy and visual color. |
| `TrustToolbar` | `frontend/src/components/TrustToolbar/TrustToolbar.tsx` | Copy answer, source, audit actions with consistent buttons. |

### Components To Refactor

| Existing File | Change |
|---|---|
| `frontend/src/views/Hero.tsx` | Rename behaviorally through exports or replace internals with `QueryWorkbench` inside `OperationsShell`. |
| `frontend/src/components/StreamingAnswerPanel.tsx` | Keep SSE contract; move visual progress into workbench-friendly phase rail. |
| `frontend/src/components/AnswerPanel/AnswerPanel.tsx` | Keep parser/table logic; remove layout responsibility that belongs to shell/inspector. |
| `frontend/src/components/AnswerTrustActions/AnswerTrustActions.tsx` | Fold into `TrustToolbar` and `ProofInspector`. |
| `frontend/src/components/PersonaToggle.tsx` | Keep auth switching; expose compact and full variants through composition, not boolean prop sprawl. |
| `frontend/src/components/Login.tsx` | Keep acceptance credentials; align visual system and error/loading copy with the new shell. |
| `frontend/src/App.tsx` | Make `/app` the authenticated command surface and reduce dashboard-first branching for the critical path. |

## Data Flow

Use the existing service and store boundaries:

- Auth stays in `frontend/src/hooks/useAuth.tsx` and `frontend/src/services/authService.ts`.
- Query HTTP/SSE stays in `frontend/src/services/queryService.ts`, `frontend/src/hooks/useStreamingQuery.ts`, and `frontend/src/stores/queryStore.ts`.
- `QueryWorkbench` submits a query through the existing streaming hook/store.
- `StreamingAnswerPanel` produces answer state, phase state, citations, SQL/source rows, and audit event ID.
- `ProofInspector` receives derived proof data as props. It does not call the API directly except for future explicit deep-link audit loading.
- Persona switching uses `PersonaToggle`, then replays the last query through `queryStore.switchPersona`.

No component in this phase should parse raw API payloads outside the service/store layer.

## Tier-Specific UX

| Tier | Visual | Scope Copy | Answer Boundary |
|---|---|---|---|
| T1 Researcher | Indigo | "Full researcher workspace with identified records where policy allows." | Names, emails, grant amounts only when allowed by API response. |
| T2 Government | Amber | "Aggregated cohorts and state-level evidence with k-anonymity." | No individual PII; cohort/state tables emphasized. |
| T3 Industry | Slate | "Anonymized capability and partnership opportunities." | Anonymous labels, opportunity language, no personal identifiers. |

Tier changes must alter at least three visible elements:

1. Top bar scope color and text.
2. Answer/source column shape.
3. Inspector privacy notice.

## UX Copy Rules

Use plain production copy:

- Login error: "Email or password is incorrect."
- Loading: "Signing you in..." and "Verifying citations..."
- PII blocked: "This query asks for sensitive personal information. Ask for aggregated or anonymized research evidence instead."
- Empty result: "No matching rows found. Try a broader institution, state, or research area."
- Source data unavailable: "Source rows are not available for this tier."
- Audit unavailable: "Audit proof was not returned for this answer. Try again."

Do not show raw status codes, stack traces, `"Error:"`, `"undefined"`, `"null"`, raw JSON, or internal exception text.

## Visual System

Use existing tokens in `frontend/src/index.css` and design-system token files. Add tokens only when the current system lacks a real semantic value.

Required semantic token set:

- App background
- Surface 1, 2, 3
- Border
- Muted text
- Focus ring
- Tier 1, 2, 3
- Success, warning, danger
- Inspector background
- Phase rail active/done/pending

Component constraints:

- Border radius: 6-12 px for operational UI; avoid oversized rounded panels.
- Touch target: at least 44 x 44 CSS px.
- No raw hex or raw px in `frontend/src/components` or `frontend/src/views`.
- Buttons use icon plus label when space allows; icon-only buttons need accessible labels and tooltips.
- Text must not scale with viewport width.

## Accessibility Requirements

The critical path must satisfy WCAG 2.1 AA:

- One `main` landmark.
- Left rail navigation uses `nav`.
- Query input has an explicit label and keyboard shortcut `/`.
- Persona toggle uses `tablist` on desktop and a labelled dialog/sheet on mobile.
- Proof inspector drawer traps focus and closes with Escape.
- Phase updates use polite `aria-live`.
- Error states use `role="alert"` only when immediate attention is required.
- Focus rings visible on all interactive elements.
- Touch targets at least 44 x 44 CSS px.
- Color contrast: normal text >= 4.5:1, large text/UI graphics >= 3:1.

## Performance Requirements

- Login route first useful paint under 2 seconds on laptop-class hardware.
- `/app` interactive query composer under 1.5 seconds after auth.
- Query progress visible within 200 ms of submit.
- Warm answer path under 1 second where backend cache allows it.
- Avoid barrel imports from heavy icon libraries in new files.
- Lazy-load secondary route panels and heavy visualization modules.
- Avoid derived state in effects where values can be computed during render.
- Use stable callbacks for query submission and persona switching.

## Error, Empty, And Loading States

Every critical-path panel must have these states:

| State | Required Behavior |
|---|---|
| Initial | Query composer focused, suggestions visible, no empty blank answer container. |
| Loading | Phase rail active, elapsed time visible, answer area reserved to avoid layout jump. |
| Slow | After 3 seconds, show "Still working across research tables." |
| Success | Answer, confidence, citations/proof actions visible. |
| Empty | Helpful message plus three safe suggestion chips. |
| Blocked | PromptBlocked component with explanation and safe rephrasing choices. |
| Error | Human message, retry button, no raw exception text. |
| Session Expired | Return to login with "Your session expired. Sign in again." |

## Testing And Evidence

### Required Automated Checks

Run after implementation:

```bash
cd frontend && npm test -- --runInBand
cd frontend && npm run lint
cd frontend && npm run build
python3 -m pytest tests/frontend/test_login_presets.py tests/api/test_critical_path_stream.py tests/scripts/test_run_critical_path_contract.py -q
bash scripts/run_critical_path_final.sh
```

### Required Browser Evidence

Save to `evidence/2026-04-29/web_app_rebuild/`:

- `login_researcher_1366.png`
- `app_initial_1366.png`
- `query_streaming_1366.png`
- `answer_with_proof_1366.png`
- `source_inspector_1366.png`
- `audit_inspector_1366.png`
- `tier_government_1366.png`
- `tier_industry_1366.png`
- `blocked_prompt_1366.png`
- `mobile_app_375.png`
- `conference_app_1920.png`
- `console_errors.json`
- `walk_summary.md`

## Acceptance Criteria

- Login works for all three acceptance personas.
- `/app` is the single coherent workbench for query, answer, proof, and tier switching.
- Same query produces visibly different T1/T2/T3 output boundaries.
- User can verify an answer in two clicks or fewer.
- PII prompt is blocked with safe alternatives.
- Logout returns to login and does not preserve authenticated UI through back navigation.
- No visible raw JSON, stack trace, `"Error:"`, `"undefined"`, `"null"`, or `"NaN"`.
- No page-level horizontal scroll at 375, 1366, or 1920 px.
- Full critical-path runner exits 0.

## Implementation Sequencing

1. Add shell-level tests for `/app` structure, tier scope, proof inspector, and mobile layout.
2. Build `OperationsShell`, `OperationsRail`, `OperationsTopBar`, and `TierScopeBanner`.
3. Move `/app` to the shell while preserving existing query behavior.
4. Build `ProofInspector` around existing citation/source/audit data.
5. Refactor answer trust actions into the inspector.
6. Align login styling and copy to the new design system.
7. Harden responsive states.
8. Run the full verification and capture evidence.

## Spec Self-Review

- Placeholder scan: no placeholder markers or incomplete sections remain.
- Scope check: limited to critical user path; secondary routes remain reachable but are not rebuilt in this phase.
- Consistency check: component names and file paths match current repo conventions.
- Ambiguity check: post-login destination, route behavior, proof inspection, and tier boundaries are explicit.
