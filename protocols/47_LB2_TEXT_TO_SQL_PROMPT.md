> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: LB-2 — TEXT-TO-SQL PRODUCTION PROMPT HARDENING
AGENT: backend + ml
PRIORITY: P0-blocker
MILESTONE: M5b (Performance) + X1 (Schema parity CI)
QUALITY BAR: C3 (Multi-hop decomposition); Source #2 (Dhairya benchmark)
RISK REGISTER: closes Risk #1, #3, #7
═══════════════════════════════════════════════════════════════

FILES:
  - src/skills/text_to_sql/skill.py
  - src/skills/text_to_sql/sql_examples.py — few-shot prompt templates
  - src/skills/text_to_sql/validator.py — reject patterns
  - src/skills/text_to_sql/schema_aware_prompt.py (NEW)
  - src/data/schema/schema_value_synonyms.md
  - src/data/schema/failed_queries/docs/compliance/hall-of-shame.md
  - tests/benchmarks/test_dhairya_regression.py (extend, do not reduce)
  - tests/benchmarks/test_dhairya_adversarial.py (NEW)
  - tests/benchmarks/killer_queries.yaml (canonical corpus — read this)

PROBLEM:
  All 7 Dhairya failure patterns currently pass in the regression file
  because the test fixture pins exact SQL. The PRODUCTION prompt path
  (planner → router → text_to_sql.skill) does NOT consistently inject the
  SPLIT_PART pattern for total_credit_score (TEXT in "X:Y"), the CTE+
  GROUP BY for YoY, or synonym mapping for TRL/Level/Market Ready. On real
  PostgreSQL with the 62-character TRL-stage table and TEXT-typed credit
  scores, the LLM still emits CAST(... AS INT) and silently fails or
  returns wrong rows. 10-row seed passes; 50k-row staging will not.

ACTION:
  Phase 1 — FORTIFY:
    1a. Update sql_examples.py few-shots — for every Dhairya failure
        pattern include a "Wrong" example next to a "Correct" example:
        Q1 credit parse, Q3/Q16 YoY CTE, Q4 ORDER BY SUM not COUNT DISTINCT,
        Q5/Q17 stage transitions on the 62-char table, Q7 patent JOIN keys,
        Q10/Q12 active_domain follow-ups, Q15 rising-stars scalar subquery.
    1b. validator.py rejects: CAST(total_credit_score, raw LIKE '%TRL 9%'
        without synonym expansion, HAVING-without-aggregate, JOINs without
        FK column from db_struct.sql.

  Phase 2 — ELEVATE:
    2a. Build schema_aware_prompt.py: at prompt-build time, parse db_struct.sql
        for actual column types; for any TEXT-typed column referenced in
        the question, prepend parsing guidance automatically. Removes the
        "we hope the LLM remembers" failure mode.
    2b. test_dhairya_adversarial.py: 10 mutated questions per pattern (70
        cases) — typos, synonyms ("Level 9" / "TRL 9" / "Market Ready" /
        "fully market ready"), bilingual ("FY 2022-23" vs "वित्तीय वर्ष
        2022-23"), unit confusion ("crores" vs "Cr"). Source corpus:
        tests/benchmarks/killer_queries.yaml `adversarial_breakers`.

  Phase 3 — IMMORTALIZE:
    3a. Auto-extend docs/compliance/hall-of-shame.md from any production rejection: every
        time validator rejects an LLM output, append rejected SQL +
        accepted SQL, then trigger a nightly few-shot regeneration so the
        prompt grows stronger with every miss.
    3b. Wire Quality Bar scorecard to fail if Dhairya regression OR
        adversarial bucket drops below 100% — release gate.

SKILLS TO USE:
  - /prompt-engineering-patterns — few-shot, structured output, schema injection
  - /python-backend — schema parser, validator, async LLM calls
  - /testing-strategy — adversarial corpus, mutation testing, regression gating
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] tests/benchmarks/test_dhairya_regression.py: 43/43 still PASS
  - [ ] tests/benchmarks/test_dhairya_adversarial.py: 70/70 PASS (10/pattern)
  - [ ] Live EXPLAIN ANALYZE on the 3 KILLER queries against staging PG
        with ≥50k seeded rows — every plan committed to
        evidence/2026-04-26/explain_killer_*.txt
  - [ ] validator rejects any CAST(total_credit_score …) LLM output —
        proven by mock test
  - [ ] Quality Bar Constraint #3 score: 8+/10 (live evidence file attached)
  - [ ] Cost impact documented: ₹/1k queries delta from richer prompt

BEFORE COMMIT:
  - /pre-commit, /code-review-and-quality
  - Re-run full Dhairya + adversarial suite locally — report counts

GURU ASSIGNMENT NOTE:
  Source #2 (Dhairya) is the only external SQL benchmark we have. The 41%
  baseline was production reality, the 43/43 regression is fixture comfort
  food. Until the same 17 questions plus 70 mutations pass through the
  production planner→router→text_to_sql path with the LLM actually
  generating SQL (not the test pinning it), we have no proof the engine
  works. Treat the prompt + validator as the immune system of the SQL
  pipeline — every Dhairya failure is an antigen we vaccinate against
  permanently.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md, production_only.md
  - Read docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md (Source #2) cover-to-cover
  - Read db_struct.sql (Source #3) — note exact column types, FKs, table names
  - Read tests/benchmarks/killer_queries.yaml — your canonical corpus
  - Read .claude/QUALITY_BAR.md C3 + Live Evidence Requirement
  - Read every SKILL.md listed
  - Fortify → Elevate → Immortalize
  - /pre-commit before commit

DEPENDS ON: #21 (schema bridge — must reference real types from db_struct.sql)
BLOCKS: production launch, Phase 6 (#29 training data)
═══════════════════════════════════════════════════════════════
