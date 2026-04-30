# NRG Evidence Acceptance Stone

Use this as the final proof gate. It does not build features. It decides whether
a feature, flow, or release can be accepted.

## Role

You are the release acceptance engineer. You accept only evidence, not claims.

## Rule

No completion claim is valid without fresh verification from this session.

## Minimum Acceptance Gate

Before accepting any NRG claim, require these ten facts or mark the claim
`UNKNOWN`/`FAILED`:

1. Exact scope and files changed.
2. Exact commands run and their result.
3. Evidence paths saved under the current date.
4. Raw API JSON for any backend/tier claim.
5. Browser screenshot or E2E proof for any UI claim.
6. Audit event ID or request ID for the tested flow.
7. Tier 3 no-PII proof when role/tier behavior is touched.
8. Fresh audit-chain verification when audit/query/load behavior is touched.
9. Performance numbers with request count, P50/P95/P99, and failure rate when
   latency or scale is claimed.
10. Commit SHA if committed, or the words `not committed`.

Current performance truth: local 100-user C4 smoke passed in
`evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`; production
readiness still needs the 1000-user sovereign-cluster/deployed proof.

For broad validation assignments, require
`prompts_hybrid/08_full_coverage_validation_campaign_stone.md` and accept only
the declared coverage matrix, not vague "all possible cases" claims.

## Evidence Standard

| Claim | Required evidence |
| --- | --- |
| app starts | exact command and successful output |
| endpoint works | curl/http output from running service |
| cross-stack feature works | UI action, API request/response, request/response schema, tier policy, data/source evidence, rendered result, and audit/correlation ID for the same flow |
| login works | screenshot or E2E test plus API/session evidence |
| query works | request, response JSON, rendered UI screenshot |
| analytical answer is safe | rendered answer showing baseline, metric contract, confidence, caveat, and counts behind percentages |
| planning recommendation is safe | intake summary, assumptions, up to three option scenarios, evidence basis, gaps, risks, limitations, and next validation action |
| result is verified | audit ID, SQL/source proof, citations |
| cited claims are verified | source list showing source type, reliability class, freshness, language when relevant, independent confirmation, confidence, and disputed/uncertain claims |
| Tier 3 is safe | raw Tier 3 JSON showing no PII keys/values |
| export is safe | exported file inspection: row count, headers, tier scope, dates, IDs, hidden fields, formula-injection handling, and source/render parity match the rendered result |
| spreadsheet formulas are valid | XLSX formula validation output, dynamic recalculation status when available, no cached formula errors, formula cells are not replaced by hardcoded computed values, and existing workbook sheets/data are preserved for edit tasks |
| PII blocked | live API response for direct PII request |
| injection blocked | live API response for injection request |
| secure coding sink is safe | changed sink inventory plus validation/allowlist evidence, negative tests or live requests, and secret/log inspection |
| API/auth hardening is safe | live evidence for token/session failure modes, cookie flags, CORS allowlist, rate limits, security headers, credential storage, and dependency/secret scan when those areas changed |
| service boundary is valid | changed route/service/repository map, proof routes stay thin, service code is HTTP-agnostic, database access stays in repository/selector utilities, and tests can replace shared dependencies |
| configuration boundary is safe | startup validation output, `.env.example` diff, explicit CORS origin evidence, no browser-exposed secrets, no deployed localhost URL, and documented auth/session refresh behavior |
| API error and observability are safe | live 4xx/5xx/error-shape samples, request or audit ID correlation, structured log excerpt with redaction, no stack trace/raw SQL/secret leakage, and retry behavior evidence |
| audit chain valid | command output after restart |
| Text-to-SQL fixed | generated SQL and regression test output |
| prompt/model contract changed | failing input, expected output, updated prompt contract, parser behavior, and regression output |
| implementation scope/review is valid | scope and complexity classification, in/out-of-scope list, assumptions, risks, quality gates, self-review findings by severity, and disposition of CRITICAL/HIGH issues |
| feature build map is valid | feature classification, changed data/backend/frontend/auth-tier/security/config/dependency/deploy surfaces, tests, and evidence files |
| streaming, jobs, cache, or files are safe | SSE/WebSocket/polling choice, auth and disconnect cleanup, tier-safe chunks, idempotent job behavior, cache TTL/key/invalidation proof, upload/export validation, and failure-state evidence |
| migration/release readiness is proven | fresh migration output, risky migration backfill or rollback plan, index/constraint evidence, health/readiness output, deployment gate review, rollback trigger, and post-release validation plan when deploy behavior changes |
| agentic execution is safe | task plan with ids, dependencies, file ownership, test/verify commands, and review evidence |
| agent/tool workflow is safe | agent/stage responsibility map, autonomy budgets, allowed tool schemas, argument/result validation evidence, trace output, fallback behavior, memory policy, and escalation rule |
| memory update is valid | repo memory diff showing trigger/source, rule learned, reason, application, and no duplicate scratch content |
| bug/correction memory is valid | attempted task, observed failure or correction, evidence, root cause, fix, prevention rule, and regression or acceptance check |
| local C4 smoke met | final local Locust output from `live_c4_local_smoke_after_read_model_final/` or newer, with request count, P50/P95/P99, failure rate, and audit verification after load |
| production C4 met | 1000-user sovereign-cluster/deployed Locust CSV/HTML, request count, P50/P95/P99, failure rate, worker/logging settings, and audit verification after load |
| performance met | measured timings, not estimates, with local-vs-cluster scope stated |
| frontend polished | screenshots and console/network check |
| visual design review is fixed | target URL, framework/styling/source target, issue priority, changed file, before/after screenshots at affected viewports, and console/network check |
| browser automation/E2E is valid | command output, target URL, browser or viewport coverage, clean context/auth fixture, stable locator strategy, assertions, screenshots or trace/video artifacts when produced, console/network findings, API/audit evidence for the same flow, and documented mock boundaries |
| frontend system is coherent | token/primitives diff or component inventory plus screenshots showing states |
| frontend design artifact is usable | target route/component/workflow, role/tier task, token or component spec, accessibility and responsive notes, production mapping, and explicit status as proposal or implemented evidence |
| frontend build/deploy is valid | `frontend` build output plus served preview or deployed URL with route smoke evidence |
| frontend media/assets are valid | file/import references plus browser network evidence showing changed assets resolve without console errors |
| frontend type/data safety is proven | TypeScript build output plus typed API/state evidence for changed frontend paths |
| frontend performance is measured | Lighthouse/Web Vitals output or equivalent timing evidence for changed major screens |
| UX flow is coherent | screen/task map showing role, task, entry path, next action, success state, failure state, and screenshots |
| validation campaign is credible | declared campaign mode, query corpus, tier matrix, workflow matrix, security probes, performance scope, structured step log, and findings/fixes report |
| external app fusion is valid | fusion value matrix showing source material inspected, useful ideas, accept/adapt/convert/park/reject decisions, NRG target files, verification gates, and direct-merge rejections |
| whole-product superiority is proven | current validation campaign matrix across UI/UX, backend/API, database/schema, tier safety, audit proof, accessibility, performance, and evidence gates; external fusion evidence alone is insufficient |
| mobile works | mobile viewport screenshots or device recording |
| tests pass | exact command output |
| handover ready | file list and freshness check |

## Evidence Folder Structure

Create or update an evidence folder by date:

```text
evidence/YYYY-MM-DD/
  00_current_state.md
  01_startup_health.log
  02_auth_login_logout.md
  03_tier1_query_response.json
  04_tier2_query_response.json
  05_tier3_query_response.json
  06_tier3_no_pii_check.md
  07_pii_block_response.json
  08_injection_block_response.json
  09_audit_chain_verify.log
  10_text_to_sql_regression.log
  11_critical_queries.md
  12_explain_analyze.log
  13_frontend_console_network.md
  14_playwright_or_e2e.log
  15_desktop_screenshots.md
  16_mobile_screenshots.md
  17_red_team_results.md
  18_performance_results.md
  19_handover_status.md
  20_final_acceptance_report.md
  21_visual_review_before_after.md
  22_api_auth_hardening.md
  23_browser_automation_e2e.md
  24_agent_tool_workflow.md
  25_frontend_design_handoff.md
  26_implementation_scope_review.md
  27_feature_build_map.md
  28_service_boundary_contract.md
  29_config_env_cors.md
  30_streaming_jobs_cache_files.md
  31_release_gate_report.md
  32_spreadsheet_export_validation.md
  exports/
    tier1_result.csv
    tier3_result.csv
    tier1_result.xlsx
    export_integrity_check.md
```

If a file is not applicable, include it with an explanation. Missing evidence
must remain visible.

## Acceptance Checklist

### Startup

- documented start command works
- health endpoint returns healthy
- database reachable
- frontend reachable
- no manual hidden step required

### Auth

- wrong credentials fail clearly
- correct credentials work
- all roles tested
- logout works
- protected route blocks unauthenticated user
- token/session expiry, malformed token, replay where applicable, refresh or
  re-login path, and 401/403 UI mapping are proven when auth code changes

### Main Flow

- query can be typed and submitted
- loading state appears
- response returns structured data
- answer renders as prose
- analytical answers include baseline, timeframe, grain, counts behind
  percentages, confidence, and caveat when applicable
- recommendation or planning answers include intake summary, explicit
  assumptions, option scenarios, evidence basis, gaps, risks, limitations, and
  next validation action
- scenarios are labelled as scenarios, not predictions, and do not roleplay as
  the user unless an explicit product surface requires it
- table renders
- graph renders when useful
- chart type matches the question and avoids misleading axes or unsupported
  causal claims
- new charts include a chart contract: data type, chosen chart, rejected
  alternatives, encodings, accessibility fallback, and large-data performance
  guard
- chart evidence shows the selected visual matches the data shape: line or
  confidence band for time/forecast, sorted bar for ranked comparison, heatmap
  for matrix/cohort, funnel for TRL drop-off, waterfall for cumulative change,
  bullet for target performance, map only for geographic data, network only for
  real relationships, and table-only when a visual does not clarify the answer
- citations render
- cited claims expose source type, reliability class, freshness, language when
  relevant, confidence, and disputed or uncertain status when applicable
- audit proof opens
- export/copy works or blocked with clear reason
- exported CSV/XLSX rows match the rendered, tier-filtered table row count
- export headers contain only allowed columns for that tier
- exported dates and long identifiers are not mangled by spreadsheet defaults
- exported text that starts with formula-triggering characters is escaped or
  written as safe text unless it is an intentional system-generated formula
- XLSX exports with derived values contain formulas for calculated cells rather
  than stale hardcoded results
- XLSX files produced by editing a template preserve the original workbook
  sheets, styles, formulas, charts, pivots, macros, and unrelated sample data

### Security

- changed code has a sink inventory for SQL/database, HTML/Markdown,
  files/exports/assets, shell/process execution, outbound HTTP/tool calls,
  auth/session behavior, secrets, and logs when those areas are touched
- every changed sink validates or allowlists untrusted user input, model output,
  database text, generated files, or third-party responses before use
- SQL values are parameterized; generated SQL and identifiers are parsed,
  allowlisted, or schema-derived before execution
- user/model/database text is rendered as text by default or sanitized against a
  narrow allowlist before rich rendering
- file paths, export names, subprocess calls, and outbound requests reject
  traversal, command injection, unauthorized egress, and secret/PII leakage
- spreadsheet outputs reject formula injection and do not expose hidden raw
  columns, unrestricted backing rows, stale formula caches, or template metadata
  that would reveal restricted information
- user-facing errors do not expose stack traces, raw SQL errors, secrets, or
  internal filesystem paths
- auth/security middleware changes prove token/session expiry and malformed
  token handling, cookie flags, CORS allowlist behavior, rate-limit behavior,
  security headers, and dependency/secret scan output when applicable
- credential material, API keys, refresh tokens, and password hashes are not
  stored or logged in plaintext; any sensitive-data encryption uses documented
  key management and rotation behavior
- PII direct request blocked
- injection blocked
- Tier 3 raw JSON contains no PII
- Tier 3 export contains no PII keys, hidden columns, or raw backing fields
- small-cohort query blocked or generalized
- audit event created for allowed and blocked requests

### Configuration And API Boundary

- new env vars are centralized, validated at startup, and documented in
  `.env.example` with placeholders
- client-visible env vars contain no secrets and use the framework's public env
  prefix only when the value is safe for browsers
- API base URLs, model/service URLs, CORS origins, storage backends, and timeout
  values are not hardcoded in changed feature code
- CORS evidence includes an approved origin success and unapproved origin block
  when CORS behavior changes
- API clients attach auth/session state through the existing service layer and
  map backend errors to safe UI messages
- list endpoints touched by the change have bounded pagination, sort/filter
  rules, and max page-size evidence
- public or multi-consumer endpoint changes update the API contract or equivalent
  documentation

### Backend Correctness

- cross-stack changes define route, method, auth, role/tier behavior,
  request/response schema, stable error shape, audit behavior, and retry or
  duplicate-submit behavior before implementation
- cross-stack evidence correlates the same user action through UI, API request,
  server-side validation, data/source access, response rendering, and audit ID
- changed backend code preserves route/service/repository boundaries: routes
  handle HTTP, services handle business and policy decisions, repository or
  selector utilities handle database access
- domain errors are mapped once by a global handler into stable safe responses
  with request or audit IDs
- structured logs for changed paths include request ID, route, tier, policy or
  failure reason, latency, and no secrets or raw PII
- agentic or tool-calling backend changes define stage responsibility, autonomy
  budgets, allowed tools, argument/result validation, trace fields, fallback
  behavior, memory policy, and escalation rule
- tool failures become structured observations with retry, fallback,
  clarification, or safe failure. They are not accepted as verified evidence.
- critical query SQL is visible
- `total_credit_score` parsing is correct
- TRL synonym mapping works
- follow-up context works
- no truncated SQL
- no guessed unsafe join key
- prompt/model changes include contract, parser behavior, edge cases, and
  regression evidence for the original failure
- one-way progress or answer streaming uses SSE unless bidirectional behavior
  justifies WebSocket; either path proves auth, disconnect cleanup, reconnect or
  bounded retry, and tier-safe chunk filtering
- long-running reports, exports, enrichments, or model-heavy batches are
  idempotent jobs or explicitly justified synchronous work with timeout behavior
- caches touched by the change prove TTL, tier/filter-safe keys, invalidation on
  write, and no use as authoritative state
- upload or generated-file changes prove type, size, path, name, storage, and
  tier validation
- spreadsheet export or template-edit changes prove reopened file inspection,
  sheet preservation, formula validation, row/header parity, safe cell typing for
  dates and identifiers, and no spreadsheet formula-injection payloads

### Development Process

- implementation work is classified as small, focused, cross-stack, or
  release-scale with in-scope behavior, out-of-scope behavior, assumptions,
  dependencies, top risks, and quality gates
- feature or scaffold requests are classified as existing NRG feature, isolated
  experiment, or explicit new product. Generic external stacks or scaffolds do
  not override NRG architecture without an explicit migration decision,
  rollback path, and evidence plan.
- feature plans map changed data, backend, frontend, auth/tier, security,
  config, dependency, deploy, test, and evidence surfaces before implementation
- technology or architecture changes include quantified requirements,
  alternatives rejected, trade-offs, migration plan, rollback path, and evidence
  plan. Trendiness is not a sufficient reason.
- multi-task work has a concrete plan with task ids, dependencies, file
  ownership, test commands, and verify commands
- parallel or delegated tasks have disjoint write scopes or an explicit
  integration owner
- agentic execution has max iteration/tool-call/time budgets, stop conditions,
  trace evidence, and a named escalation point for destructive actions,
  repeated failures, uncertain policy decisions, or security/tier ambiguity
- behavior changes include a failing test first, or a documented equivalent
  evidence gate when TDD is not appropriate
- self-review findings are recorded as CRITICAL, HIGH, MEDIUM, or LOW.
  CRITICAL and HIGH findings are fixed before delivery or explicitly carried as
  blockers with the smallest next action.
- spec compliance review happens before code quality/security review
- tests, lint/type checks, and security checks are run when relevant to changed
  files
- browser automation uses clean contexts, explicit auth fixtures, stable
  user-facing locators, deterministic waits or assertions, and captures
  console/network findings plus screenshots or trace/video artifacts when
  produced
- mocked browser tests document every mocked endpoint and cannot prove auth,
  tier filtering, audit, security, or query correctness for final acceptance
- destructive branch, worktree, or cleanup actions require explicit human
  confirmation
- memory updates are selective, durable, and written to repo `.claude/memory/`
  before any local memory mirror; no automatic `/memories`, `.memories`,
  `.learnings`, or `.improvements` logs
- bug or correction memories include attempted task, observed failure,
  evidence, root cause, fix applied, prevention rule, and regression or
  acceptance check
- feature requests are routed to backlog, spec, issue, or implementation plan
  only when they change product scope; command failures are not memory unless
  reproducible, recurring, or operationally important

### Frontend Quality

- frontend work modifies the existing `frontend/` app unless an isolated
  experiment is explicitly requested
- no console errors
- no failed network requests during normal flow
- no raw JSON
- no `undefined`, `null`, or `NaN` visible
- reusable tokens/primitives drive buttons, inputs, badges, cards/tool panels,
  dialogs, tables, charts, toasts, and skeletons
- design choices match NRG's trust-and-authority analytics surface rather than
  unrelated ecommerce, portfolio, mobile-app, or landing-page patterns
- significant visual redesigns state the role/task, trust-and-authority tone,
  technical constraints, and credibility cue; decorative choices are justified
  by scanning, trust, explanation, or task completion
- design tokens, component specs, wireframes, concept screens, sitemaps, and flow
  diagrams are tied to real NRG routes, role/tier workflows, production files,
  accessibility requirements, responsive behavior, and audit/proof paths
- wireframes and concept screens are marked as proposals unless implemented in
  `frontend/` and verified against the running app
- changed images, videos, fonts, downloads, or generated visual assets reference
  real files/imports, reserve stable dimensions, expose accessible alternatives
  when informative, and have browser network evidence showing no broken asset
  requests
- functional icons use the existing icon system or accessible SVG icons; emojis
  are not used as control icons, status proof, or navigation affordances
- Lucide icons are preferred for common NRG actions/statuses because the app
  already uses `lucide-react`; introducing another icon source requires a reason
  and bundle/build evidence
- changed major screens have a documented role/tier, user task, entry path,
  next action, success state, and failure state
- complex proof, SQL, citations, filters, and table details use progressive
  disclosure instead of overwhelming the first view
- empty and error states provide a safe next action and preserve audit clarity
- significant screen changes include design rationale: user problem,
  constraint, chosen pattern, rejected alternative, and verification plan
- changed components show relevant loading, disabled, empty, error, success,
  hover, and focus states
- changed frontend code keeps API response shapes typed at the service boundary
  and models async UI with explicit states
- changed screens preserve semantic landmarks, coherent heading order, readable
  body text, and native HTML semantics before ARIA
- static visual rules use the token/utility/component styling system, not
  scattered inline styles
- changed screens show clear visual hierarchy: primary content/action,
  secondary metadata, tertiary helper text, and grouped spacing
- visual review fixes start from a running app URL, identify the source and
  styling target, classify issues as P1/P2/P3, and include before/after
  viewport screenshots for changed routes
- visual review covers overflow, overlap, alignment, spacing consistency,
  blocked touch targets, missing focus states, contrast failures, and responsive
  breakage
- status, trend, and risk indicators are not communicated by color alone
- numeric table columns are aligned and formatted for comparison
- destructive actions are visually scoped and require confirmation when they
  can alter data, access, or audit state
- sortable, filterable, paginated, or live-updating lists use stable IDs as
  keys
- data fetching follows the existing service/query layer; ad hoc fetch
  waterfalls require justification
- animations respect reduced-motion preferences
- motion uses purposeful 150-300ms transform/opacity transitions, avoids
  `transition-all`, and does not rely on continuous decorative animation
- fixed and overlay elements use a small z-index scale rather than arbitrary
  large z-index values
- icon-only buttons, form controls, async status updates, and proof controls
  have accessible names, labels, or announcements
- touch targets are at least 44x44px with enough spacing, browser zoom remains
  enabled, and hover-only controls have keyboard/touch alternatives
- no horizontal overflow on mobile
- all navigation links work
- all empty and error states are human-readable

### Performance

- page load measured
- query latency measured
- critical query latency measured
- load test request count greater than zero if load test is claimed
- local C4 and production C4 are not interchangeable; local C4 may be accepted
  from the read-model evidence, but production readiness requires the
  1000-user cluster/deployed run
- schema changes prove migration execution on a fresh database and document
  additive/backfill/rollback behavior for risky changes
- new indexes, constraints, or denormalized data are tied to measured access
  patterns, `EXPLAIN ANALYZE`, or a stated correctness rule
- large backfills are batched or otherwise bounded, and live-table index changes
  avoid long write locks where the database supports it
- background jobs, streaming, external calls, and API requests have timeout,
  retry, and graceful-failure evidence when touched
- frontend build/deploy claims include `npm run build`, served preview or
  deployed URL, and route smoke evidence for changed screens
- frontend major-screen changes include Web Vitals or Lighthouse evidence when
  feasible
- added heavy dependencies or charting code have a bundle/lazy-load rationale

### Handover

- README current
- production readiness summary current
- walkthrough guide current
- API contract current
- operations runbook current
- security/compliance note current
- screenshots current

## Final Acceptance Report

Use this format:

```text
ACCEPTANCE REPORT
Date:
Scope:

Accepted: YES/NO

Evidence reviewed:
- ...

Passed gates:
- ...

Failed gates:
- ...

Unknown/unproven:
- ...

Required next actions:
1.
2.
3.

Commit SHA if committed, or not committed:
```

## Failure Rule

If a gate fails, do not soften it. Write `FAILED`, explain why, and state the
smallest next action that would convert it to evidence.
