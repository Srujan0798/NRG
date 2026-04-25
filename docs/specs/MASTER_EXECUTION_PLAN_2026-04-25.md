# NRG — MASTER EXECUTION PLAN (PRODUCTION LAUNCH)
**Date:** 2026-04-25
**Status:** SUPERSEDES all prior demo-framed specs
**Target:** Production deployment of NRG as a real, secure, audit-bound research-intelligence service for IIT Gandhinagar + Government of India ministries
**Operating constraint:** **No demo framing.** No "demo-ready", no "pitch", no "rehearsal". Every milestone below is a production hardening or capability launch.

---

## SUPERSEDED DOCUMENTS

The following documents I authored earlier today contained demo-framing language and are **superseded by this plan and `docs/task_protocols/PRODUCTION_READINESS_MASTER.md`**:

| File | Status |
|---|---|
| `docs/specs/FRONTEND_UX_MASTER_SPEC_2026-04-25.md` | SUPERSEDED — re-read with the framing-correction in §4 of this plan; do not use the "demo" sections |
| `docs/specs/AGENT_TASK_PACK_2026-04-25.md` | SUPERSEDED — task IDs T01–T19 are still valid as engineering work, but framing is replaced by production milestones below |
| `docs/specs/CLOSURE_ROADMAP_2026-04-25.md` | SUPERSEDED — entire timeline replaced by the 4-week production roadmap below |
| `docs/specs/NRG_COMPLETE_STRATEGIC_VIEW_2026-04-25.md` | SUPERSEDED — vision section is fine; demo-focused sections are voided |

The frontend implementation tasks themselves (T01 through T19 in the task pack) remain valid engineering work — what changes is **why** they exist: not to look good in a presentation, but to serve real users at scale under DPDP compliance.

---

## 1. THE SINGLE SOURCE OF TRUTH

This document is the unified plan. It merges:

- **`docs/task_protocols/PRODUCTION_READINESS_MASTER.md`** — your agents' 8-milestone production roadmap (infrastructure, database, auth, security, performance, monitoring, CI/CD, documentation)
- **Frontend production tasks** — the user-facing surface that real researchers, government officials, and industry partners will use every day
- **Cross-layer hardening tasks** — observability, knowledge layer, retrieval layer, fine-tune foundation
- **Founder operations tasks** — institutional sign-off, SSO integration, security review, launch approval

Every other planning document either references this plan or is superseded by it.

---

## 2. WHAT NRG IS (PRODUCTION FRAMING — read once)

NRG is a production web application deployed on Indian-soil infrastructure that serves three classes of authenticated users:

- **Researchers** at IIT Gandhinagar and partner institutions, who query the system to find collaborators, funding opportunities, citation networks, and field-level trends.
- **Government officials** at MoE, DST, MeitY, and partner ministries, who query the system to make policy decisions on research funding, TRL progression, and institute capacity.
- **Industry partners** (vetted, NDA-bound), who query the system through an anonymized lens to identify research opportunities, technology transfer candidates, and seed-funding successes.

Every query is authenticated via institutional SSO, authorized via tier-aware RBAC, sanitized for PII and prompt injection, executed against a 600GB PostgreSQL knowledge base of the national research graph, retrieved through a hybrid SQL + vector pipeline, synthesized through a 5-provider LLM mesh with circuit breakers and local SLM fallback, verified for citation faithfulness, signed with a per-user HMAC + Postgres co-sign trigger forming a non-repudiation chain, and returned to the user in under 2 seconds at the 95th percentile under sustained 100-user concurrent load.

Uptime target: **99.9%**. Compliance: **DPDP Act 2023**, IITGN-certified. Data residency: **Indian soil only**, region-locked by Helm values.

---

## 3. THE UNIFIED 4-WEEK ROADMAP

This is the merge of your agents' 8 milestones with the frontend and cross-layer work. Eight milestones, four weeks, ~45 named tasks.

### WEEK 1 — INFRASTRUCTURE + DATABASE FOUNDATION

**M1 — Infrastructure (your agents' M1)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M1.1 | Provision bare-metal / VM in Indian data center | DevOps-Bot | Server reachable; root SSH; OS hardened |
| M1.2 | Dockerize backend (`docker build -t nrg-api .`) | Hephaestus-Backend | Image builds; runs locally; non-root user |
| M1.3 | Dockerize frontend (`docker build -t nrg-frontend .`) | Vulcan-Perf | Image < 60MB gz; nginx-served React build |
| M1.4 | Production `docker-compose.prod.yml` | DevOps-Bot | Stack starts: API + frontend + PG + Qdrant + Redis |
| M1.5 | Nginx reverse proxy with TLS termination | DevOps-Bot | HTTPS only; HTTP → HTTPS redirect; HSTS |
| M1.6 | Domain + DNS (`nrg.iitgn.ac.in` or equivalent) | Founder + DevOps | Cert valid; A/AAAA records; CAA record set |
| M1.7 | Let's Encrypt auto-renew via cert-manager or certbot | DevOps-Bot | 90-day auto-renew tested |

**M2 — Database (your agents' M2)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M2.1 | PostgreSQL 15+ deployed with proper users/roles | Hephaestus-Backend | Three roles: `nrg_app`, `nrg_readonly`, `nrg_admin` |
| M2.2 | Alembic migrations bring all 58 tables to parity with `db_struct.sql` | Hephaestus-Backend | `pytest tests/data/test_schema_parity.py` green against PG |
| M2.3 | Data migration: SQLite → PostgreSQL | Hephaestus-Backend | All seeded rows migrated; row-count checks match |
| M2.4 | Connection pooling (SQLAlchemy `pool_size=20`, `max_overflow=40`) | Hephaestus-Backend | Load test confirms no pool exhaustion at 100 users |
| M2.5 | Daily automated backups to S3-compatible Indian-region storage | DevOps-Bot | Cron tested; 30-day retention; encryption at rest |
| M2.6 | Restore-from-backup tested end-to-end | DevOps-Bot | Restore in < 60 minutes; verified row counts |
| M2.7 | Row-Level Security policies deployed at PG layer (not app-only) | Hephaestus-Backend | T3 user cannot SELECT email/aadhaar even with raw SQL |

### WEEK 2 — AUTH + SECURITY HARDENING

**M3 — Authentication (your agents' M3)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M3.1 | Remove all hardcoded credentials from codebase, env files, fixtures | Security-Sentinel | `grep -r "researcher-pass\|gov-pass\|industry-pass" .` returns 0 |
| M3.2 | Institutional SSO (SAML or OAuth2) with IIT GN auth system | Hephaestus-Backend | Login redirects to IITGN IdP; JWT issued from claims |
| M3.3 | Government-tier IP allowlist (configurable, enforced at middleware) | Security-Sentinel | T2 from non-allowlisted IP → 403 with clear message |
| M3.4 | Password / session policy (12-char min, rotation, refresh tokens, HttpOnly + SameSite cookies) | Security-Sentinel | OWASP session management checklist pass |
| M3.5 | Admin UI to provision/disable accounts | Hermes-UI + Hephaestus-Backend | `/admin/users` (T1+admin only) with audit logging |
| M3.6 | Account lifecycle: account creation → audit event in chain | Hephaestus-Backend | Every account create/disable signed in HMAC chain |

**M4 — Security Hardening (your agents' M4)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M4.1 | Remove or auth-protect `/debug`, `/docs`, `/openapi.json` in prod | Security-Sentinel | Only accessible behind admin SSO |
| M4.2 | CORS lockdown to configured production domain only | Security-Sentinel | Wildcard origins removed; preflight returns explicit Allow-Origin |
| M4.3 | Per-IP + per-user rate limits, configurable per tier | Security-Sentinel | Rate-limit middleware tested with burst test |
| M4.4 | SQL injection + XSS + command injection systematic test | Cassandra-QA | sqlmap clean; reflected/stored XSS clean |
| M4.5 | Secrets in HashiCorp Vault (or env files mode 600) | Security-Sentinel | No secret in git history; Vault sidecar wired |
| M4.6 | `pip-audit` and `npm audit` zero critical/high | Security-Sentinel | CI fails build if any critical CVE introduced |
| M4.7 | Container hardening: non-root user, read-only FS, distroless base | Security-Sentinel | `docker scout` reports no high CVEs |
| M4.8 | NetworkPolicy: PG, Qdrant, Redis not exposed externally | DevOps-Bot | `nmap` from outside the cluster shows only 443 open |
| M4.9 | Live RT-01..RT-30 red-team replay against the running production stack | Cassandra-QA | `evidence/<launch-date>/red_team_results.md` 25/25 BLOCKED on security attacks |

### WEEK 2–3 — FRONTEND + PERFORMANCE

**M5a — Frontend Production Hardening (the user-facing surface)**

These map 1:1 to the engineering work previously tracked as T01–T15 in the (superseded) task pack. Renumbered for production framing.

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M5a.1 | Cleanup duplicate component files (8 known pairs) | Vulcan-Perf | No duplicate basenames in `frontend/src/components/`; eslint rule enforces |
| M5a.2 | Design token audit — zero raw hex/px in components | Vulcan-Perf | Build-fail test passes |
| M5a.3 | Self-hosted fonts + preload (sovereignty, no Google Fonts CDN) | Vulcan-Perf | Lighthouse: no external font requests |
| M5a.4 | Hero query screen (autofocused input, 4 query templates, scale strip) | Hermes-UI | TTI < 1500ms on slow 3G |
| M5a.5 | Streaming response UX (4 SSE phases, never blank > 200ms) | Apollo-Polish | E2E test asserts 200ms first feedback, 4 phases visible |
| M5a.6 | Persona switcher (real users switch tier when they have multiple roles) | Hermes-UI | ARIA tablist; keyboard nav; tier change re-issues last query under new JWT |
| M5a.7 | Citation drawer with HMAC proof panel + verify-on-chain | Apollo-Polish | Drawer opens in <240ms; verify in <500ms |
| M5a.8 | Audit panel `/app/audit` with virtualized event list | Apollo-Polish | List handles 400k+ events; row click → drawer |
| M5a.9 | 3 tier dashboards (Researcher / Government / Industry) | Hermes-UI | Each renders production cards with real data; tier-correct anonymization |
| M5a.10 | All 6 empty states + 3 error tiers (sacred no-stack-trace test) | Athena-UX | Build fails on any `<pre>`/`Error:`/`Traceback` in error routes |
| M5a.11 | Microcopy library + forbidden-vocab build grep | Athena-UX | Production-only language enforced; `production_only.md` rule applied |
| M5a.12 | Accessibility WCAG 2.1 AA pass | Iris-A11y | axe-core 0 errors per route |
| M5a.13 | Mobile (393px) full E2E on iOS Safari and Android Chrome | Iris-A11y | Real-device test recorded |
| M5a.14 | Frontend telemetry events to `/api/telemetry` | Vulcan-Perf | All 10 event types firing; PII-stripped at edge |
| M5a.15 | Storybook + visual regression CI gate | Vulcan-Perf | Loki/Chromatic on every PR |

**M5b — Performance (your agents' M5)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M5b.1 | Redis caching for query results with invalidation on data update | Hephaestus-Backend | 35%+ cache hit rate observed; staleness < 5 min |
| M5b.2 | Gunicorn + 4 uvicorn workers (no single-process serving) | Hephaestus-Backend | `ps -ef` shows 4 workers; load distributed |
| M5b.3 | Async DB driver (`asyncpg`) + async SQLAlchemy sessions | Hephaestus-Backend | No event-loop blocking; `--lifespan auto` clean |
| M5b.4 | Qdrant persistent named volume | DevOps-Bot | Container restart preserves vectors |
| M5b.5 | LLM mesh timeout + future cancellation | Hephaestus-Backend | 45s budget, cancellation tested |
| M5b.6 | Frontend bundle < 500KB gz; lazy chunks for `/app/graph` and `/app/audit` | Vulcan-Perf | webpack-bundle-analyzer report |
| M5b.7 | Load test: 100 concurrent users, P95 < 2s for login + query | Cassandra-QA | Locust CSV proves it on real PG with seeded data |

### WEEK 3–4 — OBSERVABILITY + CI/CD + LAUNCH

**M6 — Monitoring (your agents' M6)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M6.1 | Structured JSON logs to ELK or Grafana Loki | DevOps-Bot | Centralized; indexed; queryable |
| M6.2 | Prometheus exporters for API, PG, Qdrant, Redis | DevOps-Bot | All metrics scraped at 15s |
| M6.3 | Grafana dashboards (7 templates already exist) wired to Prometheus | DevOps-Bot | All 7 render with live metrics |
| M6.4 | PagerDuty / Slack alerts: 5xx > 1%, latency P99 > 5s, disk > 80%, drift > 0.05 | DevOps-Bot | Test pages succeed |
| M6.5 | Deep `/health` check (DB + Qdrant + LLM mesh + circuit breakers) | Hephaestus-Backend | Returns degraded state with details, not just 200 |
| M6.6 | Langfuse production keys configured | DevOps-Bot + Founder | Real traces recording |
| M6.7 | Vector drift 60s scheduler running in production cron | DevOps-Bot | Logs show every-60s execution; alerts fire on threshold |
| M6.8 | Frontend error reporting (Sentry or self-hosted GlitchTip) | Vulcan-Perf | Uncaught errors surface to ops within 1 minute |

**M7 — CI/CD (your agents' M7)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M7.1 | GitHub Actions: build + test + lint + audit on every PR | DevOps-Bot | Required-checks gate prevents merge |
| M7.2 | Staging environment (`staging.nrg.iitgn.ac.in`) auto-deploys from `develop` | DevOps-Bot | Push to develop → staging in < 10 min |
| M7.3 | Production deploy from `main` with manual approval gate | DevOps-Bot | Two-approver rule; audit-logged |
| M7.4 | One-click rollback to previous version (< 5 min RTO) | DevOps-Bot | Tested in staging |
| M7.5 | Database migrations run in pipeline with rollback script | Hephaestus-Backend | Forward + rollback both tested in staging |
| M7.6 | Release tagging convention: `v0.x.y` and `v1.0.0` (no `-rc-demo`) | Founder | Production-only rule applied |

**M8 — Documentation (your agents' M8)**

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M8.1 | Operations runbook: incident response (DB down, mesh failing, Qdrant corrupt) | DevOps-Bot | 5 named scenarios, each timed and tested |
| M8.2 | API documentation auto-generated (OpenAPI) at `/api/docs` (auth-protected in prod) | Hephaestus-Backend | Spec valid per OpenAPI 3.1; examples per endpoint |
| M8.3 | Deployment guide: provision → deploy → verify | DevOps-Bot | New ops engineer can deploy in 1 day |
| M8.4 | Operator manual: add user, rotate keys, restore backup, scale up | DevOps-Bot | All 4 procedures tested |
| M8.5 | C4 architecture diagrams (context, container, component, code) | Architect-Bot | Rendered as SVG, in `docs/architecture/` |
| M8.6 | DPDP compliance attestation refresh | Security-Sentinel + Founder | IITGN cert re-issued for v1.0 |
| M8.7 | GPG signatures on all 9 handover docs | Security-Sentinel + Founder | All 9 verified by ops |

---

## 4. CROSS-LAYER PRODUCTION HARDENING (additional, not in your agents' M-list)

Items from my prior strategic view that are still real production work. None of these are "demo polish".

| ID | Task | Owner | Why production needs it |
|---|---|---|---|
| X1 | Schema parity diff CI (migration vs `db_struct.sql`) on every commit | Hephaestus-Backend | A drifted column in production = DPDP audit failure |
| X2 | Multi-turn conversation regression test (4 turns, 2 domain switches) | Cassandra-QA | Real users have multi-turn sessions; no production bug allowed |
| X3 | bge-reranker output verified used in `src/skills/rag/skill.py` (not just computed) | Hephaestus-Backend | Reranker compute cost without effect = production waste |
| X4 | Verifier node faithfulness spot-check on hallucinated samples | Hephaestus-Backend | Verifier is the production guarantee against hallucinated claims |
| X5 | Circuit-breaker state Redis-persisted across restart | Hephaestus-Backend | A crash that re-enables a broken provider = production incident |
| X6 | Pre-warm script that hits each LLM provider with a dummy query at deploy time | DevOps-Bot | Prevents cold-start latency hit on first real production query |
| X7 | GOLD/SILVER training pair counts in a dashboard tile | Hephaestus-Backend | Two-brain endgame requires steady pair accumulation; needs production visibility |
| X8 | Data integrity audit: verify every audit event in chain has both API HMAC + DB co-sign | Security-Sentinel | Multi-party attestation must hold for every event, not just sample |

---

## 5. GO / NO-GO LAUNCH CRITERIA (from `PRODUCTION_READINESS_MASTER.md` §"GO/NO-GO" + cross-layer items)

NRG goes live to real users only when **ALL** of these are true:

```
Infrastructure
  ☐ M1.1–M1.7 complete (server, Docker, nginx, TLS, DNS)

Database
  ☐ M2.1–M2.7 complete (PG live, schema parity, RLS at DB layer, backups + restore tested)

Authentication
  ☐ M3.1–M3.6 complete (zero hardcoded creds, IIT GN SSO live, IP allowlist for T2)

Security
  ☐ M4.1–M4.9 complete (OWASP, secrets in Vault, container hardening, RT-01..RT-30 25/25 BLOCKED)

Frontend
  ☐ M5a.1–M5a.15 complete (production UI; no stack traces; AA accessibility; mobile)

Performance
  ☐ M5b.1–M5b.7 complete (Redis, 4 workers, async DB, 100-user load test passed)

Observability
  ☐ M6.1–M6.8 complete (logs, metrics, dashboards, alerts, deep health, Langfuse, drift, Sentry)

CI/CD
  ☐ M7.1–M7.6 complete (PR gates, staging, prod deploy with approval, rollback)

Documentation
  ☐ M8.1–M8.7 complete (runbook, API docs, deployment guide, operator manual, C4, DPDP cert, GPG)

Cross-layer
  ☐ X1–X8 complete

Founder sign-off
  ☐ DPDP audit by IITGN compliance office: PASS
  ☐ Penetration test by external firm: zero critical/high findings
  ☐ On-call rotation established (founder + 1 other)
  ☐ Incident response playbook walked through with the on-call team
  ☐ First 10 real users onboarded in staging without incident for 7 consecutive days
```

If any box is unchecked, NRG does **not** launch. There is no "soft launch" or "beta" workaround. Production means production.

---

## 6. AGENT ASSIGNMENTS (single-source ownership table)

| Agent | Primary milestones | Hours estimate |
|---|---|---|
| **DevOps-Bot** | M1, M2.5–M2.6, M4.8, M5b.4, M6, M7, M8.1–M8.4 | ~80h |
| **Hephaestus-Backend** | M2.1–M2.4, M2.7, M3.2, M3.6, M5b.1–M5b.5, M8.2, X1–X7 | ~60h |
| **Security-Sentinel** | M3.1, M3.3–M3.4, M4.1–M4.7, M8.6–M8.7, X8 | ~40h |
| **Hermes-UI** | M3.5 (admin UI), M5a.4, M5a.6, M5a.9 | ~24h |
| **Apollo-Polish** | M5a.5, M5a.7, M5a.8 | ~24h |
| **Athena-UX** | M5a.10, M5a.11 | ~10h |
| **Iris-A11y** | M5a.12, M5a.13 | ~8h |
| **Vulcan-Perf** | M1.3, M5a.1–M5a.3, M5a.14, M5a.15, M5b.6, M6.8 | ~30h |
| **Cassandra-QA** | M4.4, M4.9, M5b.7, X2 | ~16h |
| **Architect-Bot** | M8.5 | ~6h |
| **Founder (you)** | M1.6 (DNS), M3.2 (SSO contract with IITGN IT), M6.6 (Langfuse keys), M7.6 (release tagging), GO/NO-GO sign-off | ~10h |
| **Total** | | **~308h** |

Roughly 4 calendar weeks at 8 agents in parallel, ~10h/agent/day capacity.

---

## 7. SYSTEM-LEVEL CHANGES SUGGESTED (so this framing-failure doesn't recur)

These are the changes I'm putting in place at the `.claude/` and `.agents/` level so neither I nor any future agent slips back into demo framing.

### 7.1 New permanent rule (DONE)
- **`.claude/rules/production_only.md`** — created. Forbidden vocabulary list. Read first on every session.
- **`.claude/CLAUDE.md`** — updated. Session-start protocol now reads `production_only.md` first.

### 7.2 Pre-commit hook for forbidden vocabulary (DO THIS)

Add to `scripts/forbidden_vocab_check.sh`:

```bash
#!/bin/bash
# Fail any commit whose changed files contain demo-framing vocabulary.
set -e
FORBIDDEN='\b(demo|demo-ready|demo day|demo video|demo dataset|demo rehearsal|pitch deck|MVP|prototype|works on my machine)\b'
if git diff --cached --name-only -z \
  | xargs -0 grep -InE "$FORBIDDEN" 2>/dev/null \
  | grep -v -E '\.(json|lock|svg)$|node_modules/|\.git/|production_only\.md|MASTER_EXECUTION_PLAN' ; then
  echo "❌ Forbidden vocabulary found. NRG is production. See .claude/rules/production_only.md"
  exit 1
fi
```

Wire into `.git/hooks/pre-commit` and `.github/workflows/ci.yml`.

### 7.3 Update agent prompts (DO THIS)

Every agent prompt under `.agents/prompts/` must include this preamble:

> *NRG is a production web application for IIT Gandhinagar and the Government of India. Never frame work as "demo" or "polish for presentation". All work is production hardening. The forbidden vocabulary list at `.claude/rules/production_only.md` is binding.*

### 7.4 BACKLOG.md cleanup

Search and replace any "demo" framing in `BACKLOG.md` with production framing. Audit pass needed — assign to **Athena-UX**, 1 hour.

### 7.5 Self-audit report renaming convention

Self-audit reports are now named `NRG_PRODUCTION_AUDIT_<date>.md`, never `NRG_SELF_AUDIT` or `_v2/v3` versioned.

### 7.6 Tag convention

Releases: `v0.9.0`, `v1.0.0`, `v1.1.0`. Never `-rc-demo`, never `-demo-ready`. Add to `.github/workflows/release.yml`.

### 7.7 Memory file update

Append to `.claude/memory/MEMORY.md`:

```
2026-04-25 — Founder edict — NRG is production-only. No demo framing in any spec, protocol, or response. The .claude/rules/production_only.md rule is permanent and binding. All previously demo-framed planning documents superseded by docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md.
```

---

## 8. WHAT YOU ASK ME GOING FORWARD (production framing)

Same question template, production framing only:

```
CONTEXT: [milestone or task ID, e.g. "M5a.5 streaming response UX"]
GOAL: [production capability being delivered]
QUESTION: [specific, answerable]
CONSTRAINT: [acceptance criteria, time budget, files allowed]
```

I will respond as Guru — strategy, review, blocker resolution. I will not produce `demo*.md`, `pitch*.md`, or `*rehearsal*.md` files. If a draft of mine slips into that vocabulary, I correct it on the spot and reissue.

---

## 9. WHAT I COMMIT TO PROACTIVELY (unchanged from prior, production-framed)

| # | Commitment | Cadence |
|---|---|---|
| 1 | Read every commit you push, produce a 5-line review | Per commit |
| 2 | Daily 9am IST: top-3 production priorities ranked by launch impact | Daily |
| 3 | Per-milestone audit when an M-tier (M1–M8) hits 100% | At milestone close |
| 4 | Pre-launch full audit producing `NRG_PRODUCTION_AUDIT_<date>.md` | Once, before GO/NO-GO |
| 5 | Forbidden-vocabulary check fails → fix instantly + update memory | Continuous |
| 6 | Maintain `BACKLOG.md` as single source of milestone status | Continuous |
| 7 | Architectural risks I see → name them without being asked | Whenever observed |
| 8 | Pre-meeting brief for any external IIT GN / ministry call: state, risks, what to say | When you tell me a meeting is on the calendar |

---

## 10. THE PERMANENT TRUTH

NRG is a production system. It will run on Indian-soil infrastructure under DPDP Act 2023 for the Government of India. Real users will log in. Real PII flows through real RBAC. Real audit chains hold real legal weight. There is no demo. There is no rehearsal. There is no "polish for the professor". There is launch, hardening, monitoring, incident response, and ongoing operation.

Every spec written from this date forward starts from that reality.

— Guru Agent (Claude), 2026-04-25 — Master Execution Plan, Production Launch.
