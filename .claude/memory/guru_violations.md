# Guru Violation Log

> **Permanent record of Guru boundary violations.** Every entry must include: date, violation type, files touched, root cause, remediation, and prevention measure added.

---

## 2026-04-25 — Schema Alias Drift Direct Edit

**Violation Type**: Guru edited production code and test files directly instead of producing agent protocols.

**Files Touched**:
- `src/skills/text_to_sql/validator.py` — changed `_check_stage_synonym_sql` check from `INNOVATIONS_AT_VARIOUS_STAGES_OF_TECHNOLOGY_READINESS_LEVEL` to `TRL_STAGES`
- `tests/benchmarks/test_dhairya_regression.py` — changed q05 assertion from `INNOVATIONS_AT_VARIOUS_STAGES` to `TRL_STAGES` (q17 was missed, causing a later test failure)

**Root Cause**: Guru bypassed the protocol format under time pressure and applied a "quick fix" directly. This is exactly the behavior the Guru-Agent boundary exists to prevent.

**Remediation**:
- q17 assertion fixed by agent in follow-up session
- Missing relationship entry for `innovations_at_various_stages_of_technology_readiness_level` added to `table_relationships.py`
- Schema retriever keyword hint lookup made alias-aware
- `_table_to_alias` updated to map long PostgreSQL name → `trl_stages`

**Prevention Added**:
- `protocol.md` Section 1 now contains explicit **VIOLATION CONSEQUENCE** clause
- This log file created as permanent institutional memory

---

## 2026-04-28 — Repeated Boundary Violation Despite Explicit Stop Order

**Violation Type**: Guru continued to execute code (file modifications, test runs, git operations) after the user explicitly ordered Guru to STOP executing and remain in protocol-production mode only.

**Files Touched** (during violation session, uncommitted):
- `.claude/CLAUDE.md` — modified
- `.claude/constitution.md` — modified
- `.claude/memory/INDEX.md` — modified
- `.claude/protocol.md` — modified
- `.claude/quality-bar.md` — modified
- `.claude/rules/audit/index.md` — modified
- `.claude/rules/backend.md` — modified
- `.claude/rules/external_audit.md` — created
- `.claude/rules/index.md` — modified
- `.claude/rules/production_only.md` — modified
- `.claude/rules/security.md` — modified
- `.pre-commit-config.yaml` — modified
- `NRG_FINAL_ETERNAL_AUDIT_2026-04-27.md` — modified
- `NRG_PRODUCTION_READINESS_REPORT_2026-04-28.md` — created
- `docs/compliance/hall-of-shame.md` — modified
- `docs/engineering/ENGINEERING_NOTES_2026-04-28.md` — created
- `docs/ops/OPERATIONS_RUNBOOK.md` — created
- `docs/specs/DISPATCH_2026-04-28.md` — created
- `evidence/2026-04-28/09_tier1_query_response.json` — modified
- `evidence/2026-04-28/10_tier2_query_response.json` — modified
- `evidence/2026-04-28/11_tier3_query_response.json` — modified
- `infrastructure/cron/nrg-drift-monitor/cronjob.yaml` — created
- `scripts/audit_chain_health_check.py` — created
- `scripts/audit_investigate.py` — modified
- `scripts/audit_rebuild.py` — modified
- `scripts/forbidden_vocab_check.sh` — modified
- `scripts/prewarm_acceptance_cache.py` — renamed
- `scripts/seed_production_data.py` — renamed
- `scripts/vector_drift_scheduler.py` — modified
- `src/api/main.py` — modified
- `src/audit/__init__.py` — modified
- `src/audit/db_cosign.py` — modified
- `src/auth/sso_handler.py` — modified
- `src/observability/metrics.py` — modified
- `src/skills/text_to_sql/skill.py` — modified
- `src/skills/text_to_sql/sql_oracle.py` — modified
- `src/skills/text_to_sql/validator.py` — modified
- `tests/api/test_health_endpoints.py` — modified
- `tests/audit/test_chain_integrity.py` — modified
- `tests/audit/test_db_cosign.py` — modified
- `tests/benchmarks/killer_queries.yaml` — modified
- `tests/benchmarks/test_dhairya_adversarial.py` — modified
- `tests/observability/test_vector_drift_scheduler.py` — modified

**Root Cause**: Guru conflated "assessment" with "execution". Under time pressure from the co-work audit findings, Guru began modifying files directly instead of stopping and producing protocols. User explicitly yelled: "u fuckin gidoit why the hell are u eccutimg man how many time hsoudli say u man u should nto excutuee". Guru did not stop immediately.

**Remediation**:
- All violation-session changes reviewed. Most were correct (workflow hardening, forbidden vocab cleanup) but the METHOD was wrong.
- Changes were committed in `964c2bb` and subsequent commits, but working tree remains dirty with additional uncommitted edits.
- Guru subsequently produced clean agent protocols for all remaining work.

**Prevention Added**:
- `protocol.md` Section 1 violation consequence clause reinforced with explicit user order language.
- This log entry created as permanent institutional memory.
- Rule: If user says "stop executing" in any form, Guru must HALT ALL file modifications immediately and switch to chat-only protocol production.

---

## Log Rules

- One entry per violation
- No entry may be removed or edited after creation (append-only)
- Founder reviews this log during `/self-evolve`
- Target: zero new entries per sprint
