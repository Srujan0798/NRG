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

## Log Rules

- One entry per violation
- No entry may be removed or edited after creation (append-only)
- Founder reviews this log during `/self-evolve`
- Target: zero new entries per sprint
