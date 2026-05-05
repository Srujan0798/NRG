# NRG Agent System Manifest

> **Canonical reference for `.claude/` and `.agents/` structure.**
> Last updated: 2026-05-05
> Total skills: 136 (86 in `.claude/skills/`, 50 in `.agents/skills/`)
> Duplicate skills: 0
> Forbidden vocabulary violations: 0

---

## Directory Purpose

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `.claude/` | Guru (Claude Code) | Strategy, architecture, review, canonical skills |
| `.agents/` | Shishya (Execution agents) | Task execution, implementation, agent-unique skills |

**Rule**: No skill should exist in both directories. Run `.claude/scripts/nrg-skill-count.py` to check.

---

## `.claude/` Structure

```
.claude/
├── CLAUDE.md                    ← Session entry point (read first)
├── CURRENT_STATE.md             ← Current sprint state
├── MANIFEST.md                  ← This file
├── agent-warfare.md             ← Role hierarchy + evolution loop
├── protocol.md                  ← Task format + response rules
├── constitution.md              ← Sovereign AI behavior rules
├── quality-bar.md               ← 6 Hard Constraints
├── REMOTE_WORKFLOW.md           ← Remote access guide
├── rules/
│   ├── index.md                 ← Rules directory overview
│   ├── production_only.md       ← Forbidden vocabulary (PERMANENT)
│   ├── backend.md               ← Backend coding rules
│   ├── frontend.md              ← Frontend coding rules
│   ├── security.md              ← Security rules
│   ├── cost_budget.yaml         ← Cost controls
│   ├── audit/
│   │   ├── index.md             ← Audit rules index
│   │   └── protocol.md          ← Eternal verification standard
│   └── ux/
│       ├── index.md             ← UX rules index
│       └── protocol.md          ← Production UX standard
├── prompts/
│   └── guru_universal.md        ← Guru universal prompt
├── memory/
│   ├── INDEX.md                 ← Memory directory index
│   ├── bugs/                    ← Bug postmortems
│   ├── patterns/                ← Engineering patterns
│   ├── projects/                ← Project overviews
│   ├── references/              ← Reference materials
│   ├── user_profile.md          ← User preferences
│   └── sprint_retrospective.md  ← Sprint reviews
├── skills/                      ← 86 skills (see below)
└── scripts/                     ← Workflow automation
    ├── nrg-verify-workflow.py   ← Validate workflow integrity
    ├── nrg-skill-count.py       ← Count + flag duplicates
    └── nrg-evidence-prune.py    ← Report stale evidence
```

### `.claude/skills/` — 86 Skills

See `.claude/CLAUDE.md` for the full skill index by category.

---

## `.agents/` Structure

```
.agents/
├── AGENTS.md                    ← Agent entry point (read first)
├── prompts/
│   └── shishya_universal.md     ← Shishya universal prompt
└── skills/                      ← 50 unique skills (see below)
```

### `.agents/skills/` — 50 Agent-Unique Skills

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

---

## Verification Checklist

Run this to confirm the system is healthy:

```bash
# 1. True skill counts + duplicates
python3 .claude/scripts/nrg-skill-count.py

# 2. Full workflow validation
python3 .claude/scripts/nrg-verify-workflow.py

# 3. Evidence age/bloat check
python3 .claude/scripts/nrg-evidence-prune.py --days 14
```

---

*Update this manifest when skills are added, removed, or relocated. Run `nrg-skill-count.py` first.*
