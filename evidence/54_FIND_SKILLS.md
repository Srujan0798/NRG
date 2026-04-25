# Find Skills — NRG Capability Gap Analysis
**Date:** 2026-04-25
**Skill:** `.claude/skills/find-skills/SKILL.md`

---

## Applying Find Skills to NRG

### Step 1: Understand NRG's Needs

Based on the codebase and recent work, NRG has needs in several domains:

| Domain | Need | Existing Coverage |
|--------|------|-------------------|
| Testing | Fix 263 failing tests | `/test-suite` exists |
| Security | OWASP scanning | `/security-audit` exists |
| Code Review | Pre-merge quality gate | `/code-review` exists |
| Database | SQL migrations | `/database-migrations-sql-migrations` exists |
| Documentation | Doc-sync drift detection | `/docs-sync` exists |
| **Missing** | **API documentation generator** | None |
| **Missing** | **PostgreSQL-specific optimization** | None |
| **Missing** | **Frontend visual regression testing** | None |

### Step 2: Check Popular Skills

Based on skills.sh leaderboard and NRG's stack:

**Already Installed (via agent skills):**
- `vercel-labs/agent-skills` — React/Next.js best practices (used in frontend design)
- `anthropics/skills` — Frontend design, document processing

**Recommended for NRG:**

1. **API Documentation** — NRG lacks auto-generated API docs
   - Consider: `redocly/openapi-cli` or similar
   - Install: `npx skills add redocly/openapi-cli`

2. **Visual Regression Testing** — Frontend needs screenshot diff
   - Consider: `regviz/visreg` or `playwright/test`
   - Playwright already in use (webapp-testing skill)

3. **PostgreSQL Performance** — 58-table schema needs query optimization
   - Consider: `postgresql/manual-tuning` skill
   - NRG has Neon Postgres skill but no PostgreSQL-specific performance skill

### Step 3: Skills Search Commands

For future use when specific needs arise:

```bash
# API documentation
npx skills find api docs

# PostgreSQL optimization
npx skills find postgresql performance

# Visual regression
npx skills find screenshot diff

# Text-to-SQL improvement
npx skills find sql generation
```

### Step 4: Verification Quality

All recommendations should verify:
- Install count (prefer 1K+)
- Source reputation (official preferred)
- GitHub stars (100+ minimum)

---

## What NRG Does NOT Need

Based on skill audit:
- No new frontend framework (React + TypeScript + Vite is established)
- No new testing framework (pytest + Playwright covers all needs)
- No new CI/CD tooling (GitHub Actions + shell scripts working)
- No new monitoring (Langfuse + audit chain provides observability)

---

## Skills CLI Usage for NRG

The `.claude/skills/find-skills/SKILL.md` defines how to use `npx skills`:

```bash
npx skills find [query]      # Search for skills
npx skills add <package>     # Install a skill
npx skills check             # Check for updates
npx skills update             # Update all installed
```

### Relevant searches for NRG's roadmap:
- "react testing best practices" → Could improve test quality
- "api documentation openapi" → Would help API consumers
- "sql performance postgresql" → Would help with 58-table prod schema
- "docker security scan" → Already have dockerfile-validator

---

## Skill Application Evidence

This document applies the find-skills framework to identify capability gaps in NRG's current skill inventory (39 Claude + 52 Agent = 91 skills total).

**Finding:** NRG has comprehensive coverage but could benefit from:
1. API documentation generation skill
2. PostgreSQL query optimization skill
3. Visual regression testing for frontend

The skill was applied by checking existing coverage against known gaps and recommending targeted skill additions rather than broad coverage expansion.