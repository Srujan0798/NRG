# NRG Evidence Acceptance Stone

Use this as the final proof gate. It does not build features. It decides
whether a feature, flow, or release can be accepted.

## Role

You are the release acceptance engineer. You accept only evidence, not claims.

## Rule

No completion claim is valid without fresh verification from this session.

## Minimum Acceptance Gate

Before accepting any NRG claim, require these ten facts or mark the claim
`UNKNOWN`/`FAIL`:

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

For deployed, handover, production, or show-readiness claims, also require the
deployment-gate proof in `prompts_hybrid/09_deployment_gate_stone.md`. Localhost
evidence is not deployed evidence.

Current performance truth: local quota-neutral 1000-user C4 passed in
`evidence/2026-05-02/guru_shishya_validation/c4_rerun/165_quality_bar_scorecard_60s_4workers_bounded_audit_executor.json`.
Local C4 evidence is local-only unless the evidence folder names a deployed
target. Deployed readiness still needs sovereign-cluster/deployed replay,
production Qdrant/API targets, and founder signing.

For broad validation assignments, require
`prompts_hybrid/08_full_coverage_validation_campaign_stone.md` and accept only
the declared coverage matrix, not vague "all possible cases" claims.

---

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
| local C4 met | local Locust or scorecard output with request count, P50/P95/P99, failure rate, environment mode, and audit verification after load |
| production C4 met | 1000-user sovereign-cluster/deployed Locust CSV/HTML, request count, P50/P95/P99, failure rate, worker/logging settings, and audit verification after load |
| tests pass | exact command output |
| performance met | measured timings, not estimates, with local-vs-deployed scope stated |
| frontend polished | screenshots and console/network check |
| visual design review is fixed | target URL, framework/styling/source target, issue priority, changed file, before/after screenshots at affected viewports, and console/network check |
| browser automation/E2E is valid | command output, target URL, viewport coverage, clean context/auth fixture, stable locator strategy, assertions, screenshots or trace/video artifacts when produced, console/network findings, API/audit evidence for the same flow, and documented mock boundaries |
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
| handover ready | file list and freshness check |

---

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

If a file is not applicable, include it with an explanation. Missing evidence must remain visible.

---

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
- table renders
- graph renders when useful
- citations render
- audit proof opens
- export/copy works or blocked with clear reason
- exported CSV/XLSX rows match the rendered, tier-filtered table row count
- export headers contain only allowed columns for that tier
- exported dates and long identifiers are not mangled by spreadsheet defaults
- exported text that starts with formula-triggering characters is escaped or
  written as safe text unless it is an intentional system-generated formula

### Security
- changed code has a sink inventory for SQL/database, HTML/Markdown,
  files/exports/assets, shell/process execution, outbound HTTP/tool calls,
  auth/session behavior, secrets, and logs when those areas are touched
- every changed sink validates or allowlists untrusted user input, model output,
  database text, generated files, or third-party responses before use
- PII direct request blocked
- injection blocked
- Tier 3 raw JSON contains no PII
- Tier 3 export contains no PII keys, hidden columns, or raw backing fields
- small-cohort query blocked or generalized
- audit event created for allowed and blocked requests

### Backend Correctness
- critical query SQL is visible
- `total_credit_score` parsing is correct
- TRL synonym mapping works
- follow-up context works
- no truncated SQL
- no guessed unsafe join key
- streaming chunks do not bypass final tier filtering
- generated SQL and identifiers are parsed, allowlisted, or schema-derived
  before execution

### Frontend Quality
- no console errors
- no failed network requests during normal flow
- no raw JSON
- no `undefined`, `null`, or `NaN` visible
- all navigation links work
- all empty and error states are human-readable
- no horizontal overflow on mobile
- icon-only buttons, form controls, async status updates, and proof controls
  have accessible names, labels, or announcements
- changed screens preserve semantic landmarks, coherent heading order, readable
  body text, and native HTML semantics before ARIA

### Performance
- page load measured
- query latency measured
- critical query latency measured
- load test request count greater than zero if load test is claimed
- local C4 and production C4 are not interchangeable; production readiness
  requires the 1000-user cluster/deployed run

---

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

If a gate fails, do not soften it. Write `FAIL`, explain why, and state the smallest next action that would convert it to evidence.
