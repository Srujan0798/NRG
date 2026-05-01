---
name: Installed Skills Inventory
description: All skills available to NRG — Agent (Shishya) + Guru (Claude)
type: reference
---

## Current Repo Filesystem Count (2026-05-02)

Authoritative skill source for NRG is the repository itself:

- `.claude/skills/`
- `.agents/skills/`

Do not use `$CODEX_HOME`, plugin caches, or user-home skill inventories as the
project source of truth. A fresh clone of this repo should carry the same NRG
Guru/Shishya skill set.

Fresh inventory from direct repo directory comparison:

- **Agent/Shishya skill directories**: 51 under `.agents/skills/`
  - 50 use `SKILL.md`
  - 1 uses uppercase `SKILL.MD`: `better-auth-security-best-practices`
- **Guru/Claude skills**: 86 under `.claude/skills/`
- **Total repo-contained skill directories**: 137
- **Shared skill names between `.claude` and `.agents`**: 1 —
  `nrg-validation-campaign`

Detailed inventory: `evidence/2026-05-02/guru_shishya_validation/55_skill_inventory.tsv`
Usage ledger: `evidence/2026-05-02/guru_shishya_validation/56_skill_usage_ledger.md`

The older categorized list below is retained as historical context and is no longer the authoritative count.

## Agent Skills (`.agents/skills/`) — historical 31 total

Execution skills for Shishya (agent) work.

### Data — 7 skills
- `/explore-data` — Dataset profiling and quality checks
- `/validate-data` — QA analysis before sharing
- `/statistical-analysis` — Descriptive stats, trend analysis, hypothesis testing
- `/sql-queries` — Performant SQL across dialects
- `/build-dashboard` — Dashboard design and metrics
- `/create-viz` — Publication-quality Python visualizations
- `/data-visualization` — Matplotlib, seaborn, plotly charts

### Design — 5 skills
- `/frontend-design` — Production-grade web UI components
- `/design-critique` — Usability, hierarchy, consistency review
- `/ux-copy` — Microcopy, error messages, CTAs
- `/accessibility-review` — WCAG 2.1 AA audit
- `/react-composition-patterns` — Scalable React component architecture

### Backend — 5 skills
- `/debug` — Structured debugging session
- `/test-driven-development` — TDD workflow
- `/database-schema-designer` — SQL/NoSQL schema design
- `/database-migration` — Zero-downtime migrations
- `/secure-linux-web-hosting` — Server hardening, Nginx, HTTPS

### DevOps — 3 skills
- `/deploy-checklist` — Pre-deployment verification
- `/deployment-pipeline-design` — CI/CD with approval gates
- `/helm-chart-scaffolding` — Kubernetes Helm chart creation

### Security — 1 skill
- `/better-auth-security-best-practices` — Rate limiting, CSRF, session hardening

### AI/ML — 4 skills
- `/langgraph-fundamentals` — LangGraph orchestration patterns
- `/langchain-rag` — Retrieval-augmented generation
- `/fastapi-python` — FastAPI backend patterns
- `/vector-index-tuning` — Vector DB optimization (Qdrant)

### Database — 1 skill
- `/postgresql-table-design` — PostgreSQL schema design

### Monitoring — 1 skill
- `/prometheus-configuration` — Prometheus monitoring setup

### Docs — 1 skill
- `/documentation` — Technical docs, runbooks, READMEs

---

## Guru Skills (`.claude/skills/`) — historical 46 total

Strategy, review, and architecture skills for Guru (Claude) work.

### NRG Core — 14 skills
- `/test-suite` — Full test suite with coverage
- `/audit-check` — Audit chain integrity verification
- `/deploy-local` — Start full NRG stack locally
- `/code-review` — Deep multi-axis code review
- `/security-audit` — OWASP + sovereignty scan
- `/pre-commit` — Quality gate (MANDATORY before every commit)
- `/post-deploy` — Smoke test after deployment
- `/self-evolve` — Sprint analysis + system update
- `/architect` — CTO-level architecture decisions
- `/sprint-plan` — Sprint planning from backlog
- `/bug-hunt` — Root cause analysis
- `/performance` — Benchmark + regression detection
- `/docs-sync` — Documentation drift detection
- `/release-readiness` — Pre-release verification

### Strategy + Review — 14 skills
- `/architecture-adr` — Architecture decision records
- `/testing-strategy` — Test strategy design
- `/tech-debt` — Technical debt identification
- `/system-design` — Service and API design
- `/standup` — Standup update generation
- `/write-spec` — Feature spec / PRD writing
- `/stakeholder-update` — Tailored status updates
- `/metrics-review` — Product metrics analysis
- `/roadmap-update` — Roadmap creation and reprioritization
- `/compliance-check` — Regulatory compliance verification
- `/incident-response` — Incident triage and postmortem
- `/doc-coauthoring` — Structured documentation workflow
- `/external-audit` — External review coordination
- `/kubernetes-specialist` — Kubernetes architecture and deployment

### Engineering — 18 skills
- `/python-backend` — FastAPI, SQLAlchemy, Upstash patterns
- `/code-review-and-quality` — Quality standards
- `/security-auditor` — Vulnerability scanning
- `/frontend-react-best-practices` — React/Next.js optimization
- `/webapp-testing` — Playwright E2E testing
- `/prompt-engineering-patterns` — LLM prompt design
- `/dockerfile-validator` — Dockerfile security audit
- `/database-migrations-sql-migrations` — SQL migration patterns
- `/typescript-advanced-types` — Advanced TS type system
- `/changelog-generator` — Automated changelog from commits
- `/claude-api` — Anthropic SDK optimization
- `/external-prompt-merge` — External prompt integration
- `/find-skills` — Skill discovery and installation
- `/nodejs-backend-patterns` — Node.js backend patterns
- `/incident-response` — Incident triage and postmortem
- `/metrics-review` — Product metrics analysis
- `/performance` — Benchmark + regression detection
- `/tech-debt` — Technical debt identification

---

## Historical Total: 77 skills

- **Agent (Shishya)**: 31 skills in `.agents/skills/`
- **Guru (Claude)**: 46 skills in `.claude/skills/`

Last updated: 2026-05-02
