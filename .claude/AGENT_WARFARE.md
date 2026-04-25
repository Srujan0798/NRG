# NRG Agent Warfare System — The Autonomous Machine

> No human bottleneck. No manual steps. Every cycle makes the system smarter.
> This document is the operating system for how agents build, evolve, and improve NRG.

---

## The Philosophy

Traditional dev: Human thinks → Human codes → Human tests → Human deploys.
Our system: **Architect commands → Agents execute → System self-audits → Learnings feed back → Next cycle is stronger.**

The architect (you) is the brain. The agents are the hands. The skills are the playbooks. The memory is the institutional knowledge. The loops are the heartbeat.

---

## Role Architecture

### The Command Structure

```
┌─────────────────────────────────────────────────┐
│                   ARCHITECT (You)                │
│   Vision · Strategy · Decisions · Quality Gates  │
└──────────────────────┬──────────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
   ┌────▼────┐   ┌────▼────┐      ┌─────▼─────┐
   │   CTO   │   │   CFO   │      │  MENTOR   │
   │ Agent   │   │ Agent   │      │  Agent    │
   │         │   │         │      │           │
   │Tech arch│   │Resource │      │Quality    │
   │Stack    │   │Budget   │      │Standards  │
   │Infra    │   │Priority │      │Code review│
   └────┬────┘   └────┬────┘      └─────┬─────┘
        │              │                  │
   ┌────▼──────────────▼──────────────────▼────┐
   │              EXECUTION AGENTS              │
   │                                            │
   │  Backend · Frontend · ML/RAG · DevOps ·    │
   │  Security · Testing · Docs                 │
   └────────────────────┬──────────────────────┘
                        │
                   ┌────▼────┐
                   │GUARDIAN │
                   │ Agent   │
                   │         │
                   │Post-run │
                   │Audit    │
                   │Evolve   │
                   └─────────┘
```

### Role Definitions

**ARCHITECT (You — the human / Founder)**
- Sets vision, approves major decisions
- Reviews agent output at quality gates
- Resolves conflicts between agent recommendations
- Owns the 3 Data Sources: `Core_Idea_Clean.md` (vision), `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` (SQL benchmark), `db_struct.sql` (prod schema)
- Owns `BACKLOG.md` (task priorities) and `.claude/CLAUDE.md` (system brain)

**CTO AGENT** — `/architect` skill
- Makes technology decisions within the vision
- Reviews PRs for architectural consistency
- Decides: "should this be a new service or a module?"
- Reads: Core_Idea_Clean.md, AUDIT_V3_FINAL.md, all src/ code

**MENTOR AGENT** — `/code-review` skill
- Reviews every PR/commit for quality, security, patterns
- Enforces: no raw SQL, no PII leaks, audit logging, type hints
- Produces: improvement suggestions, not just pass/fail
- Learns: tracks recurring issues in memory → updates rules

**GUARDIAN AGENT** — `/security-audit` + `/self-evolve` skills
- Post-execution security scan
- Checks: OWASP top 10, PII exposure, injection vectors, egress violations
- Self-evolution: after every sprint, analyzes what went wrong → updates CLAUDE.md rules

**EXECUTION AGENTS** — Your fleet
- Receive task protocols with clear acceptance criteria
- Run `/pre-commit` before every commit
- Report results via structured output

---

## The Self-Evolution Loop

```
╔══════════════════════════════════════════════════════════╗
║                    THE EVOLUTION CYCLE                    ║
║                                                          ║
║   ┌─────────┐    ┌──────────┐    ┌──────────┐          ║
║   │  PLAN   │───▶│ EXECUTE  │───▶│  AUDIT   │          ║
║   │         │    │          │    │          │          ║
║   │Sprint   │    │Agents    │    │Tests     │          ║
║   │tasks    │    │implement │    │Security  │          ║
║   │from     │    │code      │    │Coverage  │          ║
║   │backlog  │    │          │    │Quality   │          ║
║   └─────────┘    └──────────┘    └────┬─────┘          ║
║        ▲                              │                  ║
║        │         ┌──────────┐         │                  ║
║        │         │  EVOLVE  │◀────────┘                  ║
║        │         │          │                            ║
║        └─────────│Update    │                            ║
║                  │rules     │                            ║
║                  │memory    │                            ║
║                  │skills    │                            ║
║                  │CLAUDE.md │                            ║
║                  └──────────┘                            ║
╚══════════════════════════════════════════════════════════╝
```

### How Each Phase Works

**PLAN** → Use `/sprint-plan` skill
- Read current backlog (`BACKLOG.md` — the active task list)
- Read memory (what failed last time, what's blocked)
- Check all 3 Data Sources (see `.claude/CLAUDE.md`) — any new inputs from professor/external?
- Check schema gap: Dev SQLite 18 tables vs Prod PostgreSQL 58 tables
- **Produce Known State Table**: explicit WORKING vs BROKEN list before any new work. Agents must not re-break what's working. See `.claude/rules/audit_protocol.md` Section 4 for the D1-D10 checklist template.
- Produce prioritized task list with dependencies
- Architect approves → agents receive tasks

**EXECUTE** → Agents use `/pre-commit` before every commit
- Each agent gets ONE task protocol
- Must run `/pre-commit` which: lints, tests, checks security, checks coverage
- If pre-commit fails → agent fixes before committing
- Parallel execution: backend + frontend + ML agents work simultaneously

**AUDIT** → Use `/code-review` + `/security-audit` + `/test-suite`
- After all tasks complete, run full audit
- Security scan for new vulnerabilities
- Coverage check (must stay >= 60%)
- Performance check (no regressions)
- Produces: PASS/FAIL + detailed report

**EVOLVE** → Use `/self-evolve` skill
- Analyzes audit results
- Updates .claude/rules/ with new patterns discovered
- Updates CLAUDE.md with new conventions
- Updates memory with learnings
- Verifies all 3 Data Sources are current — ask Founder if new external inputs received
- Produces: "Next sprint should focus on X because Y"

---

## The Memory Brain

```
.claude/memory/   ← IN THE REPO (committed, pushed, accessible anywhere)
├── MEMORY.md                      ← Index (auto-loaded every session)
├── user_profile.md                ← Who the Founder is
├── project_nrg.md                 ← Current state (updated after each sprint)
├── feedback_workflow.md           ← How the Founder wants to work
├── feedback_guru_protocol.md      ← Protocol format enforcement rules
├── reference_three_data_sources.md ← The 3 external data inputs driving NRG
├── reference_dhairya_benchmark.md ← Dhairya's 17-query SQL benchmark reference
├── project_sql_audit_dhairya.md   ← SQL audit status and findings
├── bugs_patterns.md               ← Recurring bugs → prevention rules
├── perf_baselines.md              ← Performance benchmarks to beat
├── sprint_retrospective.md        ← What worked, what didn't, per sprint
└── tech_decisions.md              ← ADRs made during the project
```

After every sprint, the EVOLVE phase updates these files. Next sprint starts with full institutional knowledge.

---

## Skill Inventory (91 total: 39 Claude + 52 Agent)

### Core NRG Skills (13 — both Claude + Agents)
| `/test-suite` | `/audit-check` | `/deploy-local` | `/code-review` | `/security-audit` |
| `/pre-commit` | `/post-deploy` | `/self-evolve` | `/architect` | `/sprint-plan` |
| `/bug-hunt` | `/performance` | `/docs-sync` |

### Claude Cowork Skills (12 Claude + 14 Agent)
Claude: `/architecture-adr`, `/testing-strategy`, `/tech-debt`, `/system-design`, `/standup`, `/write-spec`, `/stakeholder-update`, `/metrics-review`, `/roadmap-update`, `/compliance-check`, `/incident-response`, `/doc-coauthoring`
Agents: `/debug`, `/deploy-checklist`, `/documentation`, `/explore-data`, `/sql-queries`, `/statistical-analysis`, `/validate-data`, `/build-dashboard`, `/create-viz`, `/data-visualization`, `/accessibility-review`, `/ux-copy`, `/design-critique`, `/incident-response`

### Community + Ultra-Dex Skills (14 shared + extras)
Shared: `/python-backend`, `/code-review-and-quality`, `/security-auditor`, `/frontend-react-best-practices`, `/webapp-testing`, `/prompt-engineering-patterns`, `/dockerfile-validator`, `/database-migrations-sql-migrations`, `/typescript-advanced-types`, `/nodejs-backend-patterns`, `/changelog-generator`, `/claude-api`, `/mcp-builder`
Agent-only extras: `/frontend-design`, `/react-composition-patterns`, `/web-design-guidelines`, `/database-schema-designer`, `/test-driven-development`, `/deployment-pipeline-design`, and more

Full list: `ls .claude/skills/` (Claude) or `ls .agents/skills/` (Agents)

---

## The Frictionless Workflow

### For You (Architect)
1. Run `/sprint-plan` → get prioritized task list
2. Assign tasks to agents → they execute
3. Agents run `/pre-commit` before every commit
4. You run `/code-review` on results
5. Run `/security-audit` + `/test-suite` for final gate
6. Run `/self-evolve` to capture learnings
7. Repeat

### For Agents
1. Receive task protocol
2. Read CLAUDE.md + relevant rules (auto-loaded)
3. Implement
4. Run `/pre-commit` — must pass
5. Commit with conventional message
6. Report completion

### Zero-Friction Guarantees
- **No permission prompts**: settings.json auto-approves safe tools
- **No context loss**: CLAUDE.md + memory loaded every session
- **No repeated mistakes**: self-evolve updates rules after each failure
- **No quality drift**: pre-commit gates on every single commit
- **No knowledge silos**: docs-sync keeps everything aligned
