# FINAL SKILL AUDIT — Claude's Recommendation

**Role:** You are using me as Claude (your assistant), not as an agent.  
**Date:** 2026-04-25  
**Decision:** Clean up after demo. Here's the exact plan.

---

## THE PROBLEM

You have **91 skills across 2 directories** with **26 exact duplicates**. This creates:
- Confusion about which skill to invoke
- Wasted context window when I scan for relevant skills
- Maintenance debt when updating skill content

---

## THE PRINCIPLE

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `.claude/skills/` | **Claude Code** (me) | Generic software engineering skills — things I'd use across ANY project |
| `.agents/skills/` | **Your agents** (Kimi, etc.) | NRG-specific skills + anything your agent swarm needs |

**Rule:** If a skill is generic (applies to any FastAPI/React project), it lives in `.claude/skills/`. If it's NRG-specific (RAG, sovereign mesh, DPDP compliance), it lives in `.agents/skills/`.

---

## DECISION 1: Delete 8 Irrelevant Skills (do now)

These don't match your stack. No value keeping them.

| Skill | Location | Why Delete |
|-------|----------|------------|
| `nodejs-backend-patterns` | `.claude/` | You use Python/FastAPI |
| `neon-postgres` | `.agents/` | You use SQLite |
| `secure-linux-web-hosting` | `.agents/` | Demo runs locally |
| `startup-financial-modeling` | `.agents/` | Not a startup |
| `startup-metrics-framework` | `.agents/` | Not a SaaS product |
| `claude-api` | `.claude/` | You use Minimax/NVIDIA mesh |
| `vercel-react-best-practices` | `.agents/` | Duplicate of `frontend-react-best-practices` |
| `react-composition-patterns` | `.agents/` | Overlaps with existing frontend skills |

**Action:** `rm -rf` these 8 directories.

---

## DECISION 2: Deduplicate 24 Skills (do after demo)

Same skill exists in both places. Keep the `.agents/` version (your agents need them). Delete from `.claude/`.

```
architect, audit-check, bug-hunt, changelog-generator,
code-review, code-review-and-quality, database-migrations-sql-migrations,
deploy-local, dockerfile-validator, docs-sync, find-skills,
frontend-react-best-practices, incident-response, nodejs-backend-patterns,
performance, post-deploy, pre-commit, prompt-engineering-patterns,
python-backend, security-audit, security-auditor, self-evolve,
sprint-plan, test-suite, typescript-advanced-types, webapp-testing
```

**Action:** After demo, delete these 24 from `.claude/skills/`.

---

## DECISION 3: Keep These 13 in `.claude/skills/` (never delete)

These are unique, generic, and actively triggered by your workflow.

| Skill | Why Keep |
|-------|----------|
| `architecture-adr` | You have 10 ADRs in `docs/adr/` |
| `compliance-check` | DPDP compliance is a core NRG feature |
| `demo-readiness` | Created for this sprint, actively used |
| `doc-coauthoring` | You write specs, proposals, docs frequently |
| `external-audit` | v4.1 protocol requires this |
| `metrics-review` | Benchmarks exist in `tests/benchmarks/` |
| `python-backend` | FastAPI development is ongoing |
| `roadmap-update` | You maintain product roadmaps |
| `standup` | Personal workflow, no harm keeping |
| `system-design` | Triggered by architecture discussions |
| `tech-debt` | ESLint warnings, Qdrant empty = active debt |
| `testing-strategy` | 33 test directories, strategy matters |
| `write-spec` | Feature specs are your starting point |

---

## DECISION 4: Keep These 27 in `.agents/skills/` (never delete)

These are either NRG-specific or your agents' tools.

| Skill | Why Keep |
|-------|----------|
| `accessibility-review` | Frontend needs a11y checks |
| `better-auth-security-best-practices` | Auth is critical |
| `build-dashboard` | Dashboard is part of demo |
| `create-viz` | Publication-quality viz |
| `data-visualization` | Data storytelling |
| `database-migration` | Schema changes happen |
| `database-schema-designer` | DB design skill |
| `debug` | Structured debugging |
| `deploy-checklist` | Pre-deploy verification |
| `deployment-pipeline-design` | CI/CD exists |
| `design-critique` | UX review |
| `documentation` | Technical writing |
| `explore-data` | Dataset profiling |
| `frontend-design` | Distinctive UI creation |
| `sql-queries` | SQL generation |
| `statistical-analysis` | Research data analysis |
| `test-driven-development` | TDD workflow |
| `ux-copy` | Microcopy, error messages |
| `validate-data` | QA before sharing |
| + 8 more | Various utility skills |

---

## THE FINAL LAYOUT (after cleanup)

```
.claude/skills/          → 13 skills (generic engineering)
.agents/skills/          → ~43 skills (NRG-specific + generic)
TOTAL: 56 skills (down from 91)
```

---

## EXECUTION ORDER

1. **Now:** Delete the 8 irrelevant skills (Decision 1)
2. **After demo:** Delete the 24 duplicates from `.claude/skills/` (Decision 2)
3. **Never touch:** The 13 in Decision 3 and 27 in Decision 4

---

## DO YOU WANT ME TO EXECUTE DECISION 1 NOW?

The 8 irrelevant skills are safe to delete immediately — they don't affect the demo. Say yes and I'll remove them.
