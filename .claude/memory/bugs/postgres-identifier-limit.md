---
name: PostgreSQL 63-byte identifier limit (62-char column trap)
description: PostgreSQL truncates identifiers > 63 bytes silently. The `innovations_at_various_stages_of_technology_readiness_level` column is 62 chars; ANY LLM-generated alias (`_count`, `_summary`) triggers a fatal truncation exception. Rename or pre-alias via VIEW.
type: feedback
---

PostgreSQL enforces a strict **63-byte limit** on all identifiers (table names, column names, aliases). The `db_struct.sql` schema contains a column at the worst possible length:

`innovations_at_various_stages_of_technology_readiness_level` — **62 characters**.

Any alias an LLM-generated SQL statement appends — `_count`, `_summary`, `_total`, `AS x` (almost any pattern) — pushes the identifier past 63 bytes and triggers PostgreSQL error code `42602: identifier "<name>" will be truncated to "<truncated>"`. On many configurations this is fatal (some clients render it as a warning + auto-truncation, but the resulting truncated alias then collides with itself or breaks downstream column references).

Three independent external reviews flagged this as a near-certain crash during the user-acceptance session. The risk is high because the column is referenced in the killer Text-to-SQL queries (TRL-stage analysis is the canonical Source #2 / Dhairya pattern Q5/Q17).

**Why:** Column-naming is downstream of the official `db_struct.sql` schema (Source #3). We cannot unilaterally rename the production schema, but we CAN expose it to the LLM under a safe alias.

**How to apply:**
- Either: (a) rename the column in `db_struct.sql` itself (requires professor sign-off — schema is theirs) to e.g. `tech_readiness_stage`, OR (b) create a permanent PostgreSQL VIEW `vw_innovations_trl` that pre-aliases the column to a safe length, and route the semantic layer + LLM prompts at the VIEW, never the raw table.
- Either path is enforced in LB-6 acceptance criteria (`protocols/51_LB6_SCHEMA_PARITY_58_TABLES.md`). The semantic layer (LB-8) MUST emit only the safe alias.
- Validate with `tests/data/test_postgres_identifier_safety.py`: enumerate all column names in `db_struct.sql`, flag any > 60 chars (10% safety margin), and assert each has a corresponding VIEW or rename in the migration tree.
- General rule: if any future column exceeds 55 chars, treat it as a bug at schema-design time. PostgreSQL's 63-byte limit applies to every alias an LLM might generate downstream.

**Source:** Three external reviews (Grok 2026-04-25, Claude-as-Principal 2026-04-25, The Principal Auditor 2026-04-26). Promoted to permanent rule 2026-04-26.
