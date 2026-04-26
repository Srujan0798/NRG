# NRG Agent System Manifest

> **Canonical reference for `.claude/` and `.agents/` structure.**
> Last updated: 2026-04-25
> Total unique skills: 65 (41 in `.claude/skills/`, 24 in `.agents/skills/`)
> Duplicate skills: 0
> Forbidden vocabulary violations: 0

---

## Directory Purpose

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `.claude/` | Guru (Claude Code) | Strategy, architecture, review, canonical skills |
| `.agents/` | Shishya (Execution agents) | Task execution, implementation, agent-unique skills |

**Rule**: No skill exists in both directories. Every skill has exactly one canonical home.

---

## `.claude/` Structure

```
.claude/
├── CLAUDE.md                    ← Session entry point (read first)
├── MANIFEST.md                  ← This file
├── agent-warfare.md             ← Role hierarchy + evolution loop
├── protocol.md             ← Task format + response rules
├── constitution.md          ← Sovereign AI behavior rules
├── quality-bar.md               ← 6 Hard Constraints
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
│   ├── MEMORY.md                ← User profile + project state
│   ├── INDEX.md                 ← Memory directory index
│   ├── bugs/                    ← Bug postmortems
│   ├── patterns/                ← Engineering patterns
│   ├── projects/                ← Project overviews
│   ├── references/              ← Reference materials
│   ├── user_profile.md          ← User preferences
│   └── sprint_retrospective.md  ← Sprint reviews
└── skills/                      ← 41 skills (see below)
```

### `.claude/skills/` — 41 Canonical Skills

#### NRG Core (14)
`/test-suite`, `/audit-check`, `/deploy-local`, `/code-review`, `/security-audit`, `/pre-commit`, `/post-deploy`, `/self-evolve`, `/architect`, `/sprint-plan`, `/bug-hunt`, `/performance`, `/docs-sync`, `/release-readiness`

#### Claude Strategy + Review (13)
`/architecture-adr`, `/testing-strategy`, `/tech-debt`, `/system-design`, `/standup`, `/write-spec`, `/stakeholder-update`, `/metrics-review`, `/roadmap-update`, `/compliance-check`, `/incident-response`, `/doc-coauthoring`, `/external-audit`

#### Engineering + DevEx (14)
`/python-backend`, `/code-review-and-quality`, `/security-auditor`, `/frontend-react-best-practices`, `/webapp-testing`, `/prompt-engineering-patterns`, `/dockerfile-validator`, `/database-migrations-sql-migrations`, `/typescript-advanced-types`, `/nodejs-backend-patterns`, `/changelog-generator`, `/claude-api`, `/external-prompt-merge`, `/find-skills`

---

## `.agents/` Structure

```
.agents/
├── AGENTS.md                    ← Agent entry point (read first)
├── prompts/
│   └── shishya_universal.md     ← Shishya universal prompt
└── skills/                      ← 25 unique skills (see below)
```

### `.agents/skills/` — 25 Agent-Unique Skills

#### Data + Analysis (8)
`explore-data`, `validate-data`, `statistical-analysis`, `sql-queries`, `build-dashboard`, `create-viz`, `data-visualization`, `database-schema-designer`

#### Frontend + Design (6)
`frontend-design`, `design-critique`, `ux-copy`, `accessibility-review`, `react-composition-patterns`, `documentation`

#### Backend + DevOps (5)
`debug`, `test-driven-development`, `database-migration`, `neon-postgres`, `secure-linux-web-hosting`

#### Deployment + Business (5)
`deploy-checklist`, `deployment-pipeline-design`, `startup-financial-modeling`, `startup-metrics-framework`, `better-auth-security-best-practices`

---

## Cross-Reference: Where to Find a Skill

| Need | Directory | Count |
|------|-----------|-------|
| Pre-commit gate | `.claude/skills/pre-commit/` | 1 |
| Security audit | `.claude/skills/security-audit/` | 1 |
| Code review | `.claude/skills/code-review/` | 1 |
| Python backend patterns | `.claude/skills/python-backend/` | 1 |
| React best practices | `.claude/skills/frontend-react-best-practices/` | 1 |
| SQL query help | `.agents/skills/sql-queries/` | 1 |
| Debug session | `.agents/skills/debug/` | 1 |
| Data visualization | `.agents/skills/create-viz/` or `.agents/skills/data-visualization/` | 2 |
| Write documentation | `.agents/skills/documentation/` | 1 |

---

## Verification Checklist

Run this to confirm the system is diamond-proof:

```bash
# 1. Zero duplicates
for skill in .claude/skills/*/; do
  name=$(basename "$skill")
  [ -d ".agents/skills/$name" ] && echo "DUPLICATE: $name"
done

# 2. Zero forbidden vocabulary (excluding production_only.md which defines them)
for word in forbidden_vocabulary_list; do
  grep -rln "\b$word\b" .claude/ .agents/ --include="*.md" 2>/dev/null | grep -v "production_only.md" | while read f; do
    echo "VIOLATION: $word in $f"
  done
done

# 3. Correct counts
echo "Claude skills: $(ls .claude/skills/ | wc -l)"
echo "Agent skills: $(ls .agents/skills/ | wc -l)"
```

---

*This manifest is auto-generated. Update it when skills are added, removed, or relocated.*
