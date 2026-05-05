# NRG — Agent (Shishya) Entry Point

> **You are an execution agent for a production sovereign AI platform.**
> Read this, then read your assigned skill(s), then execute.

---

## Start Here (4 Steps — do in order)

1. **Read [.claude/CURRENT_STATE.md](../.claude/CURRENT_STATE.md)** — current open items, quality bar, what's blocked
2. **Read [docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md](../docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md)** — canonical files, portable corpus, Dhairya/db_struct gates
3. **Read [.claude/rules/production_only.md](../.claude/rules/production_only.md)** — forbidden vocabulary, production framing
4. **Read the SKILL.md for every skill in your task** — then begin

> Only if your task touches SQL/schema: also read `db_struct.sql` and `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
> Only if architecture context needed: read `Core_Idea_Clean.md`
> For v1.0, query, validation, answer-flow, handover, SQL/RAG, or frontend proof work: also read `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`; use `CORPUS/` only as a verified mirror after `python3 scripts/verify_corpus_sync.py`.

> Founder correction hard rule: if asked whether NRG is "100% better", "not
> partial", "best in every point", or stronger than an external v1.0 app across
> appearance, UI/UX, DB, backend, accessibility, speed, and every corner, use
> the hybrid release fusion skill, `.claude/skills/nrg-validation-campaign/SKILL.md`, and
> `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`. Return a
> proof matrix with `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`. No evidence means
> no claim.

---

## Quality Bar (6 Hard Constraints — know these cold)

| # | Constraint | Test | Current |
|---|-----------|------|---------|
| C1 | DPDP Indian PII detection | `tests/security/test_pii_indian.py` | ✅ |
| C2 | Per-user audit binding | `tests/security/test_per_user_audit_binding.py` | ✅ |
| C3 | Multi-hop DAG planner | `tests/orchestration/test_multi_hop_planner.py` | ✅ |
| C4 | P99 <500ms @ 1000 concurrent | `scripts/quality_bar_scorecard.py` with `tests/load/locustfile_c4.py` | ✅ local quota-neutral / cluster pending |
| C5 | Vector drift auto-retrain | `scripts/vector_drift_check.py` | ✅ |
| C6 | Schema egress allowlist | `tests/security/test_egress_allowlist.py` | ✅ |

Full constraint spec: `.claude/quality-bar.md`

---

## Your Skills Arsenal (50 in .agents/skills/ + 86 in .claude/skills/)

### .agents/skills/ — Execution Skills
| Category | Skills |
|----------|--------|
| **Data** | `explore-data` · `validate-data` · `statistical-analysis` · `sql-queries` · `build-dashboard` · `create-viz` · `data-visualization` |
| **Data Pipelines** | `data-engineering` · `authoring-dags` · `debugging-dags` · `testing-dags` · `profiling-tables` · `checking-freshness` |
| **Design** | `frontend-design` · `design-critique` · `ux-copy` · `accessibility-review` · `react-composition-patterns` · `figma-implement-design` · `figma-generate-design` |
| **Backend** | `debug` · `test-driven-development` · `database-schema-designer` · `database-migration` · `fastapi-python` · `postgresql-table-design` · `secure-linux-web-hosting` |
| **AI/ML** | `langchain-rag` · `langgraph-fundamentals` · `vector-index-tuning` · `pydantic-ai` |
| **DevOps** | `deploy-checklist` · `deployment-pipeline-design` · `helm-chart-scaffolding` · `prometheus-configuration` |
| **Security** | `better-auth-security-best-practices` |
| **Workflow** | `using-git-worktrees` · `dispatching-parallel-agents` · `finishing-a-development-branch` · `verification-before-completion` · `subagent-driven-development` · `writing-plans` · `requesting-code-review` · `receiving-code-review` |
| **Docs** | `documentation` |

### .claude/skills/ — Strategy + NRG-Sovereign Skills
**NRG Sovereign (8):** `nrg-audit-chain` · `nrg-data-analyst` · `nrg-dpdp-compliance` · `nrg-embedding-models` · `nrg-grafana-monitoring` · `nrg-kong-gateway` · `nrg-nginx-sovereign` · `nrg-redis-caching`

**Engineering:** `python-backend` · `code-review-and-quality` · `security-auditor` · `frontend-react-best-practices` · `database-migrations-sql-migrations` · `test-suite` · `security-audit` · `pre-commit` · `post-deploy` · `bug-hunt` + 66 more

**Search + Synthesis:** `knowledge-synthesis` · `search-strategy`

**Developer Workflow (8):** `superpowers` · `feature-dev` · `security-guidance` · `skill-creator` · `pr-review-toolkit` · `claudemd-management` · `session-report` · `context7`

> When in doubt which skill to use: pick the most specific one. Multiple skills can be combined.

---

## Agent Loop Safety

Use these rules for any task involving agents, tools, planners, dispatchers,
memory, retries, or autonomous execution:

- Set an explicit max iteration, retry, step, or budget limit.
- If a tool fails, surface the failure in your report with tool name, input
  summary, error class, and recovery action. Do not hide it behind a generic
  "handled" note.
- Keep tool access focused. If the task seems to need more than 5-7 tools,
  split the task or ask Guru for a supervisor protocol.
- Custom tools need clear descriptions, required inputs, examples, output
  shape, and failure behavior.
- Persist only durable memory: decisions, bug patterns, evidence paths, and
  reusable rules. Do not store raw scratch context or duplicate prompt text.
- Use multi-agent/supervisor patterns only for independent subtasks, distinct
  expertise, parallel work, or explicit review. Otherwise keep the solution
  simpler.
- When agent behavior is wrong, debug in this order: iteration count, tool
  calls, available memory, reasoning trace where visible, then each tool in
  isolation.

---

## Evidence Standard

**Full audit cycle** (use for milestone/LB tasks): 20 files per `.claude/rules/audit/protocol.md §2.1`

**Small task** (use for K-*/fix/feat tasks):
```
evidence/2026-<MM-DD>/
├── <task_id>_test_output.log     ← pytest -v or test run output
├── <task_id>_before_after.diff   ← git diff of changes
└── <task_id>_verification.txt    ← one-line confirm: command + result
```
Commit these with the fix. No evidence = not done.

---

## Task Format (what every Guru assignment gives you)

```
FILES      — What to read/modify
PROBLEM    — What's wrong
STEPS      — Sequential actions
SKILLS     — Which skills to activate
EVIDENCE   — What to produce
DONE WHEN  — Acceptance criteria
```

---

## Report Back

```
TASK COMPLETE: [task-id / name]
STATUS: done | partial | blocked

SKILLS USED:
  - [skill] — [how applied]

CHANGES:
  - [file]: [what changed and why]

EVIDENCE:
  - evidence/2026-XX-XX/<files committed>

TESTS: X passed, Y failed
ISSUES FOR GURU:
  - [blockers or decisions needed]
```

---

## DO NOT
- Make strategic decisions — flag to Guru
- Skip pre-commit checks (`/pre-commit`)
- Commit without a test
- Use SQLite-only schema — always consider the 58-table PostgreSQL schema (`db_struct.sql`)
- Claim DONE without evidence file committed
