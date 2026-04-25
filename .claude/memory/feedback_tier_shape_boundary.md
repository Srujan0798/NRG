---
name: Tier-Shape Boundary Rule
description: NRG RBAC must be enforced at TWO layers — the SQL boundary AND the API response-shape layer; SQL filtering alone is insufficient
type: feedback
---

NRG must enforce the per-tier column allowlist at **two** independent layers:

1. **SQL boundary** — `tier_query_filters` in `rbac_policies.yaml` strips columns from SELECT before execution.
2. **Response-shape boundary** — a last-mile filter in `src/api/main.py` re-applies the tier allowlist to the payload (`sql_results`, `citations`, `retrieval_sources`, SSE chunks) immediately before `JSONResponse(...)` is returned, on every endpoint that ships data: /query, /query/graph, /publications, /stats, /api/query/stream.

**Why:** Single-layer RBAC is one bug away from a DPDP §8(4) violation. The synthesizer/verifier nodes touch raw SQL results in memory; if any future change ever bypasses the SQL filter (e.g. a `SELECT *` debug path, a follow-up query reusing cached rows, a graph endpoint composing across tables), the response layer is the only thing standing between the user and a leaked email/phone/Aadhaar. One leaked PII column ends the IIT-GN engagement.

**How to apply:**
- Any new endpoint that returns DB rows MUST pass through `_apply_tier_response_filter(payload, tier)`. Add a contract test that fails CI if a new endpoint route is registered without it.
- Column allowlist sourced from `rbac_policies.yaml`, never hardcoded per endpoint.
- Add a hypothesis property test: 1000 random sql_results × 3 tiers = 0 disallowed columns. Run on every PR touching `src/api/main.py` or `src/auth/rbac.py`.
- Audit-log every strip event (`pii_strip:tier3:email`) to the per-user audit chain so we can prove later that no PII reached T3 even on payloads that originally contained it.
- See `.claude/QUALITY_BAR.md` "Tier-Shape Boundary" and `docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md` Risk #2.

**Source:** Grok external audit 2026-04-25 GAP-1 — promoted to permanent rule 2026-04-26.
