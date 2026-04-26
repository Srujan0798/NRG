---
name: DB-layer defence-in-depth (third layer below SQL filter and response shape)
description: NRG already has SQL-boundary RBAC + API response-shape filter; add PostgreSQL Anonymizer dynamic masking + native PL/pgSQL HMAC triggers as a third DB-level layer. Defence-in-depth — every layer assumes the others might miss.
type: feedback
---

NRG currently enforces RBAC and PII protection at two layers (SQL boundary + API response shape — see `feedback_tier_shape_boundary.md`). Add a **third, DB-native layer** so even direct-database access (DBA, ORM bypass, manual `psql` patch, future endpoint that forgets the response-shape filter) cannot leak.

Two specific DB-layer mechanisms required:

### 1. PostgreSQL Anonymizer (`pg_anonymizer`) for dynamic masking
- Install: `CREATE EXTENSION IF NOT EXISTS anon CASCADE;`
- Activate dynamic masking: `SELECT anon.start_dynamic_masking();`
- Map masking policies to PostgreSQL roles. Tier 3 sees `12******7890` for Aadhaar even on a raw `SELECT aadhaar_id FROM researchers`.
- Tier 2 sees the same for direct PII columns; aggregates pass through.
- Tier 1 sees full values — application-layer audit logs every access.

### 2. Native HMAC-recompute triggers
- HMAC chain integrity must NOT depend on the application layer. Manual DB patches via `psql` bypass the Python ORM and silently break the chain.
- Add a `BEFORE INSERT OR UPDATE` trigger function in PL/pgSQL that recomputes the HMAC on every row mutation, using a server-side secret (loaded from a Vault-backed extension or `current_setting()`).
- Trigger is `SECURITY DEFINER` so it runs regardless of caller role.
- Validation: `tests/security/test_hmac_db_trigger.py` — manually `UPDATE researchers SET name='X' WHERE id=Y` via raw `psql`; assert HMAC column auto-updated; assert chain still verifies.

**Why:** The first credibility test in any external review is "what if the DB is touched directly?". Two layers (SQL + response-shape) only protect the API path. A government-grade auditor will ask: "what if a DBA logs into the prod cluster and runs a SELECT?" Answer must be: "they see masked PII and any UPDATE re-signs the chain — defence-in-depth all the way down."

**How to apply:**
- LB-1 (`protocols/46_LB1_TIER_SHAPE_FILTER.md`) Phase 3 IMMORTALIZE acceptance extended to include `pg_anonymizer` install + masking policy + role mapping.
- LB-6 (`protocols/51_LB6_SCHEMA_PARITY_58_TABLES.md`) acceptance extended to include the BEFORE-UPDATE HMAC trigger function + test.
- Migrations: `alembic/versions/<new>_pg_anonymizer_install.py` and `<new>_hmac_trigger.py`.
- Document this third-layer defence in `docs/security/THREE_LAYER_DEFENCE.md` (NEW) — agents creating new endpoints or new tables get a checklist.
- Cross-reference Risk #2, #11, #23 in `PRODUCTION_LAUNCH_RISK_REGISTER.md`.

**Source:** The Principal Auditor 2026-04-26. Promoted to permanent rule 2026-04-26.
