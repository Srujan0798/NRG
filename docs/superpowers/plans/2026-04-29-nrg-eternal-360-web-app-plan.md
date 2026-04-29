# NRG Eternal 360 Web App Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use `subagent-driven-development` to execute this plan when splitting work across frontend, backend, data, security, and QA agents. Do not improvise around this document. Update evidence and checklist status as work lands.

Date: 2026-04-29
Repository: `/Users/srujansai/Desktop/NRG`
Primary artifact: reviewer-visible web app and 10-step critical-path walk
Related source documents:

- `docs/specs/CRITICAL_PATH_DISPATCH_2026-04-28.md`
- `docs/specs/CRITICAL_PATH_DISPATCH_FINAL_2026-04-28.md`
- `.claude/rules/ux/protocol.md`
- `.agents/skills/*/SKILL.md`
- `evidence/2026-04-28/critical_path/walk_summary.md`

## Executive Goal

Build NRG into a company-grade, reviewer-ready, sovereign research intelligence web app where every visible interaction feels fast, specific, trustworthy, and controlled.

The target user must be able to open the founder laptop, run one command, and perform this path without embarrassment:

1. Open the app.
2. Sign in.
3. See a clear product surface.
4. Ask a high-value research question.
5. Watch progress immediately.
6. Receive a useful, cited, tier-aware answer.
7. Inspect source data.
8. Inspect the audit event.
9. Switch tiers and see real RBAC differences.
10. Trigger a blocked PII prompt and see a human refusal.
11. Log out cleanly.

This document is intentionally broader than the 10-step acceptance walk. The critical path earns the meeting. The 360 plan makes the product survive real company scrutiny.

## Non-Negotiable Truth

The reviewer does not see architecture diagrams first. The reviewer sees the screen.

They judge in roughly 90 seconds:

- Is it fast?
- Does it know something useful?
- Can I trust it?
- Does it look like a serious institution would use it?
- Does it fail gracefully?

Every workstream below exists to improve one of those judgments.

## Current Known State

The repository already contains important working pieces:

- MiniMax is configured through `LLM_PROVIDER=minimax`.
- SSE streaming exists at `/api/query/stream`.
- Login UI exists in `frontend/src/components/Login.tsx`.
- Streaming answer UI exists in `frontend/src/components/StreamingAnswerPanel.tsx`.
- Acceptance evidence exists under `evidence/2026-04-28/critical_path/`.
- `scripts/run_critical_path.sh --strict --walk` has passed in the current workspace.

Recent verification snapshot from the workspace:

- `bash scripts/run_critical_path.sh --strict --walk`: PASS
- `python3 -m pytest tests/security/test_per_user_audit_binding.py tests/security/test_audit_chain.py -q`: 46 passed
- `cd frontend && npm run lint`: passed
- `cd frontend && npm run build`: passed
- `cd frontend && npm test -- QueryWorkbench OperationsShell ProofInspector AnswerTrustActions --runInBand`: passed

Remaining risk:

- The acceptance walk step that submits a query has been observed around 7.8 seconds including screenshot and evidence overhead. The product target remains: visible progress under 200 ms, warm answer under 1 second, cold answer under 6 seconds.
- The app is now improved, but the full 360 plan below has not been completed. Do not confuse critical-path pass with company-grade closure.

## Operating Principles

1. The screen is the product.
2. Evidence beats claims.
3. No raw errors reach users.
4. No PII crosses a tier boundary.
5. No answer is accepted without source data.
6. No slow query is accepted without visible progress.
7. No design change ships without responsive and accessibility checks.
8. No backend change ships without API contract checks.
9. No data change ships without freshness and quality checks.
10. No release claim ships without screenshots, recordings, logs, and a reproducible command.

## Definition Of Done

A task is done only when all of these are true:

- Code is merged or staged in the intended files.
- The relevant tests pass locally.
- The relevant screenshots, JSON, logs, or summaries are written to `evidence/`.
- The user-visible behavior is manually inspected.
- The task checklist in this document or the linked dispatch is updated.
- No unrelated user work is reverted.

## Quality Bar

The target is verified staging parity and crore-level institutional trust.

Minimum visible quality:

- Login completes without blank screens.
- Hero explains product, user, and action in one glance.
- Typography is consistent.
- Buttons have clear hierarchy.
- Inputs are focused, labeled, and keyboard accessible.
- Loading states are immediate and meaningful.
- Answers have structure, confidence, citations, source data, and audit proof.
- Tier switch visibly changes the answer.
- Empty states are helpful.
- Error states are human.
- The app looks intentional at 375, 1366, and 1920 px.

Minimum engineering quality:

- One-command boot.
- Deterministic seed data.
- Deterministic acceptance users.
- Health endpoint reports auth, DB, cache, retriever, audit, and table state.
- SSE events arrive in order.
- API responses are typed and tier-filtered.
- DB queries are bounded and indexed.
- Frontend state cannot render `undefined`, raw `Error:`, tracebacks, or stack dumps.

## Architecture Target

The web app should be treated as five coordinated systems:

1. Experience shell
   - Login, top bar, persona controls, dashboard shell, responsive layout.

2. Query workbench
   - Search input, suggestion chips, streaming progress, answer rendering, trust actions.

3. Intelligence backend
   - Sanitizer, planner, router, SQL executor, retriever, synthesizer, verifier, confidence scorer.

4. Trust and governance layer
   - RBAC, response filtering, audit chain, HMAC event proof, PII refusal, DPDP controls.

5. Operations layer
   - Docker boot, migrations, seeds, prewarm, health, logs, metrics, CI, acceptance evidence.

## Tech Stack Contract

Frontend:

- React with existing app structure.
- TypeScript for all new UI logic.
- CSS tokens for colors, spacing, typography, states, and elevation.
- Playwright for acceptance and visual evidence.
- axe-core for accessibility gates.

Backend:

- FastAPI.
- JWT auth with HttpOnly cookies where browser flow is concerned.
- SSE for query progress.
- PostgreSQL for structured research data.
- Redis for cache.
- Qdrant for vector retrieval where needed.
- MiniMax as primary LLM, NVIDIA fallback where configured.

Data:

- Alembic migrations.
- Seed scripts for acceptance data.
- Deterministic acceptance users.
- Explicit PII classification and tier allowlists.

Ops:

- `docker-compose.prod.yml`.
- `scripts/run_critical_path.sh`.
- Evidence under `evidence/YYYY-MM-DD/...`.

## Company-Grade Workstreams

The work is split into 16 workstreams. Each can be assigned to a specialist agent or human owner, but acceptance must be integrated through the same critical-path walk.

1. Product narrative and information architecture.
2. Visual system and UI shell.
3. Login and session reliability.
4. Query UX and SSE streaming.
5. AI answer quality.
6. Citations, source data, and audit proof.
7. Tier switching and sovereign RBAC.
8. Dashboard design and metrics.
9. Empty, loading, error, and blocked states.
10. Backend API contracts.
11. Database, data quality, and performance.
12. Security, privacy, and compliance.
13. Accessibility and responsive behavior.
14. Observability and operations.
15. Automated QA and evidence capture.
16. Market readiness, release readiness, and founder dry-run.

## Phase 0 - Freeze The Critical Path

Purpose: lock the reviewer-visible path before broader rebuilds.

Owner: senior full-stack lead
Evidence directory: `evidence/2026-04-29/phase0_freeze/`

Tasks:

- [ ] Run `bash scripts/run_critical_path.sh --strict --walk`.
- [ ] Save terminal output to `evidence/2026-04-29/phase0_freeze/run.log`.
- [ ] Copy or regenerate the 10 walk screenshots.
- [ ] Confirm `walk_recording.mp4` exists and plays.
- [ ] Read `walk_summary.md` and record slowest step.
- [ ] Open the app manually and repeat the 10 steps.
- [ ] Create `phase0_defects.md` with every visible defect, even small ones.
- [ ] Label each defect P0, P1, P2, or polish.

Acceptance:

- [ ] The current app is reproducible before deeper rebuild work begins.
- [ ] There is a written defect baseline.
- [ ] No new work starts from vague complaints.

## Phase 1 - Product Narrative

Purpose: every screen must explain what NRG is without marketing fog.

Core promise:

NRG is a sovereign intelligence layer over India's research graph. It helps researchers, government, and industry ask policy-grade questions and verify the answer down to source rows and audit events.

Primary user stories:

- As a researcher, I need named collaborators, publications, grants, institutions, and source details.
- As a government user, I need cohort-level, state-level, and policy-safe intelligence without exposing individual PII.
- As an industry user, I need anonymized opportunity maps and partnership signals without restricted personal data.
- As a reviewer, I need to trust that the app knows its data, respects tiers, and can prove claims.

Required language:

- Product line: `National Research Graph - sovereign intelligence over India's research database`
- Query placeholder: `Ask about Indian research...`
- Trust line: `Answers include citations, source rows, confidence, and audit proof.`
- Tier line T1: `Researcher view: named records and research details permitted for academic use.`
- Tier line T2: `Government view: aggregated cohorts and state-level intelligence.`
- Tier line T3: `Industry view: anonymized opportunity signals and partnership paths.`

Forbidden visible language:

- `Error:`
- `Traceback`
- `undefined`
- `null`
- raw stack traces
- internal provider errors
- raw 401/403/500 messages
- unexplained acronyms in primary copy

Acceptance:

- [ ] Every route has a one-sentence purpose.
- [ ] Every primary CTA uses plain language.
- [ ] Every error tells the user what happened and what to do next.

## Phase 2 - Visual System

Purpose: replace mixed UI with one deliberate institutional system.

Files:

- `frontend/src/styles/tokens.css`
- `frontend/src/index.css`
- `frontend/src/components/ui/*`
- `frontend/src/components/OperationsShell/*`
- `frontend/src/components/QueryWorkbench/*`
- `frontend/src/components/ProofInspector/*`
- `frontend/src/components/TierScopeBanner/*`

Design direction:

- Quiet institutional product, not a marketing landing page.
- Dense but readable.
- Strong information hierarchy.
- No decorative gradient blobs.
- No generic card soup.
- Cards only for repeated items, drawers, and genuinely framed tools.
- Main work area should feel like a command center.

Color roles:

- Background: near-white and deep neutral, not beige or one-note blue.
- Text: high contrast neutral.
- T1: indigo accent.
- T2: amber accent.
- T3: graphite accent.
- Success: green, reserved for verified states.
- Warning: amber, reserved for policy or uncertainty.
- Critical: red, reserved for destructive or blocked states.

Token requirements:

- [ ] All production colors are CSS variables.
- [ ] Literal hex values are blocked outside token files.
- [ ] Spacing scale is tokenized.
- [ ] Radius scale is tokenized and capped unless existing system requires larger.
- [ ] Font stack is local or self-hosted.
- [ ] Focus rings are tokenized.
- [ ] Motion durations are tokenized and under 200 ms for common UI transitions.

Atomic components:

- [ ] Button
- [ ] IconButton
- [ ] Input
- [ ] PasswordInput
- [ ] Select
- [ ] SegmentedControl
- [ ] Badge
- [ ] Pill
- [ ] Drawer
- [ ] Tabs
- [ ] Table
- [ ] EmptyState
- [ ] ErrorState
- [ ] LoadingState
- [ ] BlockedState
- [ ] Toast
- [ ] Tooltip

Visual QA:

- [ ] Capture login, hero, query, answer, drawer, tier switch, blocked state at 375 px.
- [ ] Capture the same at 1366 px.
- [ ] Capture the same at 1920 px.
- [ ] No horizontal scroll.
- [ ] No overlapping text.
- [ ] No unreadable contrast.
- [ ] No icon-only action without tooltip or accessible label.

## Phase 3 - Information Architecture

Purpose: routes and navigation must match the actual user work.

Required routes:

- `/login`
- `/`
- `/dashboard/researcher`
- `/dashboard/government`
- `/dashboard/industry`
- `/query`
- `/answers/:id`
- `/audit/:event_id`
- `/source/:answer_id`
- `/settings/session`
- `/health`
- fallback not-found route

Route requirements:

- [ ] Each route has loading, empty, error, and blocked states.
- [ ] Each route uses shared shell where authenticated.
- [ ] Each authenticated route shows tier badge and logout.
- [ ] Browser refresh preserves session.
- [ ] Back button behaves predictably.
- [ ] Query state can be linked or restored by answer ID.

Acceptance:

- [ ] Playwright route smoke test covers every route.
- [ ] No route renders a blank screen for more than 200 ms.
- [ ] Not-found route is branded and offers return home.

## Phase 4 - Login And Session Reliability

Purpose: login must never be the reason the acceptance walk fails.

Files:

- `src/api/auth.py`
- `src/auth/jwt_handler.py`
- `src/auth/rbac_policies.yaml`
- `frontend/src/components/Login.tsx`
- `frontend/src/services/authService.ts`
- `scripts/issue_test_jwt.py`
- `scripts/seed_acceptance_users.py`

Acceptance users:

- `researcher@iitgn.ac.in` / `Researcher@2026` / tier 1
- `ministry@nrg.gov.in` / `Ministry@2026` / tier 2
- `partner@industry.in` / `Industry@2026` / tier 3

Required behaviors:

- [ ] Missing JWT keys are detected before API boot.
- [ ] Seed script creates all three users idempotently.
- [ ] Password hashes are bcrypt-compatible.
- [ ] `POST /auth/login` returns access token, refresh token, persona, tier, and user ID.
- [ ] Browser stores auth in HttpOnly cookies for production flow.
- [ ] Refresh token flow silently restores session.
- [ ] Logout clears cookies and in-memory state.
- [ ] Wrong password shows `Email or password is incorrect`.
- [ ] Locked or disallowed user gets human message.
- [ ] No auth failure renders a stack trace.

Verification:

```bash
python3 scripts/seed_acceptance_users.py
python3 scripts/issue_test_jwt.py --email researcher@iitgn.ac.in
curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"researcher@iitgn.ac.in","password":"Researcher@2026"}' | jq .
```

Playwright:

- [ ] Login as all three personas.
- [ ] Assert correct dashboard.
- [ ] Assert tier indicator visible.
- [ ] Refresh page and assert session remains.
- [ ] Logout and assert session cleared.
- [ ] Assert no console errors.

## Phase 5 - Hero And First Screen

Purpose: the first 5 seconds must communicate product, use, and next action.

Required above-fold structure:

1. Institute lockup left.
2. Persona/tier switcher and logout right.
3. Product line.
4. Auto-focused query input.
5. Four suggestion chips.
6. Scale strip with live stats.
7. Trust proof strip.

Suggestion chips:

- `Top funding agencies by grant amount`
- `TRL-9 innovations in clean energy`
- `Compare Gujarat and Karnataka AI output 5y`
- `Who collaborates with IIT-GN on hydrogen?`

Stats:

- Researchers.
- Publications.
- Institutions.
- Tables.
- DPDP or governance state.

Acceptance:

- [ ] Input autofocuses on mount.
- [ ] `/` focuses the query input.
- [ ] Each suggestion chip fills and submits the query.
- [ ] Scale strip uses `/stats` or bootstrapped server data.
- [ ] First meaningful paint under 1.5 seconds on target laptop.
- [ ] Lighthouse desktop 90/90/90/90.
- [ ] Lighthouse mobile at least 80/90/90/90.

## Phase 6 - Query UX And SSE Streaming

Purpose: the app must feel alive immediately.

Backend SSE contract:

```json
{"phase":"parsing"}
{"phase":"planning"}
{"phase":"querying","row_count":25}
{"phase":"synthesizing"}
{"phase":"verifying"}
{"phase":"answer","data":{}}
```

Frontend labels:

- `Parsing your question...`
- `Planning a multi-hop strategy...`
- `Querying 58 research tables...`
- `Synthesizing the answer...`
- `Verifying citations...`

Budgets:

- First visible progress: under 200 ms.
- Heartbeat: every 1 second between phases.
- Warm answer: under 1 second.
- Cold answer: under 6 seconds.
- No skeleton-only state beyond 200 ms.

Required states:

- Idle.
- Drafting.
- Submitting.
- Streaming.
- Answered.
- Empty.
- Blocked.
- Failed.
- Retrying.

Verification:

- [ ] Unit test SSE reducer.
- [ ] Mock SSE server test for phase order.
- [ ] Playwright test asserts every phase label appears.
- [ ] Playwright records cold and warm query timings.
- [ ] Evidence includes `cp3_streaming_cold.gif` or video.
- [ ] Evidence includes `cp3_streaming_warm.gif` or video.

## Phase 7 - AI Answer Quality

Purpose: answers must be useful, grounded, tier-aware, and concise.

Files:

- `src/config/llm_config.py`
- `src/orchestration/graph.py`
- `src/api/main.py`
- `src/api/response_filter.py`
- `frontend/src/components/StreamingAnswerPanel.tsx`
- `frontend/src/components/AnswerPanel/AnswerPanel.tsx`

Answer contract:

Every answer must include:

- Direct answer in the first sentence.
- 3 to 5 supporting bullets or short paragraphs.
- Key numbers with source citations.
- Tier-specific visibility.
- Confidence level and reason.
- Source row IDs or citation IDs.
- SQL or retrieval trace available behind trust action.
- Audit event ID.
- Safe limitation statement when needed.

Answer must not include:

- Fabricated numbers.
- Uncited quantitative claims.
- PII in T2 or T3.
- Internal stack traces.
- Provider names unless in admin/debug surfaces.
- Raw prompts.
- Apology loops.
- Unsupported certainty.

Golden questions:

1. `Top funding agencies by grant amount`
2. `TRL-9 innovations in clean energy`
3. `Compare Gujarat and Karnataka AI output 5y`
4. `Who collaborates with IIT-GN on hydrogen?`
5. `Which institutions have the strongest industry collaboration in AI?`

Golden matrix:

- 5 questions x 3 tiers = 15 answer cells.
- Minimum accept score: 13/15.
- Any PII leak in T2 or T3 is automatic failure.
- Any hallucinated numeric claim is automatic failure.
- Any missing citation on a numeric claim is automatic failure.

Grading rubric:

- 0 = unusable or unsafe.
- 1 = technically answers but weak, vague, or poorly cited.
- 2 = reviewer-ready.

Each answer is graded on:

- Specificity.
- Correct tier behavior.
- Citation quality.
- Numerical grounding.
- Clarity.
- Latency.
- Trust actions.

Implementation tasks:

- [ ] Define a typed answer schema.
- [ ] Enforce the schema before rendering.
- [ ] Add answer verifier that checks every numeric claim has a citation.
- [ ] Add tier voice templates.
- [ ] Add confidence computation from source coverage and verifier result.
- [ ] Add answer repair pass for missing citations.
- [ ] Cache golden questions by tier.
- [ ] Store golden answers under `evidence/.../golden/`.
- [ ] Add `scripts/evaluate_golden_answers.py`.

## Phase 8 - Citations, Source Data, And Audit Proof

Purpose: the trust moment must be verifiable in two clicks.

Required answer UI:

- Confidence pill.
- Inline citation chips.
- `Copy Answer`.
- `View Source Data`.
- `View Audit Event`.

Source drawer:

- [ ] SQL shown in a readable block.
- [ ] Row count visible.
- [ ] First 25 rows visible in a table.
- [ ] Columns are tier-filtered.
- [ ] Download CSV available.
- [ ] Empty result has helpful next queries.

Audit drawer:

- [ ] Event ID.
- [ ] JWT `kid`.
- [ ] Timestamp.
- [ ] Tier.
- [ ] Request fingerprint.
- [ ] Previous chain hash truncated.
- [ ] Chain validity status.
- [ ] Link or action to verify when available.

Acceptance:

- [ ] Every answer has at least one citation unless it is a refusal.
- [ ] Every non-refusal answer has source data.
- [ ] Every answer has an audit event.
- [ ] Drawers open and close with keyboard.
- [ ] Drawers are full-screen on mobile and side sheets on desktop.

## Phase 9 - Tier Switching And Sovereign RBAC

Purpose: same query, three visibly different outputs.

Tier behavior:

- T1 researcher: named researchers, institution names, emails where permitted, grant amounts.
- T2 government: aggregated cohorts, k-anonymity, state-level and policy-safe outputs.
- T3 industry: anonymized labels, partnership opportunities, no restricted PII.

Required implementation:

- [ ] Persona toggle re-issues the last query under the target tier.
- [ ] URL updates to reflect current tier or dashboard.
- [ ] Toggle is disabled if user has only one tier.
- [ ] Backend enforces tier response boundary.
- [ ] Frontend never receives forbidden fields.
- [ ] Dashboard banner explains current scope.
- [ ] Answer card columns differ by tier.
- [ ] Evidence saves T1, T2, and T3 response JSON for same query.

Property tests:

- [ ] Generate 1000 randomized query shapes.
- [ ] Apply each tier filter.
- [ ] Assert no PII fields in T2/T3.
- [ ] Assert k-anonymity threshold for government aggregates.
- [ ] Assert industry output uses anonymized labels.

Acceptance:

- [ ] `cp5_tier_t1_response.json != cp5_tier_t2_response.json`
- [ ] `cp5_tier_t2_response.json != cp5_tier_t3_response.json`
- [ ] Visual banners differ.
- [ ] Column sets differ.

## Phase 10 - Dashboard Design

Purpose: dashboards must help the user decide what to ask or inspect next.

Dashboard principles:

- Show the most decision-relevant state first.
- Use dense, scannable metrics.
- Avoid decorative charts.
- Every chart has a question it answers.
- Every metric has source, freshness, and definition.

Researcher dashboard:

- Collaboration graph summary.
- Recent publication clusters.
- Grant agency distribution.
- Institution collaboration table.
- Suggested research queries.
- Saved answers and citations.

Government dashboard:

- State-wise research capacity.
- Funding concentration.
- Strategic technology readiness.
- Regional collaboration gaps.
- DPDP-safe cohort counts.
- Policy briefing exports.

Industry dashboard:

- Opportunity themes.
- Anonymized researcher clusters.
- Partner institution shortlist.
- TRL and commercialization signals.
- Non-sensitive contact workflow.
- Suggested partnership queries.

Metric requirements:

- [ ] Metric name.
- [ ] Business question answered.
- [ ] SQL source.
- [ ] Refresh cadence.
- [ ] Owner.
- [ ] Alert threshold where relevant.

Dashboard QA:

- [ ] No chart without labels.
- [ ] No unlabeled axes.
- [ ] No color-only meaning.
- [ ] No tiny unreadable legends.
- [ ] No metric without freshness timestamp.
- [ ] No aggregate that violates privacy thresholds.

## Phase 11 - Empty, Loading, Error, And Blocked States

Purpose: every failure or absence must still feel controlled.

State matrix per route:

- Initial empty.
- Loading.
- Partial loading.
- Empty result.
- Error.
- Blocked/refused.
- Offline.
- Session expired.
- Permission denied.
- Not found.

Required copy:

- Generic error: `Something went wrong. We logged it with ID: <id>. Try again.`
- Invalid login: `Email or password is incorrect.`
- Blocked PII: `This request asks for restricted personal data. Try an aggregated or anonymized version.`
- Empty source rows: `No matching rows were found. Try broader terms or a different time range.`
- Session expired: `Your session expired. Sign in again to continue.`

Build-time checks:

- [ ] Fail if production view contains visible `Error:`.
- [ ] Fail if production view contains visible `Traceback`.
- [ ] Fail if production view contains visible `undefined`.
- [ ] Fail if production view renders raw `<pre>` for errors.

Acceptance:

- [ ] `cp6_empty.png`
- [ ] `cp6_loading.png`
- [ ] `cp6_error.png`
- [ ] `cp6_blocked.png`

## Phase 12 - Backend API Contracts

Purpose: the frontend must depend on stable, typed behavior.

Required endpoints:

- `GET /health`
- `GET /stats`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/session`
- `GET /api/query/stream`
- `POST /api/query`
- `GET /api/answers/{answer_id}`
- `GET /api/answers/{answer_id}/source`
- `GET /api/audit/{event_id}`

API requirements:

- [ ] All JSON responses include request ID.
- [ ] Errors use one envelope.
- [ ] Auth failures are distinguishable from permission failures.
- [ ] SSE events include phase, timestamp, and request ID.
- [ ] Answer payload includes schema version.
- [ ] Source payload includes tier-filtered columns only.
- [ ] Audit payload includes chain validation status.

Error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "HUMAN_READABLE_CODE",
    "message": "Safe user message",
    "request_id": "uuid"
  }
}
```

Verification:

- [ ] Contract tests for every endpoint.
- [ ] Snapshot tests for representative payloads.
- [ ] Frontend mock server matches backend contracts.
- [ ] OpenAPI generated and checked into docs if stable.

## Phase 13 - Database And Data Quality

Purpose: answers are only as good as source data.

Data inventory:

- Researchers.
- Publications.
- Institutions.
- Grants.
- Patents.
- Collaborations.
- Technology readiness.
- Geography.
- Funding agencies.
- Audit events.
- User accounts.
- RBAC policy tables or files.

Required controls:

- [ ] Table count exposed in `/health`.
- [ ] Freshness timestamp for each major table.
- [ ] Row count checks for acceptance data.
- [ ] Null rate checks for key dimensions.
- [ ] Duplicate detection for researchers, institutions, publications.
- [ ] Foreign key integrity checks.
- [ ] PII classification by column.
- [ ] Tier allowlist by column.
- [ ] Query performance indexes for golden questions.
- [ ] Slow query log review.

Acceptance data:

- [ ] At least 50K researchers.
- [ ] At least 50K publications.
- [ ] 181 institutions or documented current count.
- [ ] 58 or 73 tables accepted only if documented by actual schema state.
- [ ] Golden questions return non-empty source rows.

Verification commands:

```bash
alembic upgrade head
python3 scripts/seed_acceptance_data.py
python3 scripts/check_acceptance_data_quality.py
python3 scripts/prewarm_acceptance_cache.py
```

If `check_acceptance_data_quality.py` does not exist, create it with:

- row count checks
- freshness checks
- key null checks
- duplicate checks
- tier PII checks
- golden query source-row checks

## Phase 14 - Performance

Purpose: the app must feel faster than the user's doubt.

Budgets:

- Login submit visible feedback: under 200 ms.
- Login complete: under 1 second on warm local stack.
- Hero first useful paint: under 1.5 seconds.
- Query first streaming phase: under 200 ms.
- Warm query answer: under 1 second.
- Cold query answer: under 6 seconds.
- Source drawer open: under 300 ms.
- Audit drawer open: under 300 ms.
- Tier switch visual update: under 500 ms.
- Tier switch completed answer: under 3 seconds.
- Route transition: under 300 ms.

Frontend optimization:

- [ ] Remove unused large dependencies.
- [ ] Lazy-load heavy drawers and charts.
- [ ] Avoid blocking font loads.
- [ ] Preload critical stats.
- [ ] Use memoization only where measured.
- [ ] Avoid layout shifts.

Backend optimization:

- [ ] Prewarm 14 killer queries.
- [ ] Cache query plans where safe.
- [ ] Cache source row payloads where safe by tier.
- [ ] Add DB indexes for golden query filters.
- [ ] Enforce query timeouts.
- [ ] Stream phase events before heavy LLM work.
- [ ] Keep acceptance uvicorn worker behavior deterministic.

Performance evidence:

- [ ] Lighthouse reports.
- [ ] Playwright timing summary.
- [ ] API timing logs.
- [ ] DB slow-query report.
- [ ] Cache hit ratio.

## Phase 15 - Accessibility

Purpose: institutional software must be usable by keyboard, screen reader, and touch.

WCAG target: 2.1 AA.

Checks:

- [ ] All controls have accessible names.
- [ ] Keyboard can complete login, query, source drawer, audit drawer, tier switch, logout.
- [ ] Focus order matches visual order.
- [ ] Focus ring is visible.
- [ ] Color contrast passes AA.
- [ ] Icons have labels or are hidden from screen readers when decorative.
- [ ] Drawers trap focus.
- [ ] Escape closes drawers.
- [ ] Touch targets are at least 44 x 44 px on mobile.
- [ ] Reduced motion is respected.
- [ ] Streaming updates are announced politely, not aggressively.

Verification:

```bash
cd frontend
npm run test -- axe
npx playwright test frontend/tests/e2e/accessibility.spec.ts
```

Evidence:

- [ ] axe report.
- [ ] Keyboard walkthrough notes.
- [ ] Mobile touch target screenshots.

## Phase 16 - Security, Privacy, And Compliance

Purpose: trust must be enforced, not just claimed.

Auth:

- [ ] JWT private key never committed.
- [ ] JWT public key loaded correctly.
- [ ] Issuer and audience validated.
- [ ] Expiry enforced.
- [ ] Refresh token rotation or documented safe behavior.
- [ ] Cookies use HttpOnly, Secure in production, SameSite policy.

CORS:

- [ ] Allowed origins are explicit.
- [ ] Credentials behavior is tested.
- [ ] Local dev origin is documented.

RBAC:

- [ ] Tier policy file has owner.
- [ ] Tier policy changes require tests.
- [ ] Backend filters before serialization.
- [ ] Frontend never hides forbidden data as the only protection.

PII:

- [ ] Aadhaar and similar identifiers are blocked.
- [ ] T2 and T3 do not receive names/emails where forbidden.
- [ ] Logs do not store raw restricted prompts unless policy allows redacted storage.
- [ ] Exports are tier-filtered.

Prompt injection:

- [ ] Sanitizer catches obvious unsafe requests.
- [ ] Retrieval context cannot override policy.
- [ ] LLM prompt states tier and forbidden fields.
- [ ] Verifier scans output for forbidden field patterns.

Audit:

- [ ] Chain validity in `/health`.
- [ ] Per-user binding tests pass.
- [ ] Historical salt verification works.
- [ ] Audit event shown in UI.

Security verification:

```bash
python3 -m pytest tests/security -q
bash scripts/forbidden_vocab_check.sh
```

## Phase 17 - Observability And Operations

Purpose: operators must know what broke before the founder does.

Required health fields:

- API status.
- Database status.
- Redis status.
- Qdrant status.
- Auth status.
- Audit chain validity.
- Table count.
- Retriever status.
- Cache status.
- LLM provider status or last known status.

Logging:

- [ ] Every request has request ID.
- [ ] SSE query has phase timing logs.
- [ ] Auth failures are logged without secrets.
- [ ] LLM failures are logged with provider and safe error code.
- [ ] RBAC denials are logged with tier and policy code.

Metrics:

- Login success rate.
- Login latency.
- Query cold latency.
- Query warm latency.
- SSE first-phase latency.
- Answer verifier pass rate.
- Citation coverage.
- PII block count.
- Tier-switch latency.
- Cache hit ratio.
- DB slow query count.
- Audit chain validation failures.

Alerts:

- [ ] Login failure rate over threshold.
- [ ] Health not green.
- [ ] Audit chain invalid.
- [ ] PII leak test failure.
- [ ] Query p95 above budget.
- [ ] LLM provider unavailable.

## Phase 18 - QA And Evidence System

Purpose: make quality visible and reproducible.

Evidence directories:

- `evidence/2026-04-29/phase0_freeze/`
- `evidence/2026-04-29/ui_audit/`
- `evidence/2026-04-29/golden_answers/`
- `evidence/2026-04-29/performance/`
- `evidence/2026-04-29/security/`
- `evidence/2026-04-29/final_walk/`

Required final evidence:

- [ ] 10 acceptance screenshots.
- [ ] Walk recording.
- [ ] Walk summary with commit hash.
- [ ] Health JSON.
- [ ] Golden answer markdown.
- [ ] Tier response JSON files.
- [ ] Lighthouse reports.
- [ ] axe report.
- [ ] Security test log.
- [ ] Backend test log.
- [ ] Frontend lint/build/test logs.

Core command:

```bash
bash scripts/run_critical_path.sh --strict --walk
```

Final verification bundle:

```bash
python3 -m pytest tests/security/test_per_user_audit_binding.py tests/security/test_audit_chain.py -q
cd frontend && npm run lint
cd frontend && npm run build
cd frontend && npm test -- QueryWorkbench OperationsShell ProofInspector AnswerTrustActions --runInBand
cd frontend && npx playwright test tests/e2e/acceptance_walk.spec.ts --project=chromium
```

## Phase 19 - 0.001 Percent Usage Checklist

Purpose: every rare path should be checked at least once before a high-stakes showing.

Login edge cases:

- [ ] Empty email.
- [ ] Invalid email format.
- [ ] Empty password.
- [ ] Wrong password.
- [ ] Locked user.
- [ ] User with one tier.
- [ ] User with multiple tiers.
- [ ] Expired access token.
- [ ] Expired refresh token.
- [ ] API down during login.
- [ ] Network timeout during login.

Query edge cases:

- [ ] Empty query.
- [ ] Very long query.
- [ ] Hindi or mixed-language query.
- [ ] Query with quotes and symbols.
- [ ] Query that returns zero rows.
- [ ] Query that returns too many rows.
- [ ] Query requiring aggregation.
- [ ] Query requiring named entities.
- [ ] Query asking for PII.
- [ ] Prompt injection attempt.
- [ ] LLM provider timeout.
- [ ] Retriever unavailable.
- [ ] DB query timeout.
- [ ] Cache miss.
- [ ] Cache hit.

Answer edge cases:

- [ ] No citations.
- [ ] Low confidence.
- [ ] Medium confidence.
- [ ] High confidence.
- [ ] Empty source rows.
- [ ] SQL unavailable.
- [ ] Audit event unavailable.
- [ ] CSV export fails.
- [ ] Copy answer fails.
- [ ] Long answer wraps correctly.

Tier edge cases:

- [ ] Switch T1 to T2.
- [ ] Switch T2 to T3.
- [ ] Switch T3 to T1.
- [ ] Switch while query is streaming.
- [ ] Switch after blocked prompt.
- [ ] Switch when last query has no rows.
- [ ] Switch when session expires.
- [ ] Verify no stale T1 data remains in T2/T3 UI.

Responsive edge cases:

- [ ] 320 px width.
- [ ] 375 px width.
- [ ] 768 px width.
- [ ] 1366 px width.
- [ ] 1920 px width.
- [ ] Browser zoom 125 percent.
- [ ] Browser zoom 150 percent.
- [ ] Reduced motion enabled.
- [ ] Dark mode.
- [ ] Light mode.

Accessibility edge cases:

- [ ] Full keyboard login.
- [ ] Full keyboard query.
- [ ] Full keyboard drawer open and close.
- [ ] Screen reader announces blocked prompt.
- [ ] Screen reader does not read decorative icons.
- [ ] Focus returns after drawer closes.

Ops edge cases:

- [ ] Docker already running.
- [ ] Ports occupied.
- [ ] Missing `.env`.
- [ ] Missing JWT keys.
- [ ] Redis cold.
- [ ] Qdrant cold.
- [ ] Postgres cold.
- [ ] Migration pending.
- [ ] Seed already applied.
- [ ] Cache already warm.

## Phase 20 - Market And Company Readiness

Purpose: the product must be credible beyond the acceptance walk.

Stakeholder promises:

- Researchers: find collaborators and evidence faster.
- Government: see policy-safe research capacity and technology readiness.
- Industry: find partnership opportunities without restricted personal data.
- Institution leadership: prove national research visibility and governance.

Market risks:

- Data trust risk: mitigated by citations, source rows, freshness, and audit proof.
- Privacy risk: mitigated by RBAC, PII classification, response filtering, and blocked prompts.
- Performance risk: mitigated by SSE, cache, prewarm, and performance budgets.
- UX credibility risk: mitigated by design system, route audit, screenshots, and founder dry-run.
- AI quality risk: mitigated by golden answers, verifier, citation coverage, and fallback.
- Deployment risk: mitigated by one-command boot and health gates.

Business proof points:

- Query time saved compared with manual database search.
- Answer verification in two clicks.
- Tier-specific outputs from same question.
- DPDP-safe refusal behavior.
- Audit event attached to each answer.
- Repeatable acceptance walk from clean laptop boot.

Company-grade milestones:

- Milestone A: critical path closed.
- Milestone B: golden answer score at least 13/15.
- Milestone C: 0 PII leaks in property tests.
- Milestone D: Lighthouse and axe gates pass.
- Milestone E: 30-day operational telemetry available.
- Milestone F: pilot user feedback incorporated.

## Phase 21 - Execution Waves

Wave A - Stabilize:

- [ ] Freeze current critical path.
- [ ] Fix login defects.
- [ ] Fix any visible crash or blank state.
- [ ] Run strict walk.

Wave B - Visual Rebuild:

- [ ] Tokenize design system.
- [ ] Rebuild shell.
- [ ] Rebuild login.
- [ ] Rebuild query workbench.
- [ ] Rebuild answer and proof surfaces.
- [ ] Run responsive screenshots.

Wave C - Intelligence Quality:

- [ ] Define answer schema.
- [ ] Add verifier.
- [ ] Build golden evaluation harness.
- [ ] Improve prompts.
- [ ] Cache golden questions.
- [ ] Grade 15 cells.

Wave D - Governance:

- [ ] Harden response filtering.
- [ ] Add property tests.
- [ ] Verify audit chain UI.
- [ ] Verify PII refusal.
- [ ] Verify export boundaries.

Wave E - Dashboard:

- [ ] Define metrics per persona.
- [ ] Build dashboard components.
- [ ] Add freshness and source labels.
- [ ] Add chart QA.

Wave F - Operations:

- [ ] Harden run script.
- [ ] Add preflight checks.
- [ ] Add final evidence bundle.
- [ ] Add CI gates.
- [ ] Add deployment checklist.

Wave G - Founder Dry-Run:

- [ ] Founder runs one-command boot.
- [ ] Founder walks manually.
- [ ] Every embarrassment is filed.
- [ ] P0 defects fixed immediately.
- [ ] Final recording tagged.

## Phase 22 - File-Level Task Map

Frontend files to own:

- [ ] `frontend/src/views/AnswerEngine.tsx`
- [ ] `frontend/src/views/ResearcherDashboard.tsx`
- [ ] `frontend/src/views/GovernmentDashboard.tsx`
- [ ] `frontend/src/views/IndustryDashboard.tsx`
- [ ] `frontend/src/components/Login.tsx`
- [ ] `frontend/src/components/StreamingAnswerPanel.tsx`
- [ ] `frontend/src/components/OperationsShell/*`
- [ ] `frontend/src/components/QueryWorkbench/*`
- [ ] `frontend/src/components/ProofInspector/*`
- [ ] `frontend/src/components/TierScopeBanner/*`
- [ ] `frontend/src/components/ui/*`
- [ ] `frontend/src/services/authService.ts`
- [ ] `frontend/src/stores/queryStore.ts`
- [ ] `frontend/src/index.css`

Backend files to own:

- [ ] `src/api/main.py`
- [ ] `src/api/auth.py`
- [ ] `src/api/response_filter.py`
- [ ] `src/auth/jwt_handler.py`
- [ ] `src/auth/rbac_policies.yaml`
- [ ] `src/audit/per_user_keys.py`
- [ ] `src/config/llm_config.py`
- [ ] `src/orchestration/graph.py`

Scripts to own:

- [ ] `scripts/run_critical_path.sh`
- [ ] `scripts/seed_acceptance_users.py`
- [ ] `scripts/seed_acceptance_data.py`
- [ ] `scripts/prewarm_acceptance_cache.py`
- [ ] `scripts/issue_test_jwt.py`
- [ ] `scripts/forbidden_vocab_check.sh`
- [ ] `scripts/evaluate_golden_answers.py`
- [ ] `scripts/check_acceptance_data_quality.py`

Tests to own:

- [ ] `tests/e2e/acceptance_walk.spec.ts`
- [ ] `tests/e2e/test_login_3_personas.spec.ts`
- [ ] `tests/e2e/test_tier_switch.spec.ts`
- [ ] `frontend/tests/e2e/responsive.spec.ts`
- [ ] `frontend/tests/a11y/axe.test.ts`
- [ ] `tests/security/test_per_user_audit_binding.py`
- [ ] `tests/security/test_audit_chain.py`
- [ ] response filter property tests

## Phase 23 - Deployment Checklist

Pre-deploy:

- [ ] Branch is clean except intended changes.
- [ ] `.env` exists and contains required non-secret shape.
- [ ] JWT keys exist locally or are generated.
- [ ] Docker is running.
- [ ] Ports are available or script handles conflicts.
- [ ] Migrations run.
- [ ] Acceptance users seeded.
- [ ] Acceptance data seeded.
- [ ] Cache prewarmed.
- [ ] Health green.

Deploy:

- [ ] Boot stack.
- [ ] Wait for ports.
- [ ] Run migrations.
- [ ] Run seeds.
- [ ] Run health.
- [ ] Run Playwright walk.
- [ ] Save evidence.

Post-deploy:

- [ ] Manual founder walk.
- [ ] Golden answer review.
- [ ] Security tests.
- [ ] Accessibility tests.
- [ ] Performance budget review.
- [ ] Defect log updated.

Rollback triggers:

- [ ] Login broken for any persona.
- [ ] Health not green.
- [ ] Audit chain invalid.
- [ ] PII leak.
- [ ] Query blank longer than 200 ms.
- [ ] Warm query above 1 second without explanation.
- [ ] Raw error visible.
- [ ] Tier switch shows wrong data.

## Phase 24 - Human Review Protocol

Purpose: avoid false confidence from automated tests alone.

Reviewer simulation:

1. Open laptop from sleep.
2. Run `bash scripts/run_critical_path.sh --strict --walk`.
3. Watch for PASS.
4. Open browser.
5. Perform 10-step manual walk.
6. Ask one unscripted safe query.
7. Ask one unsafe PII query.
8. Switch all tiers.
9. Open source drawer.
10. Open audit drawer.
11. Log out.

Human scoring:

- Speed: 1 to 5.
- Visual credibility: 1 to 5.
- Answer usefulness: 1 to 5.
- Trust proof: 1 to 5.
- Tier clarity: 1 to 5.
- Failure handling: 1 to 5.

Gate:

- No category below 4 before external showing.

## Phase 25 - Final Acceptance

The project reaches Eternal 360 readiness only when all are true:

- [ ] One-command boot passes.
- [ ] 10-step walk passes.
- [ ] Founder manual walk passes.
- [ ] Golden answer score is at least 13/15.
- [ ] No PII leaks in automated tests.
- [ ] No raw errors in frontend.
- [ ] Lighthouse budgets met or documented with accepted exception.
- [ ] axe has 0 serious/critical issues.
- [ ] Source and audit drawers work.
- [ ] Tier switch visibly changes the answer.
- [ ] Evidence bundle is committed.
- [ ] `BACKLOG.md` includes `Critical path closed YYYY-MM-DD`.
- [ ] Founder explicitly says: `ready to show`.

## Immediate Next Actions

Do these in order:

1. Run the current strict walk again and archive output.
2. Create `phase0_defects.md` from manual inspection.
3. Fix P0/P1 visible defects only.
4. Build golden answer evaluator.
5. Grade 15 answer cells.
6. Tokenize remaining UI drift.
7. Add missing edge-case tests from Phase 19.
8. Run final evidence bundle.
9. Conduct founder dry-run.
10. Commit the final evidence and close the critical path.

## Command Appendix

Critical path:

```bash
bash scripts/run_critical_path.sh --strict --walk
```

Backend security:

```bash
python3 -m pytest tests/security/test_per_user_audit_binding.py tests/security/test_audit_chain.py -q
```

Frontend quality:

```bash
cd frontend
npm run lint
npm run build
npm test -- QueryWorkbench OperationsShell ProofInspector AnswerTrustActions --runInBand
```

Playwright:

```bash
cd frontend
npx playwright test tests/e2e/acceptance_walk.spec.ts --project=chromium
```

Forbidden visible language:

```bash
bash scripts/forbidden_vocab_check.sh
```

Manual health:

```bash
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/stats | jq .
```

## Owner Matrix

Product lead:

- Narrative.
- Release story.
- Acceptance criteria.
- Founder dry-run.

Frontend lead:

- Visual system.
- Shell.
- Query workbench.
- Answer proof UI.
- Responsive behavior.
- Accessibility.

Backend lead:

- Auth.
- SSE.
- Query orchestration.
- LLM integration.
- API contracts.
- Health.

Data lead:

- Seed data.
- Golden query data quality.
- DB performance.
- Freshness.
- PII classification.

Security lead:

- RBAC.
- JWT.
- Cookies.
- CORS.
- Prompt injection.
- PII leak tests.
- Audit chain.

QA lead:

- Playwright.
- Evidence.
- Golden answer grading.
- Regression gates.
- Final bundle.

## Final Rule

Do not ship theatre. Ship the walk.

If a reviewer can see it, click it, wait on it, read it, mistrust it, export it, break it, or misunderstand it, it belongs in this plan.
