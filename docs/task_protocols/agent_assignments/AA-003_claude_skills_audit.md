# Claude Code Skills Audit — NRG Relevance Analysis

**Date:** 2026-04-25  
**Scope:** `.claude/skills/` (40 skills) — which are active, dormant, or irrelevant for NRG

---

## 🔴 IRRELEVANT — Safe to remove from `.claude/skills/`

These skills target tech stacks or workflows NRG doesn't use.

| Skill | Why Irrelevant | Trigger Check |
|---|---|---|
| `nodejs-backend-patterns` | NRG uses **Python/FastAPI**, not Node.js | No Express/Fastify/Koa in codebase |
| `neon-postgres` | NRG uses **SQLite**, not Neon Postgres | No neon imports, no postgres driver |
| `secure-linux-web-hosting` | NRG runs locally/demo, not self-hosted Linux server | No server hardening scripts |
| `startup-financial-modeling` | NRG is a research DB, not a startup raising funds | No financial models |
| `startup-metrics-framework` | No SaaS metrics needed | No CAC/LTV/burn tracking |
| `claude-api` | NRG uses **Minimax/NVIDIA**, not Anthropic SDK | No `anthropic` imports (except maybe in old code) |
| `vercel-react-best-practices` | You already have `frontend-react-best-practices` | Duplicate domain |
| `react-composition-patterns` | Covered by `frontend-react-best-practices` + `typescript-advanced-types` | Overlap |

**→ Remove count: 8 skills**

---

## 🟡 DUPLICATES — You have better version in `.agents/skills/`

Keep the `.agents/` version (it's your agent workspace), remove from `.claude/`.

| Skill | `.claude/` version | `.agents/` version | Recommendation |
|---|---|---|---|
| `code-review` | Basic | Same content | Remove `.claude/` |
| `code-review-and-quality` | Same | Same | Remove `.claude/` |
| `security-audit` | OWASP scanner | Same | Remove `.claude/` |
| `security-auditor` | Same | Same | Remove `.claude/` |
| `test-suite` | Same | Same | Remove `.claude/` |
| `pre-commit` | Same | Same | Remove `.claude/` |
| `deploy-local` | Same | Same | Remove `.claude/` |
| `dockerfile-validator` | Same | Same | Remove `.claude/` |
| `performance` | Same | Same | Remove `.claude/` |
| `post-deploy` | Same | Same | Remove `.claude/` |
| `typescript-advanced-types` | Same | Same | Remove `.claude/` |
| `frontend-react-best-practices` | Same | Same | Remove `.claude/` |
| `webapp-testing` | Same | Same | Remove `.claude/` |
| `find-skills` | Same | Same | Remove `.claude/` |
| `incident-response` | Same | Same | Remove `.claude/` |
| `prompt-engineering-patterns` | Same | Same | Remove `.claude/` |
| `bug-hunt` | Same | Same | Remove `.claude/` |
| `changelog-generator` | Same | Same | Remove `.claude/` |
| `docs-sync` | Same | Same | Remove `.claude/` |
| `database-migrations-sql-migrations` | Same | Same | Remove `.claude/` |
| `audit-check` | Same | Same | Remove `.claude/` |
| `self-evolve` | Same | Same | Remove `.claude/` |
| `sprint-plan` | Same | Same | Remove `.claude/` |
| `architect` | Same | Same | Remove `.claude/` |

**→ Remove count: 24 skills**

---

## 🟢 KEEP — Unique to `.claude/skills/` and relevant to NRG

| Skill | Why Keep | Active Trigger |
|---|---|---|
| `architecture-adr` | NRG has 10 ADRs in `docs/adr/` | ✅ Active — used for tech decisions |
| `compliance-check` | NRG has DPDP compliance, audit chain | ✅ Active — compliance is core feature |
| `demo-readiness` | Created FOR this demo sprint | ✅ Active — just created |
| `doc-coauthoring` | You write a lot of specs/docs | ✅ Active — `write-spec` triggers this |
| `external-audit` | Created for v4.1 protocol | ✅ Active — just created |
| `metrics-review` | NRG has SLO tracking, benchmarks | ⚠️ Dormant — `tests/benchmarks/` exists but skill rarely triggered |
| `python-backend` | NRG is Python/FastAPI | ✅ Active — every backend change triggers this |
| `roadmap-update` | You maintain roadmaps | ⚠️ Dormant — not actively maintained |
| `standup` | Useful for your workflow | ⚠️ Dormant — personal productivity, not codebase |
| `system-design` | Used for architecture decisions | ✅ Active — triggered by "design a system" queries |
| `tech-debt` | NRG has debt (96→7 ESLint warnings, Qdrant empty) | ✅ Active — triggered by "tech debt" queries |
| `testing-strategy` | NRG has 8 chaos tests, 17 e2e, 5 contract tests | ✅ Active — testing is ongoing |
| `write-spec` | You write feature specs | ✅ Active — triggered by spec writing |

**→ Keep count: 13 skills**

---

## ⚠️ BORDERLINE — Evaluate after demo

| Skill | Verdict |
|---|---|
| `metrics-review` | Keep if you start doing weekly metrics reviews. Dormant now. |
| `roadmap-update` | Keep if you actively maintain `docs/roadmap/`. Dormant now. |
| `standup` | Personal workflow skill — doesn't hurt to keep, but not codebase-related. |

---

## 📊 SUMMARY

| Category | Count | Action |
|---|---|---|
| **🔴 Remove (irrelevant)** | 8 | `nodejs-backend-patterns`, `neon-postgres`, `secure-linux-web-hosting`, `startup-financial-modeling`, `startup-metrics-framework`, `claude-api`, `vercel-react-best-practices`, `react-composition-patterns` |
| **🟡 Remove (duplicate)** | 24 | See full list above — all exist in `.agents/skills/` |
| **🟢 Keep** | 13 | Unique and relevant to NRG |
| **⚠️ Evaluate later** | 3 | `metrics-review`, `roadmap-update`, `standup` |

### Before cleanup: 40 skills
### After cleanup: ~16 skills (60% reduction)

---

## 🧹 RECOMMENDED CLEANUP COMMAND

```bash
cd /Users/srujansai/Desktop/NRG

# Step 1: Remove irrelevant skills
rm -rf .claude/skills/nodejs-backend-patterns
rm -rf .claude/skills/neon-postgres
rm -rf .claude/skills/secure-linux-web-hosting
rm -rf .claude/skills/startup-financial-modeling
rm -rf .claude/skills/startup-metrics-framework
rm -rf .claude/skills/claude-api
rm -rf .claude/skills/vercel-react-best-practices
rm -rf .claude/skills/react-composition-patterns

# Step 2: Remove duplicates (keep .agents/ version)
for skill in code-review code-review-and-quality security-audit security-auditor test-suite pre-commit deploy-local dockerfile-validator performance post-deploy typescript-advanced-types frontend-react-best-practices webapp-testing find-skills incident-response prompt-engineering-patterns bug-hunt changelog-generator docs-sync database-migrations-sql-migrations audit-check self-evolve sprint-plan architect; do
  rm -rf ".claude/skills/$skill"
done

# Result: ~16 skills remain in .claude/skills/
```

---

## 📁 WHERE SKILLS SHOULD LIVE

| Location | Purpose | Skills |
|---|---|---|
| `.claude/skills/` | Claude Code IDE skills — generic, codebase-agnostic | `architecture-adr`, `compliance-check`, `demo-readiness`, `doc-coauthoring`, `external-audit`, `metrics-review`, `python-backend`, `roadmap-update`, `standup`, `system-design`, `tech-debt`, `testing-strategy`, `write-spec` |
| `.agents/skills/` | Kimi/Agent workspace — NRG-specific and generic | Everything else: `accessibility-review`, `build-dashboard`, `create-viz`, `data-visualization`, `database-schema-designer`, `debug`, `deploy-checklist`, `deployment-pipeline-design`, `design-critique`, `documentation`, `explore-data`, `frontend-design`, `sql-queries`, `statistical-analysis`, `test-driven-development`, `ux-copy`, `validate-data`, etc. |

---

## 🎯 ACTION NEEDED FROM YOU

1. **Approve the cleanup?** — I can run the removal commands above.
2. **Keep any of the "irrelevant" skills?** — e.g., `claude-api` if you plan to migrate to Anthropic later.
3. **Move any `.agents/` skills to `.claude/`?** — e.g., should `database-schema-designer` live in both?

Say the word and I'll execute.
