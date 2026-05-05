# API Endpoint Matrix

Date: 2026-05-03

## Scope

This matrix documents the FastAPI route surface registered by `src/api/main.py`
and the route modules it composes. It is intentionally
contract-focused: method, path, owner, access guard, and purpose.

Framework documentation routes are excluded from the inventory:

- `/openapi.json`
- `/docs`
- `/docs/oauth2-redirect`
- `/redoc`

The SPA fallback is included because it is a registered project route.

## Route Inventory

| Method | Path | Owner | Access Guard | Purpose |
|---|---|---|---|---|
| `GET` | `/admin/dpdp/stats` | `src/api/routes/dpdp.py` | Authenticated admin or government role | Administrative operational status |
| `GET` | `/admin/slo` | `src/api/routes/admin.py` | Authenticated admin/system role only | Administrative operational status |
| `GET` | `/api/admin/rbac` | `src/api/routes/admin.py` | Authenticated admin role only | RBAC policy administration |
| `POST` | `/api/admin/rbac` | `src/api/routes/admin.py` | Authenticated admin role only | RBAC policy administration |
| `DELETE` | `/api/admin/rbac/{persona_name}` | `src/api/routes/admin.py` | Authenticated admin role only | RBAC policy administration |
| `GET` | `/api/admin/rbac/{persona_name}` | `src/api/routes/admin.py` | Authenticated admin role only | RBAC policy administration |
| `PUT` | `/api/admin/rbac/{persona_name}` | `src/api/routes/admin.py` | Authenticated admin role only | RBAC policy administration |
| `POST` | `/api/feedback` | `src/api/routes/feedback.py` | Public feedback intake; validated bounded payload | Feedback submission |
| `GET` | `/api/health/killer_queries` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `POST` | `/api/ingest` | `src/api/routes/ingest.py` | Authenticated Tier 1 only | Submit document ingest job |
| `GET` | `/api/ingest/{job_id}` | `src/api/routes/ingest.py` | Job status by id; no payload disclosure beyond job metadata | Read ingest job status |
| `GET` | `/api/internal/tier_diff` | `src/api/routes/graph.py` | Authenticated Tier 1 only; audit-bound internal diagnostics | Internal tier response-shape diagnostics |
| `GET` | `/api/metrics` | `src/api/routes/admin.py` | Authenticated Tier 1 or admin/system metrics JSON/Prometheus | Metrics surface |
| `GET` | `/api/providers/health` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/api/query/stream` | `src/api/routes/query.py` | Authenticated; tier filtering, rate limits, audit event binding | Streaming answer endpoint |
| `POST` | `/api/query/stream` | `src/api/routes/query.py` | Authenticated; tier filtering, rate limits, audit event binding | Streaming answer endpoint |
| `POST` | `/api/reindex` | `src/api/routes/admin.py` | Authenticated admin/system role only | Trigger vector reindex job |
| `POST` | `/api/telemetry` | `src/api/routes/telemetry.py` | Public client telemetry intake; allowlisted event names only | Client telemetry submission |
| `GET` | `/api/vectors/health` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/audit/event/{event_id}` | `src/api/routes/audit.py` | Authenticated; admin can list broadly, users see own events | Fetch a single audit event |
| `GET` | `/audit/events` | `src/api/routes/audit.py` | Authenticated; admin can list broadly, users see own events | List audit events under role scope |
| `GET` | `/audit/verify` | `src/api/routes/audit.py` | Authenticated; admin can list broadly, users see own events | Verify HMAC audit-chain health |
| `POST` | `/auth/login` | `src/api/routes/auth.py` | Public login; rate-limited; sets HttpOnly auth cookies | Authentication/session control |
| `POST` | `/auth/logout` | `src/api/routes/auth.py` | Authenticated; revokes bearer or auth cookies | Authentication/session control |
| `POST` | `/auth/refresh` | `src/api/routes/auth.py` | Refresh-token cookie or bearer context; rotates tokens | Authentication/session control |
| `GET` | `/auth/session` | `src/api/routes/auth.py` | Optional auth context; returns authenticated=false when absent | Authentication/session control |
| `POST` | `/auth/sso/callback` | `src/api/routes/auth.py` | Public SSO control surface; provider config required for callback | Authentication/session control |
| `GET` | `/auth/sso/login` | `src/api/routes/auth.py` | Public SSO control surface; provider config required for callback | Authentication/session control |
| `GET` | `/auth/sso/status` | `src/api/routes/auth.py` | Public SSO control surface; provider config required for callback | Authentication/session control |
| `GET` | `/collaborations` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Collaboration edges |
| `POST` | `/consent` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `DELETE` | `/consent/{scope}` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `GET` | `/dpdp/consents` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `POST` | `/dpdp/erase` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `GET` | `/dpdp/export` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `GET` | `/funding` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Funding records |
| `GET` | `/health` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/health/all` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/health/db` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/health/llm` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/health/qdrant` | `src/api/routes/health.py` | Public operational health; no user data payload | Operational health/readiness |
| `GET` | `/labs` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Lab records |
| `POST` | `/login` | `src/api/routes/auth.py` | Public login; rate-limited; sets HttpOnly auth cookies | Authentication/session control |
| `POST` | `/logout` | `src/api/routes/auth.py` | Authenticated; revokes bearer or auth cookies | Authentication/session control |
| `GET` | `/me/consents` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `DELETE` | `/me/data` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `GET` | `/me/data` | `src/api/routes/dpdp.py` | Authenticated DPDP consent/data-subject route | DPDP consent and data-subject operation |
| `GET` | `/metrics` | `src/api/routes/admin.py` | Authenticated admin/system Prometheus metrics | Metrics surface |
| `GET` | `/patents` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Patent catalogue |
| `GET` | `/projects` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Project catalogue |
| `GET` | `/publications` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Publication catalogue |
| `POST` | `/query` | `src/api/routes/query.py` | Authenticated; tier filtering, rate limits, audit event binding | Main answer-engine query endpoint |
| `GET` | `/query/graph` | `src/api/routes/graph.py` | Authenticated; tier filtering, rate limits, audit event binding | Graph query/read endpoint |
| `POST` | `/query/graph` | `src/api/routes/graph.py` | Authenticated; tier filtering, rate limits, audit event binding | Graph query/read endpoint |
| `POST` | `/refresh` | `src/api/routes/auth.py` | Refresh-token cookie or bearer context; rotates tokens | Authentication/session control |
| `GET` | `/research-documents` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Research document records |
| `GET` | `/researchers` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Researcher catalogue |
| `GET` | `/stats` | `src/api/routes/data.py` | Authenticated; tier-filtered data response | Aggregated platform stats |
| `GET` | `/{full_path:path}` | `src/api/routes/spa.py` | Public SPA fallback; serves static frontend shell | Frontend shell fallback |

## Contract Notes

- Auth is enforced primarily through `get_current_user`, `AuthContextMiddleware`,
  route-level role/tier checks, and response filtering rather than OpenAPI
  security declarations.
- Query and graph routes must remain audit-bound and tier-filtered.
- Data catalogue routes must return tier-shaped payloads. Tier 3 receives
  anonymized or aggregated records where the response-filter policy requires it.
- Health routes are public operational probes and must not return user data.
- Metrics and administrative routes require admin/system or explicitly scoped
  Tier 1 access as listed above.

## Tier And Response-Shape Contracts

| Route family | Tier contract | Response-shape contract |
|---|---|---|
| Auth/session routes | Public login/SSO entry points or authenticated session mutation | JSON auth/session payloads; tokens are returned through the established auth contract and cookies where configured. |
| Query and stream routes | Authenticated; tier filtering and audit binding are mandatory | `/query` returns an answer envelope with audit event id, tier-shaped source rows/citations, and normalized answer fields. `/api/query/stream` returns SSE events without blocking initial stream start on async answer-record writes. |
| Data catalogue routes | Authenticated; Tier 1 full rows, Tier 2 aggregated/safe fields, Tier 3 anonymized or aggregated fields | JSON arrays or aggregate objects after last-mile response filtering. NULL aggregate inputs must remain NULL unless the endpoint contract explicitly defines a zero count. |
| Graph and tier-diff routes | Authenticated; Tier 1 for internal tier diagnostics | JSON graph/tier-diff payloads after tier response-shape filtering. |
| DPDP routes | Authenticated data-subject or admin/government scope depending on path | JSON consent/export/erase status payloads; no cross-user data leakage. |
| Audit routes | Authenticated; admin broader scope, users own events only | JSON audit event, list, or verification payloads with audit ids and chain status. |
| Health/provider/vector routes | Public operational probes | Small JSON health payloads using the normalized health response contract; no user or PII fields. |
| Metrics/admin routes | Admin/system or explicit Tier 1 metrics scope | Prometheus text or bounded JSON metrics/admin payloads; no raw secrets or user PII. |
| Ingest routes | Authenticated Tier 1 only | JSON job creation/status payloads bounded to job metadata. |
| SPA fallback | Public | Static frontend shell response. |

## Drift Guard

`tests/api/test_api_endpoint_matrix.py` compares this table against the
registered FastAPI `APIRoute` method/path inventory. If a route is added,
removed, or renamed, update this matrix in the same change.
