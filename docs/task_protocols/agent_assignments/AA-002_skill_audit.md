# Skill Audit: Claude Marketplace vs. Your Current Stack

**Date:** 2026-04-25  
**Scope:** Cross-reference Claude Cowork marketplace plugins against `.claude/skills/` and `.agents/skills/`

---

## ✅ ALREADY COVERED — You have equivalent or better

| Marketplace Plugin | What it does | Your equivalent skill(s) | Location |
|---|---|---|---|
| **Engineering** | Standups, code review, architecture, incidents, tech docs | `code-review`, `code-review-and-quality`, `python-backend`, `nodejs-backend-patterns`, `system-design`, `incident-response`, `tech-debt`, `test-suite`, `testing-strategy`, `pre-commit`, `dockerfile-validator` | `.claude/skills/` |
| **Data** | SQL, datasets, visualizations, dashboards | `explore-data`, `create-viz`, `data-visualization`, `sql-queries`, `statistical-analysis`, `validate-data`, `database-schema-designer` | `.agents/skills/` |
| **Productivity** | Tasks, planning, persistent memory | `standup`, `sprint-plan`, `stakeholder-update`, `roadmap-update`, `doc-coauthoring`, `write-spec` | `.claude/skills/` |
| **Product Management** | Feature specs, roadmaps, user research | `write-spec`, `roadmap-update`, `system-design`, `architecture-adr` | `.claude/skills/` |
| **Design** | UX critique, accessibility, dev handoff | `design-critique`, `accessibility-review`, `frontend-design`, `ux-copy`, `build-dashboard`, `create-viz` | `.agents/skills/` |
| **Security** | Security audit, compliance | `security-audit`, `security-auditor`, `compliance-check`, `better-auth-security-best-practices` | `.claude/skills/` + `.agents/skills/` |
| **Operations** | Vendor mgmt, process docs, change mgmt | `deploy-checklist`, `deployment-pipeline-design`, `performance`, `post-deploy`, `deploy-local` | `.claude/skills/` + `.agents/skills/` |
| **Testing** | Test strategies, coverage | `test-suite`, `testing-strategy`, `test-driven-development`, `webapp-testing` | `.claude/skills/` + `.agents/skills/` |

---

## ⚠️ PARTIALLY COVERED — You have something close, but marketplace version may have extras

| Marketplace Plugin | Gap / Difference | Your current skill | Recommendation |
|---|---|---|---|
| **Cowork Plugin Management** | Create/manage MCP servers & plugins for your org | None | **Not needed now** — you don't have a plugin ecosystem yet |
| **Bio Research** | Preclinical research tools, life sciences DBs | None specific to bio | You have research data but it's general academic, not preclinical. **Skip unless** you add medical/life sciences datasets |
| **Enterprise Search** | Search across email, chat, docs, wikis | Your own RAG retriever | You have custom RAG in `src/skills/rag/`. **Skip** — external plugin won't integrate with your RBAC/audit chain |

---

## ❌ NOT RELEVANT — Skip these for NRG

| Marketplace Plugin | Why skip |
|---|---|
| **Slack** | External integration. Not needed for a sovereign research DB demo |
| **Sales** | Not a sales tool |
| **Marketing** | Not a marketing product (yet) |
| **Legal** | No contract review workflows |
| **Finance** | No finance workflows |
| **Wealth Management** | Irrelevant |
| **Private Equity** | Irrelevant |
| **Investment Banking** | Irrelevant |
| **Financial Analysis** | Irrelevant |
| **Equity Research** | Irrelevant — yours is *academic* research, not equity research |
| **Apollo** | Sales prospecting API. Irrelevant |
| **S&P Global** | Financial data API. Irrelevant |
| **LSEG** | Market data API. Irrelevant |
| **Common Room** | GTM/signal data. Irrelevant |
| **Customer Support** | No support ticket workflow |
| **Human Resources** | No HR workflow |
| **Brand Voice** | You have NRG brand/constitution already in `NRG_CONSTITUTION.md` |

---

## 🔍 GAPS — Skills you DON'T have that might help NRG

| Missing Skill | Why it could help | Priority |
|---|---|---|
| **Database monitoring / query perf tuning** | Your SQL queries may slow down with scale | Low (SQLite is fine for demo) |
| **Load testing / chaos engineering** | You have `tests/chaos/` but no skill guiding it | Medium |
| **API documentation auto-generation** | FastAPI has Swagger, but no skill for maintaining API docs | Low |
| **Migration rollback playbooks** | You have DB migration skills but no incident rollback skill | Low |
| **Observability / SLO monitoring** | You have `performance` skill but no dedicated SLO/dashboard skill | Low |
| **Research paper ingestion pipeline** | You lost Qdrant vectors — no skill for re-ingestion | **High** (Agent B is handling this) |

---

## 📁 RECOMMENDATION: Skill Consolidation

You have **significant overlap** between `.claude/skills/` and `.agents/skills/`:

| Skill | In `.claude/` | In `.agents/` | Redundant? |
|---|---|---|---|
| `code-review` | ✅ | ✅ | Yes — keep `.agents/` version (newer) |
| `code-review-and-quality` | ✅ | ✅ | Yes — same content |
| `security-audit` | ✅ | ✅ | Yes — keep `.claude/` version (has OWASP scanner) |
| `security-auditor` | ✅ | ✅ | Yes — `.claude/` version is more detailed |
| `test-suite` | ✅ | ✅ | Yes — same content |
| `pre-commit` | ✅ | ✅ | Yes — same content |
| `deploy-local` | ✅ | ✅ | Yes — same content |
| `dockerfile-validator` | ✅ | ✅ | Yes — same content |
| `performance` | ✅ | ✅ | Yes — same content |
| `post-deploy` | ✅ | ✅ | Yes — same content |
| `typescript-advanced-types` | ✅ | ✅ | Yes — same content |
| `frontend-react-best-practices` | ✅ | ✅ | Yes — same content |
| `webapp-testing` | ✅ | ✅ | Yes — same content |
| `nodejs-backend-patterns` | ✅ | ✅ | Yes — same content |
| `find-skills` | ✅ | ✅ | Yes — same content |
| `incident-response` | ✅ | ✅ | Yes — same content |
| `prompt-engineering-patterns` | ✅ | ✅ | Yes — same content |
| `bug-hunt` | ✅ | ✅ | Yes — same content |
| `changelog-generator` | ✅ | ✅ | Yes — same content |
| `docs-sync` | ✅ | ✅ | Yes — same content |
| `python-backend` | ✅ | ❌ | Keep in `.claude/` |

### Suggested cleanup ( AFTER demo ):
1. **Merge duplicates** — keep the more detailed version in each case
2. **Move NRG-specific skills** to `.agents/skills/` (your agent workspace)
3. **Keep generic skills** in `.claude/skills/` (Claude Code workspace)

---

## 🎯 VERDICT FOR DEMO SPRINT

**You already have everything you need.** None of the marketplace plugins would materially improve your demo readiness. Your custom skills are actually *better* for NRG because they're tailored to your stack (FastAPI, SQLite, Qdrant, React, Tailwind, Minimax mesh).

The only action item: **Agent B should check if there's a marketplace plugin for research paper ingestion / vector DB management** — but honestly, your `scripts/ingest_research_papers.py` is probably more tailored anyway.

---

## 📋 NEXT: Claude Code Skills Review

When you're ready, I can audit your `.claude/skills/` directory specifically and flag:
1. Which skills are actively triggered by your codebase
2. Which skills have never been used
3. Which skills need updating to match current code patterns

Just say the word.
