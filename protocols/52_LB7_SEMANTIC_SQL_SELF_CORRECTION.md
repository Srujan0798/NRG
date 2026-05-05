> **DEPRECATED FORMAT:** This protocol uses the old ═══ format.
> **Current format:** Use `.claude/assignment_template.md` for all new assignments.

═══════════════════════════════════════════════════════════════
TASK: LB-7 — SEMANTIC SQL SELF-CORRECTION + ANOMALY DETECTION
AGENT: backend + ml + testing
PRIORITY: P0-blocker (silent-wrong-answer is the single biggest failure mode)
MILESTONE: M5b (Performance) + X1 (Schema parity CI)
QUALITY BAR: C3 (Multi-hop) + Source #2 (Dhairya benchmark)
RISK REGISTER: closes Risk #1 (wrong SQL), Risk #15 (uncited claim), Risk #17 (NEW — silent wrong answer)
═══════════════════════════════════════════════════════════════

FILES:
  - src/skills/text_to_sql/skill.py — extend self-correction loop
  - src/skills/text_to_sql/result_anomaly_detector.py (NEW)
  - src/skills/text_to_sql/cardinality_estimator.py (NEW)
  - src/orchestration/nodes/verifier.py — wire anomaly check into verifier
  - tests/skills/test_result_anomaly_detector.py (NEW)
  - tests/orchestration/test_silent_wrong_answer.py (NEW)
  - .claude/memory/bugs_silent_wrong_answer.md (NEW — see below)

PROBLEM:
  The current Text-to-SQL retry loop catches *syntax* errors (the LLM
  emits invalid SQL → DB rejects → retry). It does NOT catch *semantic*
  errors, where the SQL parses, executes, and returns a result that
  looks plausible but is wrong:
    - JOIN on the wrong column → result set has unexpected NULLs
      (Dhairya Q7 — joined patents_details.institute when the correct
      key was combined_ipo_patent_data.applicants).
    - Cast of TEXT-typed column to INT → silently returns 0/empty for
      rows whose format doesn't match (total_credit_score "X:Y" cast).
    - GROUP BY on a column that loses dimension (Dhairya Q3) →
      aggregates correct shape, wrong values.
    - Synonym mismatch on a value column ("TRL 9" vs "Level 9") →
      returns empty when the user expected hits.
    - Cross-domain follow-up loses active_domain → wrong table queried.

  The synthesizer happily formats the wrong rows into a confident answer.
  The verifier currently only checks citation faithfulness, not result
  plausibility. The user is told a wrong number with full citation.
  This is the SILENT WRONG ANSWER — the single biggest failure mode for
  a sovereign research-intelligence platform.

ACTION:
  Phase 1 — FORTIFY:
    1a. Build src/skills/text_to_sql/result_anomaly_detector.py with
        the following signal set, each emitting a confidence-decrement:
        - row_count_zero: returned 0 rows when the query type implies ≥1
        - row_count_one_with_limit_missing: single row when LIMIT was not
          requested and the question phrasing implies a list
        - null_ratio_high: any column has > 30% NULLs in the result
        - aggregate_collapse: GROUP BY result has fewer groups than the
          number of distinct values in any referenced filter column
        - division_by_zero_signal: any computed numeric column is exactly
          0 across all rows when it should not be
        - text_cast_silent_failure: result of a `::int` or `::numeric`
          cast on a TEXT column produced 0/NULL for rows whose source
          value did not match the expected format
    1b. Build src/skills/text_to_sql/cardinality_estimator.py — given the
        question intent (planner output) and the schema, predict the
        expected row-count band for the query. Compare actual against
        prediction; flag if outside band.
    1c. When anomaly detected, the skill MUST NOT return the result as
        the final answer. It either:
          (a) re-runs the SQL with a corrective hint added to the
              prompt (e.g. "the previous join produced unexpected NULLs,
              consider the FK relationship between X.applicants and
              Y.institute"), capped at 2 retries, OR
          (b) escalates to the user with a clarifying question
              ("Did you mean institutes whose name contains 'IIT', or all
              institutes irrespective of type?") instead of returning a
              wrong-but-plausible answer.

  Phase 2 — ELEVATE:
    2a. Wire the anomaly detector into the verifier node. Verifier now
        rejects synthesizer output if the underlying SQL result triggered
        any anomaly signal AND the synthesizer produced a confident claim
        without acknowledging the anomaly.
    2b. Audit-log every anomaly with `sql_anomaly:<signal_name>` bound
        to the per-user audit chain. Operators can spot systemic prompt
        regressions (e.g. a planner change that suddenly causes 30% of
        queries to trigger row_count_zero).
    2c. The /query response gains an `answer_confidence` field
        ∈ {high, partial, low_clarify} so the frontend can render a
        warning banner when low.

  Phase 3 — IMMORTALIZE:
    3a. tests/orchestration/test_silent_wrong_answer.py — adversarial
        cases that intentionally produce SQL passing syntax but wrong
        semantically (each Dhairya failure pattern + each ADV-11..ADV-20
        from killer_queries.yaml). System must either correct or
        clarify, never return the wrong answer as final.
    3b. Promote anomaly counts to Grafana dashboard panel "Silent-Wrong
        Risk". Page on-call when sustained anomaly rate > 5% over 1h.

SKILLS TO USE:
  - /python-backend — async pipeline integration, audit log
  - /prompt-engineering-patterns — corrective re-prompt design
  - /testing-strategy — adversarial cases that trigger each signal
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] tests/skills/test_result_anomaly_detector.py: each of the 6
        signals fires on a crafted positive case AND does NOT fire on
        a crafted negative case (12+ tests).
  - [ ] tests/orchestration/test_silent_wrong_answer.py: 17/17 Dhairya
        patterns + 10/10 ADV-11..20 → system either corrects or asks for
        clarification, never returns the wrong answer as final.
  - [ ] Live evidence: 3 KILLER queries on staging PG carry
        answer_confidence=high; one mutated KILLER (e.g. wrong-domain
        follow-up) carries low_clarify and renders the clarification
        prompt instead of an answer.
  - [ ] Quality Bar Constraint #3 score: 9+/10 with anomaly evidence.
  - [ ] Audit chain shows sql_anomaly:* events with per-user binding.

BEFORE COMMIT:
  - /pre-commit + /code-review-and-quality

GURU ASSIGNMENT NOTE:
  Verdict-deliverable across multiple external audits has named the
  same single biggest risk: a confidently wrong answer to an ambiguous
  cross-domain question. Sanitiser unit tests and Dhairya regression
  fixtures don't catch this — they prove the prompt CAN emit good SQL
  for the cases we tested, not that the engine refuses to ship a wrong
  answer when the LLM stumbles. Build the immune system: anomaly
  detection at result time + corrective re-prompt + clarification fallback.
  Only ship answers the engine itself trusts.

AGENT INSTRUCTIONS (verbatim):
  - Read .agents/AGENTS.md, shishya_universal.md, production_only.md
  - Read docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md (Source #2)
  - Read tests/benchmarks/killer_queries.yaml — specifically the
    `adversarial_breakers` section
  - Read .claude/memory/bugs_silent_wrong_answer.md (created by this protocol)
  - Read .claude/QUALITY_BAR.md C3 + Verdict Template
  - Read every SKILL.md listed
  - Fortify → Elevate → Immortalize
  - /pre-commit before commit

DEPENDS ON: LB-2 (#47) lands first
BLOCKS: production launch and production deployment
═══════════════════════════════════════════════════════════════
