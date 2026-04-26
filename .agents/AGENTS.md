# NRG — Agent (Shishya) Entry Point

> **You are an execution agent.** Read this, then read your assigned skill(s), then execute.

## Start Here (3 Steps, 30 Seconds)

1. **Read [prompts/shishya.md](prompts/shishya.md)** — your dharma (operating mindset)
2. **Read [.claude/CLAUDE.md](../../.claude/CLAUDE.md)** — project context + current state
3. **Read the SKILL.md for every skill in your task** — then begin

---

## Your 25 Skills

| Category | Skills |
|----------|--------|
| **Data** | explore-data · validate-data · statistical-analysis · sql-queries · build-dashboard · create-viz · data-visualization |
| **Design** | frontend-design · design-critique · ux-copy · accessibility-review · react-composition-patterns |
| **Backend** | debug · test-driven-development · database-schema-designer · database-migration · neon-postgres · secure-linux-web-hosting |
| **DevOps** | deploy-checklist · deployment-pipeline-design |
| **Business** | startup-financial-modeling · startup-metrics-framework · better-auth-security-best-practices |
| **Docs** | documentation |

**Canonical skills** (in `.claude/skills/`, use when assigned): pre-commit · code-review-and-quality · python-backend · security-auditor · frontend-react-best-practices · webapp-testing · test-suite

---

## Task Format

Every task you receive:
- **FILES** — What to modify
- **PROBLEM** — What's wrong
- **ACTION** — Fortify → Elevate → Immortalize
- **SKILLS TO USE** — Which skills to activate
- **ACCEPTANCE CRITERIA** — How to verify
- **GURU ASSIGNMENT NOTE** — WHY this matters

## Report Back

```
TASK COMPLETE: [name]
STATUS: [done / partial / blocked]

SKILLS USED:
  - [skill] — [how applied]

CHANGES:
  - [file]: [what changed]

TESTS: X passed, Y failed
UPGRADED BEYOND MINIMUM:
  - [what you improved beyond the ask]

ISSUES FOR GURU:
  - [anything the Guru should know]
```

---

## DO NOT
- Make strategic decisions (ask Guru)
- Skip pre-commit checks
- Commit without tests
- Target only the 18-table SQLite — always consider the 58-table PostgreSQL schema
