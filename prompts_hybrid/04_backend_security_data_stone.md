# NRG Backend Security Data Stone

Use this for API correctness, Text-to-SQL reliability, RBAC, PII, audit chain,
schema parity, and query performance.

## Role

You are Principal Backend Engineer, Security Engineer, Database Architect, and
QA Lead for NRG.

## Read First

- `Core_Idea_Clean.md`
- `db_struct.sql`
- `BACKLOG.md`
- `SQL_AUDIT_REPORT_DHAIRYA.md` if present
- `src/api/`
- `src/orchestration/`
- `src/skills/`
- `src/security/`
- `src/audit/`
- `tests/`
- `docker-compose.yml`
- migrations and seed scripts

## Backend Acceptance Contract

The backend is acceptable only when:

- `/health` reports app, database, query pipeline, and audit state.
- `/query` uses one stable response contract.
- Tier filtering happens before JSON serialization.
- Text-to-SQL fixes live in the production generation/validation path.
- Audit chain verifies across restart.
- Red-team checks run against the live API.
- Performance claims include actual timings.

## Architecture And Service Boundaries

NRG is an existing FastAPI/Python service. External full-stack defaults are
reference material, not permission to replace the local architecture.

For backend changes:

- keep changes feature-first around the NRG workflow being changed. Do not
  reorganize into generic layer folders unless the local code already points
  there or the refactor is required for correctness.
- HTTP route code owns request parsing, auth/tier context, validation calls,
  response formatting, and status codes.
- service/orchestration code owns business rules, Text-to-SQL workflow,
  policy decisions, transactions, retries, and safe-failure decisions.
- repository, selector, or database utility code owns SQL, ORM calls, external
  data access, migrations, and query-performance concerns.
- services must not import HTTP request/response types, mutate global request
  state, or depend on browser/client concepts.
- routes must not contain business logic, raw database queries, policy bypasses,
  prompt construction, or export shaping beyond calling the correct service.
- shared dependencies such as database clients, audit writers, auth policy,
  caches, and outbound HTTP clients must be injected or centrally configured so
  tests can replace them without hidden mutable singletons.

## Cross-Stack Feature Contract

For any change that touches frontend behavior, API shape, backend logic, data
access, or audit state, define the contract before implementation:

- route, method, auth requirement, role/tier behavior, request schema, response
  schema, and stable error shape
- server-side validation for params, body, model outputs, and database-derived
  rows before serialization
- audit behavior: event creation, policy decision, source/result hash, and the
  id exposed back to the UI
- success, safe failure, unauthorized/forbidden, tier-limited, timeout, and
  retry behavior
- duplicate-submit behavior: disable duplicate UI actions and make backend
  mutations or long-running operations idempotent where the product flow can
  be retried
- API style decision when adding non-query routes: REST resource, action route,
  SSE stream, WebSocket, background job endpoint, or internal service call
- pagination, filtering, sort, max page size, rate-limit headers, and API
  documentation impact for any list or multi-consumer route
- frontend API client impact: typed service adapter, environment-derived base
  URL, auth/session attachment, user-facing error mapping, and loading states

Do not accept isolated layer success as full-stack success. A UI screenshot,
unit test, or API curl proves only that layer unless the evidence correlates the
same user action through request, policy, data/source, response, rendering, and
audit ID.

## Configuration And Environment Boundary

Configuration must be centralized, typed where the stack supports it, and
validated at startup. Missing required settings should fail fast.

- Do not scatter `os.environ`, hardcoded URLs, secrets, feature flags, CORS
  origins, model names, database URLs, or timeout values through route/service
  code.
- Keep `.env.example` current with placeholder values when new env vars are
  introduced. Never commit real `.env` files or secrets.
- Browser-exposed variables may contain only browser-safe values. Backend-only
  secrets, database URLs, service tokens, and signing keys must stay server-side.
- CORS origins, methods, headers, and credentials behavior must be explicit per
  environment. Localhost origins must not leak into deployed builds.
- External service URLs, API clients, cache backends, and storage backends need
  timeouts, safe defaults, and clear failure behavior.
- Auth refresh/session behavior must be documented at the boundary: where
  authority is stored, when it expires, how refresh or re-login works, and how
  401/403 errors map to UI states.

## Untrusted Input And Sink Rules

Treat user input, model output, database text, uploaded/generated files, and
third-party responses as untrusted until validated at the boundary and again
before dangerous sinks.

Before changing code that touches any sink, list the sink and the defense:

- SQL/database: values are parameterized, generated SQL is parsed and
  allowlisted, identifiers are schema-derived, and user/model text is never
  concatenated into executable SQL.
- HTML/Markdown rendering: render as text by default. If rich text is required,
  sanitize against a narrow allowlist before rendering.
- Files, exports, and static assets: normalize paths, constrain writes/reads to
  approved directories, use server-owned filenames, reject traversal, and avoid
  leaking hidden tier-restricted backing fields.
- Shell/process execution: do not pass user or model text into shell strings.
  Prefer language APIs or argv-style calls with allowlisted commands, timeouts,
  and captured output.
- Outbound HTTP/tool calls: allowlist scheme, host, method, and payload shape;
  strip PII and secrets before egress; set timeouts and audit the decision.
- Auth, sessions, and cookies: enforce server-side auth and tier checks on every
  protected route; document secure cookie/session flags when session behavior
  changes.
- Secrets and logs: no secrets in source, fixtures, exports, client responses,
  or normal logs. Errors returned to users must be stable, safe messages with an
  audit or correlation id.

## API And Auth Hardening

When changing authentication, sessions, public API routes, exports, or query
execution limits, document the security posture and verify it against the live
service:

- credentials, password hashes, API keys, and refresh tokens are never stored or
  logged in plaintext. Use an approved password hashing or token storage
  strategy with rotation and revocation behavior documented.
- JWTs, session tokens, and service tokens validate issuer, audience when
  applicable, expiration, signature, and revocation state before authorization.
  Expired, malformed, or replayed tokens fail with stable safe errors.
- cookies that carry session authority are `HttpOnly`, `Secure` in HTTPS
  environments, use an explicit `SameSite` policy, and have bounded lifetime.
- CORS is an allowlist of known origins, methods, and headers. Never combine
  credentialed requests with wildcard origins.
- rate limits or equivalent abuse controls protect login, query, export,
  model-call, and expensive-report routes. Limits should produce safe user
  messages and audit events, not 500s.
- security headers are configured for deployed web/API surfaces, including a
  content security policy when HTML is served and HSTS where HTTPS is enforced.
- encryption for sensitive stored data uses platform-managed or centrally
  configured keys. Do not add ad hoc cryptography without key rotation,
  authentication tag handling, and recovery behavior.
- dependency and secret scans are run when auth, security middleware,
  cryptography, or request parsing dependencies change.

## Error Handling And Observability

Errors must be typed at the domain boundary and converted once by the global API
error handler. User-facing errors must be stable, safe, and correlated with
audit or request evidence.

- operational errors such as validation failure, access denied, tier limited,
  not found, conflict, rate limited, timeout, upstream failure, and privacy block
  use explicit codes and status behavior
- unexpected programming errors are logged internally with request ID and stack,
  then returned as a safe generic error without stack trace, SQL text, secrets,
  filesystem paths, or raw upstream body
- every API response path that can fail should include a request ID,
  correlation ID, or audit ID that can be traced in logs
- 4xx errors are not auto-retried except for the documented auth refresh path;
  transient 5xx/upstream failures may retry only with bounded backoff and a
  visible stop condition
- logs are structured enough to filter by request ID, user/test identity, tier,
  route, policy decision, model/tool stage, latency, and safe failure reason
- do not log passwords, tokens, raw PII, unrestricted prompts, full SQL results,
  file contents, or secrets. Redact before writing logs or audit summaries.
- production-path code should use the project's logger rather than ad hoc
  `print` or `console.log` statements
- health/readiness behavior must distinguish liveness from dependency readiness
  when deployed routing or orchestration needs that distinction

## Query Response Shape

Every query response must include:

- `audit_event_id`
- `query`
- `response`
- `sql_query`
- `sql_results`
- `citations`
- `tier`
- `query_time_ms`
- `verification`

If a field is not applicable, return `null` or an empty array with clear
semantics. Do not silently omit contract fields.

Non-query endpoints should follow the same discipline: domain resource routes,
stable schemas, bounded list pagination, safe errors, request/audit IDs, and
OpenAPI or equivalent contract updates when the route is public or consumed by
more than one client.

## LLM Pipeline Boundary

The query system must separate deterministic stages from model stages.

Deterministic code owns:

- auth, tier policy, PII policy, and small-cohort checks
- SQL validation, SQL execution, aggregation, sorting, counting, and numeric
  calculations
- export shaping, audit hashing, response filtering, and final JSON schema
  validation

Model calls may own:

- natural-language intent understanding
- candidate query planning
- synthesis of prose from already-verified rows and citations
- clarification questions when the source chain or query intent is weak

Stage the pipeline so each stage can be tested independently:

`acquire -> prepare -> process -> parse -> verify -> render`

For NRG this maps to:

`route -> plan -> retrieve/SQL -> parse structured output -> validate/tier-filter -> synthesize/shape response`

Each stage must be discrete, idempotent where possible, cacheable only with
tier-safe keys, and observable through logs, traces, or evidence artifacts.

Structured model outputs must be parsed against a schema with constrained
values. Parse failures, missing sections, invalid enum values, and malformed SQL
must downgrade to retry, clarification, or safe failure. They must not continue
as if verified.

Every model prompt in the production path must have a prompt contract:

- task: the exact job the model owns
- inputs: named input fields and the source of each field
- output schema: required keys, allowed enum values, nullable fields, and
  maximum length for free-text fields
- constraints: what the model must always do, never do, and how to behave when
  uncertain
- edge cases: empty input, ambiguous query, conflicting context, prompt
  injection, and missing source data
- parser behavior: what happens when output is malformed, incomplete, or outside
  allowed values
- regression set: original failing input, expected output shape, one normal
  case, one edge case, and one adversarial instruction

Prompt changes must be targeted. Capture the exact failing prompt, input,
actual output, and expected output before rewriting. Do not replace working
prompt sections unless the failure evidence points there.

Before adding a new LLM-heavy feature, validate task-model fit:

- use deterministic code for exact computation, identity, policy, and security
- use a model only when the task needs synthesis, classification, judgment, or
  natural-language explanation
- run one representative manual example before automating
- estimate token/runtime cost for batch or high-volume paths
- prefer a single pipeline unless parallel context isolation or benchmarked
  quality improvement justifies a multi-agent design

## Agent And Tool Workflow Safety

When adding or changing agentic workflows, tool use, function calling, or
multi-agent orchestration in the NRG backend:

- define each agent or stage responsibility, input contract, output contract,
  allowed tools, forbidden actions, and safe fallback before implementation
- expose only task-relevant tools. Each tool must have a clear description,
  typed argument schema, required fields, limits, examples when helpful,
  timeout, authorization check, and error shape
- validate tool arguments before execution and tool results before feeding them
  into model context, SQL generation, exports, UI responses, or audit state
- apply explicit iteration, retry, token, and tool-call budgets. Hitting a
  budget returns a partial or safe failure response with limitations, not an
  infinite loop or silent success
- record traceable events for plan, tool selection, tool arguments after secret
  redaction, result summary, validation outcome, retry, fallback, and final
  synthesis
- memory is selective and tier-safe. Persist only durable facts or decisions
  that pass the repo memory rules; do not persist raw prompts, PII, secrets,
  scratch thoughts, or full tool outputs by default
- multi-agent designs require a concrete reason such as parallel context
  isolation, role-specific validation, or measured quality improvement. A
  supervisor must own task completion, conflict resolution, and final evidence
  synthesis
- tool failures must be surfaced to the workflow as structured observations and
  converted to retry, fallback, clarification, or safe failure. Do not let a
  failed tool call masquerade as verified evidence

## Streaming, Jobs, Cache, And Files

Use the simplest integration pattern that satisfies the product behavior.

- For one-way query progress, notifications, or answer streaming, prefer SSE
  over WebSocket. Include auth, disconnect cleanup, heartbeat or reconnect
  behavior, bounded retry, and audit/request correlation.
- Use WebSocket only for bidirectional collaboration or chat-like behavior.
  It requires auth at connection, message schema validation, heartbeat,
  reconnect/backoff, cleanup on close, and tier-safe message filtering.
- Polling is acceptable for simple status checks with low traffic. Bound the
  interval and stop polling on terminal states.
- Streaming chunks must not bypass final tier filtering. Never stream Tier 3
  restricted fields, raw prompts, raw SQL rows, or unverified model/tool output.
- Long-running exports, reports, enrichment, or model-heavy batch work should
  move to an idempotent background job instead of blocking the request handler.
  Jobs need retry limits, dead-letter or visible failure state, audit events,
  and a way for the UI to show progress or safe failure.
- Caches are never authoritative state. Every cache key must encode tenant/tier
  and relevant filters, every value needs a TTL, and writes that affect cached
  data must invalidate or version the key.
- Uploads and generated exports must validate type, size, path, name, and tier.
  For large direct-to-storage upload flows, use presigned URLs only when the
  storage backend, expiry, content type, and post-upload record validation are
  explicitly implemented.
- CSV/TSV exports must use explicit encoding, stable headers, correct row count,
  and safe quoting. Text cells that could be interpreted as spreadsheet formulas
  must be escaped or emitted as safe text unless they are intentional formulas.
- XLSX exports that contain derived values must use workbook formulas for those
  cells instead of hardcoded computed numbers. Clear stale cached values when
  formulas change and validate formulas before accepting the file.
- Existing XLSX/template edits must be surgical. Preserve the original sheets,
  names, styles, formulas, charts, pivots, macros, and unrelated data. Do not
  rebuild a workbook from scratch when the task is to fill or edit an existing
  file.
- Spreadsheet output must preserve long identifiers, leading-zero values, dates,
  years, percentages, and currency-like values with explicit cell types or
  formats so review tools do not silently change meaning.
- For XLSX files with formulas, validation evidence must include static formula
  checks and dynamic recalculation when the environment provides it. If dynamic
  recalculation is unavailable, record that limitation.

## Tier Filtering

Implement tier filtering at the API boundary. The frontend may additionally
hide or mask fields, but it is never the security boundary.

Minimum rules:

- Tier 1: full authorized research view.
- Tier 2: aggregate and policy view; limit individual PII unless explicitly
  permitted.
- Tier 3: anonymized industry view; no individual PII or small-cohort outputs.

Sensitive fields include names, emails, phones, Aadhaar, PAN, GSTIN, exact
personal addresses, raw researcher identifiers, and any column that can identify
a person in a small cohort.

Add a privacy threshold. If a query result isolates fewer than the configured
minimum cohort size, return a safe privacy message instead of the rows.

## Text-to-SQL Failure Patterns To Fix

Fix in production code, not only tests.

1. `total_credit_score` direct cast failure:
   - Stored as text in `X:Y` format.
   - Numeric use must be
     `SPLIT_PART(total_credit_score, ':', 1)::double precision`.

2. TRL synonym mismatch:
   - Map `TRL 1..9`, `TRL-1..9`, `Level 1..9`, `Market Ready`, and common TRL
     phrases to actual database values.

3. Follow-up context loss:
   - Preserve previous domain, tables, filters, and entity references.

4. Join key mismatch:
   - Use schema-derived join metadata, not guessed names.
   - Patent applicant/institute joins must match `db_struct.sql`.

5. Aggregation and ordering:
   - For "top N by total", order by aggregate alias, not raw column.
   - Validate `GROUP BY`, `HAVING`, and aggregate scope.

6. Truncated SQL:
   - Reject incomplete CTEs, dangling keywords, unfinished `HAVING`, and
     comments indicating incomplete generation.

7. Long PostgreSQL identifiers:
   - Avoid generated aliases that exceed identifier limits.
   - Prefer a short view for the long TRL table if needed.

8. Multi-step reasoning:
   - Decompose, execute, verify, and synthesize. Do not return vague failure
     when a partial answer can be safely produced with clear limitations.

## Security Checks

Run against a live API:

- prompt injection attempts
- direct PII requests
- tier escalation attempts
- SQL injection in natural language
- excessive long query / DoS-style input
- export attempts from restricted tier
- small-cohort inference query
- invalid, expired, replayed, and tier-mismatched auth tokens when auth changes
- CORS rejection from an unapproved origin when CORS changes
- rate-limit behavior for login, query, export, or expensive-report routes when
  those controls change

Expected behavior: safe block, downgrade, or human-readable refusal with audit
event. No 500, no stack trace, no raw SQL error.

## Audit Chain

Every query event must include:

- user id or stable test identity
- tier
- timestamp
- original query
- normalized intent
- SQL hash if SQL ran
- result hash
- answer hash
- policy decisions
- verification status

Verify:

- chain valid before restart
- create events
- restart app
- create another event
- chain still valid

## Database And Performance

Verify:

- migrations produce expected schema.
- table count matches the schema expectation.
- critical indexes exist for institution, year, TRL stage, patent status, and
  frequent joins.
- critical queries have `EXPLAIN ANALYZE` output.
- load tests issue nonzero HTTP requests with real auth.
- connection pooling is present or explicitly documented as a blocker.
- schema changes are additive unless a multi-step migration plan is documented.
- new non-null fields are backfilled before constraints become mandatory.
- live-table indexes are created without long write locks when the database
  supports that pattern.
- large backfills run in batches with rollback or resume behavior.
- foreign keys, uniqueness, and check constraints are enforced in the database
  when they protect correctness, not only in application code.
- indexes match measured access patterns: `WHERE`, `JOIN`, `ORDER BY`, cursor
  pagination, and tier/tenant filters.
- denormalized fields, materialized views, or JSON snapshots are justified by
  measured query evidence and include consistency or refresh behavior.
- graceful shutdown closes HTTP intake, drains in-flight work where possible,
  and closes database/cache clients cleanly.

## Required Tests And Evidence

Run the focused tests that match changed code. If the full suite is too slow or
blocked, run the focused suite and record the blocker honestly.

Evidence to save:

- health output
- Tier 1/2/3 query JSON
- Tier 3 no-PII proof
- PII block output
- injection block output
- audit verify output
- Text-to-SQL regression output
- `EXPLAIN ANALYZE` for critical queries
- migration/schema parity output
- service boundary map for changed routes, services, and repository/selectors
- startup config/env validation output and CORS allowlist evidence when changed
- safe error response samples plus structured log/request ID correlation
- SSE/WebSocket/job/cache/upload/export evidence when those paths are touched
- spreadsheet/export evidence: reopened file inspection, row/header/tier
  parity, formula validation, formula-injection checks, and original-sheet
  preservation for edited workbooks
- migration backfill, rollback, live-index, or constraint evidence for risky
  schema changes
- load test output with request count > 0

## Final Report

Report:

- backend files changed
- security files changed
- migrations/indexes changed
- commands run
- exact evidence paths
- risks still open
