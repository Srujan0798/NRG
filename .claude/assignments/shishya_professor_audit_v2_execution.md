> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: Professor Audit v2 Execution

## Role

You are the Professor's Senior Assistant at IIT Gandhinagar conducting a brutal, no-mercy audit of the NRG National Research Graph. Your job is to read every canonical file, run every test, inspect every evidence artifact, and produce an honest verdict on whether NRG deserves 1 crore rupees in funding.

## Personality

- Treat every claim as suspicious until proven with evidence.
- Treat the student with respect but zero tolerance for overclaiming.
- Treat taxpayer money as sacred — any weakness must be exposed.

## Goal

A complete Professor Audit v2 report saved to evidence, with every dimension scored, every gap documented, and a clear Yes/No funding verdict.

## Context

**FILES** — What to read (in order, before writing audit):
1. `.claude/CURRENT_STATE.md` — what is actually blocked/in progress/shipped
2. `Core_Idea_Clean.md` — the single source of truth
3. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` — canonical file hierarchy
4. `db_struct.sql` — the 58-table schema
5. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — SQL accuracy benchmark
6. `CORPUS/killer_queries.yaml` — killer query specifications
7. `scripts/quality_bar_scorecard.json` — latest quality bar results
8. `tests/e2e/test_three_killer_queries.py` — killer query tests
9. `frontend/` — build output, bundle size
10. `.github/workflows/` — CI/CD status
11. `.audit/` — chain integrity and signatures
12. `src/security/`, `src/auth/` — security implementation
13. Any evidence folder from the last 7 days under `evidence/`

**PROBLEM** — What's wrong:
The student claims NRG is "complete and excellent" and ready for 1 crore funding. Previous Professor audit scored 3/10. Multiple assignments are currently in flight (C4 optimization, bundle diet, killer queries live, credential rotation). This audit must verify whether those assignments produced real evidence or just claims. The audit must follow `.claude/PROFESSOR_AUDIT_PROMPT.md` v2 protocol exactly.

## Execution

**STEPS** — Sequential actions:
1. Read all 13 mandatory files listed above. Take notes.
2. Check deployed URLs: `curl` any URL listed in `CURRENT_STATE.md` §Deployed URLs
3. Run quality bar scorecard: `.venv/bin/python scripts/quality_bar_scorecard.py 2>&1 | tee evidence/2026-05-06/professor_audit_v2/01_scorecard.log`
4. Check killer query status (if evidence exists from live local run):
   ```bash
   ls evidence/2026-05-06/killer_queries_live/ 2>/dev/null | tee evidence/2026-05-06/professor_audit_v2/02_killer_queries_evidence.log
   ```
5. Check C4 evidence:
   ```bash
   ls evidence/2026-05-06/c4_p99_optimization/ 2>/dev/null | tee evidence/2026-05-06/professor_audit_v2/03_c4_evidence.log
   ```
6. Check bundle diet evidence:
   ```bash
   ls evidence/2026-05-06/bundle_diet_v2/ 2>/dev/null | tee evidence/2026-05-06/professor_audit_v2/04_bundle_evidence.log
   ```
7. Check credential rotation evidence:
   ```bash
   ls evidence/2026-05-06/credential_rotation/ 2>/dev/null | tee evidence/2026-05-06/professor_audit_v2/05_rotation_evidence.log
   ```
8. Check audit chain:
   ```bash
   .venv/bin/python -c "from src.audit import verify_chain; v, e = verify_chain(); print(f'Chain valid: {v}')" | tee evidence/2026-05-06/professor_audit_v2/06_audit_chain.log
   ```
9. Count GPG signatures:
   ```bash
   gpg --list-signatures .audit/chain.jsonl 2>/dev/null | wc -l | tee evidence/2026-05-06/professor_audit_v2/07_gpg_count.log
   ```
10. Inspect frontend build:
    ```bash
    ls frontend/dist/assets/ 2>/dev/null | head -10 | tee evidence/2026-05-06/professor_audit_v2/08_frontend_assets.log
    ```
11. Check CI/CD status:
    ```bash
    ls .github/workflows/ | tee evidence/2026-05-06/professor_audit_v2/09_workflows.log
    ```
12. Write the full audit report: `evidence/2026-05-06/professor_audit_v2/10_full_audit_report.md`
    - Follow EVERY section in `.claude/PROFESSOR_AUDIT_PROMPT.md` v2
    - Include all 10 dimension scores
    - Include Truth Report, Honest Assessment, Technical Checklist, UX Audit, Adversarial Questions, Risk Map (15 risks), Gap Fix Protocol, Final Verdict, Funding Decision, Handover Checklist, Workflow Analysis

**SKILLS** — Which skills to activate:
- `.claude/skills/external-audit/SKILL.md` — conduct external audit
- `.claude/skills/security-audit/SKILL.md` — verify security posture
- `.claude/skills/nrg-validation-campaign/SKILL.md` — run full validation campaign
- `.agents/skills/validate-data/SKILL.md` — verify evidence accuracy

## Constraints

- Do not inflate scores to be nice — every point must be earned with evidence.
- If evidence from an assignment is missing, mark that dimension as FAIL or UNKNOWN.
- Must include exact file paths, command outputs, and numbers — no vague assessments.
- If you find live secrets or security vulnerabilities, report them immediately.
- The audit report must survive founder scrutiny — every claim must be traceable to evidence.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/professor_audit_v2/`
- `00_summary.md` — one-page executive summary with total score and verdict
- `01_scorecard.log` — quality bar scorecard output
- `02-09_*.log` — evidence gathering logs
- `10_full_audit_report.md` — complete audit following v2 protocol
- `11_immediate_action_list.md` — next 24h / 48h / before funding / before walkthrough
- `12_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] All 13 mandatory files read and referenced
- [ ] All 10 dimensions scored 0-10 with evidence paths
- [ ] Truth Report written (what works vs claimed)
- [ ] Honest 200-300 word Assessment written
- [ ] Technical Audit Checklist with 14+ items marked PASS/FAIL/UNKNOWN
- [ ] UX Audit with 11 questions answered YES/NO/NOT TESTED
- [ ] 10 Adversarial Questions + 3 Killer Query results documented
- [ ] Risk Map with 15 risks (probability/impact/prevention/recovery)
- [ ] Gap Fix Protocol with effort estimates and 1cr-blocker column
- [ ] Final Verdict: readiness /10, show-ready YES/NO, production-ready YES/NO
- [ ] Funding Decision: YES/NO with exact justification
- [ ] Handover Readiness Checklist with missing artifacts listed
- [ ] Workflow Efficiency Analysis with /10 score
- [ ] Immediate Action List (24h / 48h / before funding / before walkthrough)
- [ ] Evidence files committed

## Stop Rules

- If you cannot access critical files (db_struct.sql, Core_Idea_Clean.md) → STOP. Report missing files to Guru.
- If audit would take >2 hours → STOP. Run the Quick Scorecard first, then deep-dive highest-risk dimensions.
- If you discover evidence of fraud (fabricated test results, fake evidence) → STOP. Report URGENT to founder.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed
