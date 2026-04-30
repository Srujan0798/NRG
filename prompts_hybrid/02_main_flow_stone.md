# NRG Main Flow Stone

Use this when the priority is to make the product showable: login, role,
dashboard, query, verified answer, and proof.

## Mission

Complete the full end-to-end user journey:

`Login -> Role/Tier -> Dashboard -> Natural Language Query -> Verified Answer -> Table/Graph -> Citations -> Audit Proof -> Export/Copy`

Everything else is secondary until this path works cleanly.

## Required Reading

- `Core_Idea_Clean.md`
- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`
- latest relevant `evidence/2026-04-30/` report
- current `frontend/`
- current API routes under `src/api/`
- current query/orchestration code under `src/orchestration/` and `src/skills/`
- tests covering auth, query, streaming, answer contracts, RBAC, and frontend

## Main Flow Acceptance Contract

The flow must work for Tier 1, Tier 2, and Tier 3.

Use evidence-backed queries first. The current safe walkthrough query is:

- `best quantum researchers`

The expected behavior is a quantum-specific answer with SQL/source evidence,
citations, and an audit event ID. Do not use advanced TRL/funding/patent walkthrough
queries unless fresh evidence proves them end to end.

### 1. Login

- Login page loads in under 2 seconds locally.
- Form is centered, clean, responsive, and branded as NRG.
- Username and password validation happens before API call.
- Enter key submits.
- Wrong credentials show a human-readable error.
- Correct credentials create a session.
- Logout clears session and browser back does not re-enter protected pages.

### 2. Role/Tier

- Researcher, Government, and Industry are visibly distinct.
- The selected role maps to the correct backend tier.
- Tier is stored consistently in auth/session state.
- Restricted routes redirect with a clear message, not a blank page.

### 3. Dashboard

- Dashboard loads without blank states or infinite spinners.
- Each tier has different copy, stats, actions, and data visibility.
- Main query box is prominent.
- Trust signals are visible: audit active, tier, data boundary, last verified.
- Stats are real or honestly labeled as seeded/sample; never `null`, `NaN`, or
  undefined.

### 4. Query Input

- Search box accepts long questions without lag or overflow.
- Enter submits.
- Empty query is blocked client-side.
- Loading states progress through meaningful phases such as:
  `Understanding question`, `Planning data lookup`, `Running verified query`,
  `Checking sources`, `Preparing answer`.
- If response takes more than 5 seconds, show a calm delay message.
- User can submit another query without refreshing.
- Follow-up query preserves context when expected.

### 5. Backend Response

The frontend must not depend on guessed response shapes. The backend returns:

- `audit_event_id`
- `query`
- `response`
- `sql_query`
- `sql_results`
- `citations`
- `tier`
- `query_time_ms`
- verification metadata: source type, source reliability class, source
  freshness, language, independent confirmation count, confidence level, and
  disputed/uncertain flags when the answer depends on cited external or
  reference material

If the backend currently returns a different shape, add an adapter at the
service boundary and write tests for it.

If the flow streams progress or answer chunks, the streamed events must preserve
the same `audit_event_id` or request correlation, pass the same tier filters as
the final response, and degrade to a stable safe error state on disconnect,
timeout, or parser failure. Prefer SSE for one-way progress; use WebSocket only
when the user flow needs bidirectional interaction.

### 6. Results View

The result must never appear as raw JSON.

Required UI:

- answer heading and readable prose
- analytical answer contract when the query asks for metrics, trends, ranking,
  comparison, funnel, cohort, or anomaly:
  short answer, key numbers, comparison baseline, confidence, caveat, and next
  action when applicable
- exact counts, totals, percentages, rankings, filters, and calculations must
  come from SQL or deterministic code; model prose may explain them but must not
  invent or recompute them
- KPI/metric results must expose grain, timeframe, numerator, denominator,
  filters, timezone when relevant, and source table or source proof
- percentages must show underlying counts; do not average percentages without
  recomputing from summed numerators and denominators
- recommendation, roadmap, or planning answers must use a guided intake and
  scenario contract before giving advice:
  stated user goal, known constraints, missing critical constraints, evidence
  basis, and assumptions
- when the question asks for a path forward, compare up to three bounded
  options: conservative, growth, and exploratory. Label them as scenarios, not
  predictions.
- each scenario must include expected outcome range, first milestone, required
  capability/data/resource gaps, key risks, tier-safe limitations, and next
  validation action
- future-state narrative is allowed only as a clearly labelled scenario to make
  trade-offs concrete. Do not roleplay as the user or present a scenario as a
  guaranteed future.
- verification badge
- clickable audit ID
- source proof modal with SQL, row count, citations, source type, reliability
  class, freshness, language when relevant, independent confirmation,
  confidence, disputed flags, and hashes if available
- formatted table with sorting and pagination
- chart/graph when data is time series, funnel, comparison, or network-shaped
- graph choice must match the data shape: line for time, bar for ranked
  comparison, histogram/box for distribution, scatter for relationship, funnel
  for TRL progression or drop-off, cohort table/heatmap for retention, network
  only for real relationships, and table-only when a visual would not clarify
  the answer
- extended chart rules: forecast needs confidence band, anomaly needs explicit
  markers, part-to-whole should use stacked bar or waffle unless there are five
  or fewer slices, target performance should use bullet chart by default,
  cumulative change should use waterfall, geographic data needs region labels,
  and any 3D or network view needs a simpler table or 2D fallback
- every visual needs one clear insight, labelled axes/legend, accessible table
  fallback, and no unlabeled decorative animation
- no truncated bar axes, dual-axis charts, many-slice pie charts, or
  cumulative-only charts that hide recent movement
- citations/source rows expandable below the answer
- copy answer
- export CSV or XLSX for tables when the flow exposes export
- export output must match the currently displayed, tier-filtered table exactly:
  same filters, same row count, same allowed columns, and no hidden raw fields
- exported identifiers, phone-like values, ZIP/PIN-like values, grant IDs, and
  other leading-zero or long-number fields must be preserved as text, not
  silently converted by spreadsheet software
- exported dates must use an explicit stable format and timezone when timezone
  matters
- spreadsheet exports must defend against formula injection. User or database
  text that starts with formula-triggering characters must be escaped or written
  as safe text unless it is an intentional system-generated formula.
- XLSX exports that include calculated fields must use workbook formulas for
  derived values, not hardcoded computed numbers, and must validate formulas
  before the export is accepted.
- XLSX edits to an existing template must preserve original sheets, styles,
  formulas, charts, pivots, and macros unless the task explicitly changes them.
  Verify by reopening the output and checking sheet names plus sample original
  data.
- API errors render as safe task states, not raw backend details: unauthenticated,
  forbidden, tier-limited, validation, timeout, rate-limit, server failure, and
  offline states each need clear copy, retry or re-login behavior where
  appropriate, and an audit/request ID when available
- retry button for failures
- clear no-results state

### 7. Tier Enforcement

Tier 3 must not receive or display:

- names of individual researchers unless explicitly allowed
- emails
- phone numbers
- Aadhaar/PAN/GSTIN
- small-cohort identifying outputs
- raw sensitive grant or profile details

This must be proven from raw API JSON, not only from the UI.

## Implementation Order

1. Start the app and reproduce the current main-flow failure.
2. Fix auth/session first.
3. Fix API service contract second.
4. Fix query submission and loading state third.
5. Fix result rendering fourth.
6. Fix tier-safe raw JSON fifth.
7. Add Playwright or component coverage for the flow.
8. Capture desktop and mobile screenshots.

## Required Verification

Run or create the equivalent checks:

- backend health check
- login success and failure
- Tier 1 query response JSON
- Tier 2 query response JSON
- Tier 3 query response JSON
- PII block test
- injection block test
- frontend main flow test
- mobile viewport screenshot
- browser console check with zero errors during normal flow
- local C4 status is not a frontend blocker if
  `evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/` remains the
  latest proof; production-scale C4 still needs cluster evidence

## Final Response Format

Report only evidence-backed status:

- files changed
- start command used
- credentials or test roles used, if safe to share
- exact query tested
- API JSON proof paths
- screenshot paths
- tests run
- blockers remaining
- commit SHA if committed, or `not committed`
