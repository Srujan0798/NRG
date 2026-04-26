---
name: Installed Skills Inventory
description: All 23 skills available to agents — 10 global community skills + 13 NRG project skills
type: reference
---

## Global Skills (installed via `npx skills`, available in ~/.agents/skills/)
1. `/python-backend` — Python/FastAPI patterns (jiatastic/open-python-skills)
2. `/code-review-and-quality` — Code review standards (addyosmani/agent-skills)
3. `/security-auditor` — Security vulnerability detection (ovachiever/droid-tings)
4. `/frontend-react-best-practices` — React/TypeScript patterns (sergiodxa/agent-skills)
5. `/webapp-testing` — E2E + integration testing (anthropics/skills — 51K installs)
6. `/prompt-engineering-patterns` — LLM prompt design (sickn33/antigravity-awesome-skills)
7. `/dockerfile-validator` — Docker/compose validation (akin-ozer/cc-devops-skills)
8. `/database-migrations-sql-migrations` — Alembic/SQL migrations (sickn33/antigravity-awesome-skills)
9. `/typescript-advanced-types` — Advanced TS types
10. `/nodejs-backend-patterns` — Node.js patterns

## Project Skills (in .claude/skills/)
11. `/test-suite` — Run all NRG tests
12. `/pre-commit` — Quality gate (MANDATORY before every commit)
13. `/code-review` — NRG-specific deep review
14. `/security-audit` — OWASP + sovereignty scan
15. `/self-evolve` — Sprint analysis + system update
16. `/architect` — Architecture decisions + ADRs
17. `/sprint-plan` — Sprint planning from backlog
18. `/bug-hunt` — Root cause analysis
19. `/performance` — Benchmark + regression check
20. `/post-deploy` — Deployment smoke test
21. `/docs-sync` — Documentation drift detection
22. `/audit-check` — HMAC audit chain verification
23. `/deploy-local` — Local stack deployment

**How to apply:** When assigning tasks, always specify which skills from this list the agent must use. Agents must report back which skills they activated and how they applied them.
