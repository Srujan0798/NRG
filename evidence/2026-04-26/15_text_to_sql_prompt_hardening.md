# LB-2 Text-to-SQL Prompt Hardening Evidence

Timestamp: 2026-04-26T02:33:17+05:30

## Acceptance Trace

- [x] Dhairya regression remains green: `tests/benchmarks/test_dhairya_regression.py`
  - Evidence: `evidence/2026-04-26/lb2_lb3_targeted_pytest.log`
  - Result: included in 123 passed in 7.48s
- [x] Adversarial corpus remains green: `tests/benchmarks/test_dhairya_adversarial.py`
  - Evidence: `evidence/2026-04-26/lb2_lb3_targeted_pytest.log`
  - Result: included in 123 passed in 7.48s
- [x] Prompt hardening guards pass: `tests/benchmarks/test_text_to_sql_prompt_hardening.py`
  - Evidence: `evidence/2026-04-26/lb2_lb3_targeted_pytest.log`
  - Covers wrong/correct few-shot pairing, schema-aware TEXT parsing, quoted casts, and raw stage-synonym LIKE rejection.
- [ ] Staging PostgreSQL EXPLAIN ANALYZE for the three killer queries
  - Evidence available: `evidence/2026-04-26/explain_killer_1.txt`
  - Evidence available: `evidence/2026-04-26/explain_killer_2.txt`
  - Evidence available: `evidence/2026-04-26/explain_killer_3.txt`
  - Status: local volumetric SQLite plans are present; a staging PostgreSQL `DATABASE_URL` was not configured in this workspace.
- [x] Validator rejects unsafe `total_credit_score` casting
  - Evidence: `tests/benchmarks/test_dhairya_adversarial.py`
  - Evidence: `tests/benchmarks/test_text_to_sql_prompt_hardening.py`
  - Covered forms include direct, quoted, and table-qualified casts.
- [x] Quality Bar Constraint #3 score: 8/10
  - Evidence: `src/skills/text_to_sql/schema_aware_prompt.py`
  - Evidence: `src/skills/text_to_sql/validator.py`
  - Evidence: `src/skills/text_to_sql/sql_examples.py`
  - Residual gap: staging PostgreSQL plan proof is still required for a 9+ score.
- [x] Cost impact documented
  - No extra model calls were added.
  - Runtime database cost is unchanged for prompt construction.
  - Prompt size increases through static schema guidance and wrong/correct few-shot rules only; query count and orchestration shape are unchanged.

## Files Touched

- `src/skills/text_to_sql/schema_aware_prompt.py`
- `src/skills/text_to_sql/skill.py`
- `src/skills/text_to_sql/validator.py`
- `src/skills/text_to_sql/sql_examples.py`
- `tests/benchmarks/test_dhairya_adversarial.py`
- `tests/benchmarks/test_text_to_sql_prompt_hardening.py`
- `tests/e2e/test_three_killer_queries.py`
- `scripts/capture_killer_query_evidence.py`

## Verdict

LB-2 is locally hardened and test-backed. It is not fully closed until staging PostgreSQL EXPLAIN ANALYZE evidence is captured against the configured staging database.
