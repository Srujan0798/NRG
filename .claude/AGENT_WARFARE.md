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

**ARCHITECT (You — the human)**
- Sets vision, approves major decisions
- Reviews agent output at quality gates
- Resolves conflicts between agent recommendations
- Owns the Core_Idea_Clean.md and AUDIT_V3_FINAL.md

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
- Read current backlog (AUDIT_V3_FINAL.md remaining tasks)
- Read memory (what failed last time, what's blocked)
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
- Produces: "Next sprint should focus on X because Y"

---

## The Memory Brain

```
~/.claude/projects/.../memory/
├── MEMORY.md              ← Index (auto-loaded every session)
├── user_profile.md        ← Who the architect is
├── project_nrg.md         ← Current state (updated after each sprint)
├── feedback_workflow.md   ← How the architect wants to work
├── bugs_patterns.md       ← Recurring bugs → prevention rules
├── perf_baselines.md      ← Performance benchmarks to beat
├── sprint_retrospective.md ← What worked, what didn't, per sprint
└── tech_decisions.md      ← ADRs made during the project
```

After every sprint, the EVOLVE phase updates these files. Next sprint starts with full institutional knowledge.

---

## Skill Inventory

| Skill | Trigger | What It Does | Used By |
|-------|---------|-------------|---------|
| `/test-suite` | Before commit, after deploy | Run all tests + coverage | All agents |
| `/audit-check` | Weekly, after incidents | Verify HMAC audit chain integrity | Guardian |
| `/deploy-local` | Dev testing | Spin up full stack locally | DevOps agent |
| `/code-review` | Every PR/commit | Quality + security + pattern review | Mentor agent |
| `/security-audit` | After each sprint | Full OWASP + PII + injection scan | Guardian |
| `/pre-commit` | Before EVERY commit | Lint + test + security gate | All agents |
| `/post-deploy` | After deployment | Smoke test + health check | DevOps agent |
| `/self-evolve` | After each sprint | Analyze + update rules + memory | Guardian |
| `/architect` | Major decisions | Architecture review + ADR creation | CTO agent |
| `/sprint-plan` | Start of each sprint | Prioritize + assign tasks | Architect |
| `/bug-hunt` | When things break | Systematic root cause analysis | Any agent |
| `/performance` | After features land | Benchmark + regression check | DevOps agent |
| `/docs-sync` | After code changes | Keep docs aligned with code | Any agent |

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
