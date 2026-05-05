> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: LB-6 — SCHEMA PARITY: 58-TABLE PRODUCTION ALIGNMENT
AGENT: backend + database + devops
PRIORITY: P0-blocker (blocks production deployment, not the user-acceptance session)
MILESTONE: M2 (Database) + X1 (Schema parity CI)
QUALITY BAR: C3 (Multi-hop) + Source #3 (db_struct.sql)
RISK REGISTER: closes Risk #14 (UAT data contradicts public figures)
═══════════════════════════════════════════════════════════════

FILES:
  - alembic/versions/add_production_tables_001.py — extend to 58 tables
  - alembic/versions/<new>_django_auth_tables.py — 11 missing Django/auth tables
  - alembic/versions/<new>_composite_indexes.py — composite indexes for common JOIN patterns
  - alembic/versions/<new>_rls_policies.py — Row-Level Security policies for tier 1/2/3
  - tests/data/test_schema_parity.py — extend to 58/58 PASS
  - tests/data/test_schema_indexes.py (NEW) — verify indexes for hot JOINs
  - tests/data/test_rls_policies.py (NEW) — verify RLS strips T3 rows
  - evidence/2026-04-26/schema_parity_58_58.txt (NEW)
  - evidence/2026-04-26/explain_index_usage.txt (NEW)

PROBLEM:
  Current Alembic migration creates 47 tables. db_struct.sql defines 58.
  Missing tables include the 11 Django/auth support tables that other
  rows reference via FK (auth_user, auth_group, auth_permission,
  auth_user_groups, auth_user_user_permissions, django_admin_log,
  django_content_type, django_migrations, django_session,
  user_registration_old, auth_group_permissions). Even if Django itself
  is not part of NRG runtime, the prod schema dump expects these tables
  to exist or referencing rows fail FK validation.

  Additionally:
  - Composite indexes on hot JOIN patterns (institute, financial_year /
    institute, as_on_year / applicants, status / state, year) are absent
    or unverified — sequential scans on 600 GB tables are operationally
    unacceptable.
  - Row-Level Security (RLS) policies are not enforced at the DB layer
    even though the rbac_policies.yaml allowlist is enforced at the
    application layer. Two-layer defence: app-layer + DB-layer.

ACTION:
  Phase 1 — FORTIFY:
    1a. Parse db_struct.sql and emit a diff against the current Alembic
        migration tree. Generate one Alembic revision per missing table
        cluster: `add_django_auth_tables_001.py` (the 11 auth tables
        with exact column types from db_struct.sql) and any other gaps.
    1b. Re-run the parity test (tests/data/test_schema_parity.py) — must
        report 58/58 PASS. Skipped tests removed.
    1c. Run `alembic upgrade head` against staging PostgreSQL with the
        complete chain; capture pg_dump diff to evidence/.

  Phase 2 — ELEVATE:
    2a. Composite indexes migration with `IF NOT EXISTS` for: 
        (institute, financial_year), (institute, as_on_year),
        (applicants, status), (state, financial_year),
        (field_of_invention, status), (gov_organisation_name, financial_year).
    2b. EXPLAIN ANALYZE the 3 KILLER queries + the 6 new ADV queries
        against staging PG with ≥50k rows; assert no Sequential Scan on
        any FK or hot column. If any survive, emit the missing index DDL.
    2c. Implement RLS on tables containing PII columns:
        researchers, expertise, advance_search_data (authors, email_record),
        publications. T3 sees zero rows from raw selects.

  Phase 3 — IMMORTALIZE:
    3a. Add tests/data/test_schema_indexes.py: parses pg_indexes catalog
        and asserts every documented composite index is live. Fails CI
        on regression.
    3b. Add tests/data/test_rls_policies.py: opens 3 connections (T1, T2, T3)
        and runs `SELECT email FROM expertise` against each. T3 must see
        zero rows; T2 sees zero PII columns; T1 sees full rows.
    3c. Add a CI workflow that runs `alembic upgrade head` against an
        ephemeral PostgreSQL container on every PR — broken migrations
        block merge.

SKILLS TO USE:
  - /database-migrations-sql-migrations — zero-downtime patterns, type parity, FK ordering
  - /python-backend — Alembic revisioning, async SQLAlchemy
  - /testing-strategy — schema-parity CI, RLS validation, EXPLAIN gating
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] tests/data/test_schema_parity.py: 58/58 PASS (no skipped). Evidence:
        evidence/2026-04-26/schema_parity_58_58.txt committed.
  - [ ] `alembic upgrade head` against ephemeral staging PG succeeds without
        FK/order errors. pg_dump diff committed to evidence/.
  - [ ] tests/data/test_schema_indexes.py: every documented composite
        index present.
  - [ ] tests/data/test_rls_policies.py: T1/T2/T3 row-count differences
        prove RLS active.
  - [ ] EXPLAIN ANALYZE on KILLER + ADV queries: zero seq scans on FK
        columns. Evidence: evidence/2026-04-26/explain_index_usage.txt.
  - [ ] Quality Bar Constraint #3 evidence path includes 58-table proof.
  - [ ] No regression on existing Dhairya 43/43.

BEFORE COMMIT:
  - /pre-commit + /code-review-and-quality + /database-migrations-sql-migrations

GURU ASSIGNMENT NOTE:
  The professor's first follow-up after the user-acceptance session will
  be "when does this run on the real 600 GB?" If the answer is "we ship
  47 tables but the dump has 58", the project loses credibility before
  it leaves the room. The 11 missing auth/Django tables are not
  cosmetic — they anchor FK chains that will silently break on any
  serious data import. Close the parity gap, lock RLS at DB layer as a
  second defence next to rbac_policies.yaml, and prove every hot JOIN
  uses an index. Two layers everywhere.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md, production_only.md
  - Read db_struct.sql (Source #3) end-to-end
  - Read .claude/QUALITY_BAR.md "Live Evidence Requirement" + "Tier-Shape Boundary"
  - Read .claude/memory/feedback_tier_shape_boundary.md
  - Read every SKILL.md listed
  - Fortify → Elevate → Immortalize
  - /pre-commit before commit

DEPENDS ON: none (parallel-safe to LB-1..LB-5)
BLOCKS: production deployment (not the user-acceptance session)
═══════════════════════════════════════════════════════════════
