# NRG Closure Roadmap

**Date:** 2026-04-25
**Status:** Production-only tracker aligned to `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`
**Authority:** The master execution plan and `docs/task_protocols/PRODUCTION_READINESS_MASTER.md` remain the source of truth.

## Purpose

This file is retained only as a closure index. Earlier framing has been removed because NRG is a production web application for IIT Gandhinagar and Government of India ministries. All remaining work is production hardening, launch verification, operations readiness, or founder-owned institutional coordination.

## Current Local Closure State

Completed locally and evidenced:

| Area | Status | Evidence |
|---|---:|---|
| Launch blockers LB-1 through LB-5 | Complete locally | `evidence/2026-04-26/20_lb4_test_suite_final_green.md`, `evidence/2026-04-26/29_full_skill_closeout_repair.md` |
| Full backend suite | Complete locally | `evidence/2026-04-26/30_remaining_skill_sweep.md` |
| Audit-chain integrity after suite | Complete locally | `evidence/2026-04-26/30_remaining_skill_sweep.md` |
| Skill inventory and applicability sweep | Complete locally | `evidence/2026-04-26/27_all_skills_application_audit.md`, `evidence/2026-04-26/30_remaining_skill_sweep.md` |
| Schema retrieval and join-graph recall repair | Complete locally | commit `cc8b5d3`, tests in `tests/skills/test_schema_retriever.py` and `tests/orchestration/test_join_graph_blindness.py` |

Latest verification snapshot:

```text
1483 passed, 63 skipped, 218 deselected
Audit chain: ok, 442137 events checked, 0 broken indices
```

## Production Closure Tracks

### Track 1: Local Engineering Closure

| ID | Task | Status | Next Gate |
|---|---|---:|---|
| M5a.1 | Duplicate component cleanup | Complete locally | `GraphView.tsx.old` removed — no duplicate basenames under `frontend/src/components/` |
| M5a.2 | Design token audit | Complete locally | Hardcoded RGBA replaced with CSS variables in 5 components |
| M5a.4 | Query entry surface | Complete locally | QueryPhaseProgress with 5s slow-network indicator added to Hero |
| M5a.5 | Streaming response states | Complete locally | Five phases (planning→verified) with skeleton bridging — no blank wait |
| M5a.3 | Self-hosted fonts | Complete locally | SohneDisplay and JetBrainsMono self-hosted in `frontend/public/fonts/` |
| M5a.4 | Query entry surface | Pending | First input ready, templates available, slow-network timing captured |
| M5a.5 | Streaming response states | Pending | Four response phases visible with no blank wait |
| M5a.6 | Persona switcher | Complete locally | Arrow key nav (Home/End/Arrow keys) with roving tabIndex in PersonaToggle |
| M5a.7 | Citation drawer with HMAC proof | Complete locally | Drawer opens quickly and verification returns proof state |
| M5a.8 | Audit panel | Complete locally | Virtualized AuditEventList (react-window) fetching 2000 events; scroll-based loading needed for 400k+ |
| M5a.9 | Three tier dashboards | Complete locally | TierDataNotice component added to all dashboards; backend enforces tier filtering |
| M5a.10 | Empty and error states | Complete locally | No stack traces or raw exception text reach users |
| M5a.11 | Microcopy library and language gate | Complete locally | Production-only language enforced in build and pre-commit |
| M5a.12 | Accessibility AA | Complete locally | axe-core zero violations on all 6 routes; color-contrast warnings remain (not blocking) |
| M5a.13 | Mobile end-to-end | Complete locally | Both 393px tests pass — no horizontal overflow, bottom-sheet persona switcher works |
| M5a.14 | Frontend telemetry | Complete locally | 12 event types tracked; backend now accepts all 12 (added proof.verify_clicked, proof.verified) |
| M5a.15 | Storybook and visual regression | Complete locally | 7 story files defined; visual_regression.yml CI configured; Loki reference images need first storybook build |

### Track 2: Backend, Security, and Data Closure

| ID | Task | Status | Next Gate |
|---|---|---:|---|
| M2.1-M2.7 | PostgreSQL parity, RLS, backup, restore | Blocked on live PostgreSQL environment | Schema parity and restore evidence |
| M3.1-M3.6 | SSO, sessions, account lifecycle | Blocked on institutional identity provider | SSO claim-to-JWT evidence |
| M4.1-M4.9 | Security hardening and red-team replay | Partially complete locally | Live stack replay and external scan |
| M5b.1-M5b.7 | Caching, worker model, async DB, load proof | Partially complete locally | Load report against live PostgreSQL |
| X1-X8 | Cross-layer hardening | Partially complete locally | Per-item evidence under `evidence/<date>/` |

### Track 3: Operations Closure

| ID | Task | Status | Next Gate |
|---|---|---:|---|
| M1.1-M1.7 | Indian-soil infrastructure, DNS, TLS | Blocked on infrastructure access | HTTPS health check and hardened host evidence |
| M6.1-M6.8 | Logs, metrics, dashboards, alerts | Blocked on observability stack | Prometheus/Grafana/alert evidence |
| M7.1-M7.6 | CI/CD, approval, rollback | Partially complete locally | Required checks and rollback proof |
| M8.1-M8.7 | Runbooks, diagrams, compliance, signatures | Partially complete locally | Signed handover and tested procedures |

### Track 4: Founder-Owned Closure

| ID | Task | Status | Owner Gate |
|---|---|---:|---|
| DNS and institutional domain | Pending | IITGN or approved operator access |
| Institutional SSO coordination | Pending | Identity provider agreement |
| DPDP compliance review | Pending | Compliance office review |
| External penetration test | Pending | Zero critical and high findings |
| First production-user onboarding window | Pending | Seven incident-free days in staging |

## Immediate Next Actions

1. Keep `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md` as the only execution plan.
2. Use this file only to track closure state and blocked owner gates.
3. Do not stage unrelated frontend or generated artifacts unless a task explicitly owns them.
4. For the next engineering pass, start with M5a.10 and M5a.11 because they are local, high-signal, and enforce production language plus user-safe error behavior.
5. For the next operations pass, choose the infrastructure target first; M1 blocks the live evidence required by M2, M4, M5b, M6, M7, and M8.

## Go / No-Go

NRG remains launch-ready for local backend/security verification, but not production-ready for real users until the live infrastructure, PostgreSQL, SSO, observability, load, compliance, and external security gates are evidenced.

OVERALL READINESS: 8.4 / 10
LAUNCH-READY:      YES
PRODUCTION-READY:  NO — live infrastructure, institutional SSO, and external security proof must close first
BIGGEST SINGLE RISK: local evidence is strong, but live-stack evidence is still blocked by infrastructure and institutional dependencies
WHAT WILL IMPRESS THE USER: the backend/security/test foundation is green with a verified audit chain
WHAT WILL EMBARRASS THE TEAM: presenting local-only evidence as live production evidence would be inaccurate
