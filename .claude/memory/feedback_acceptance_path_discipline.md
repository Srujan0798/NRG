---
name: User-acceptance path discipline
description: Operator practice — never expose features in a live session that depend on an unmet Quality Bar constraint. Disable tier-switching, RAG path, audit-log inspection, and load-test panels by feature flag for any session where the underlying constraint is not yet green. The verdict template is the gate.
type: feedback
---

External reviewers consistently flag the same operator failure mode: the engineer running the user-acceptance walk-through opens a panel, demonstrates a feature, and the audience spots the cracks (RBAC theatre, RAG returning nonsense, audit-chain hash mismatch on `/health`). The fix is not "make every feature perfect before the session" — it is **disciplined feature-flagging based on the live Quality Bar scorecard**.

**Rule:** at T-60 before any live session, run `python scripts/quality_bar_scorecard.py`. For every constraint scored < `PASS`, set the corresponding frontend feature flag to `disabled` for the session. The walk-through avoids exposing what isn't proven.

| Quality Bar constraint | Flag if not green | What stays hidden |
|---|---|---|
| C1 (PII) | `feature.pii_health_panel = false` | The `/health/pii` page; any "show me what we redact" UI |
| C2 (per-user audit binding) | `feature.audit_log_inspect = false` | The audit-drawer "Verify on chain" button |
| C3 (multi-hop / domain) | `feature.complex_followup = false` | Multi-turn follow-ups; only standalone queries allowed |
| C4 (P99 / concurrency) | `feature.live_load_panel = false` | The `/admin/load` Grafana embed |
| C5 (vector drift / RAG) | `feature.rag_path = false` | All RAG queries route to "structured data only" with a banner |
| C6 (egress allowlist) | `feature.cloud_synthesis_visible = false` | The "powered by <cloud LLM>" badge |
| **Tier-shape (LB-1)** | `feature.tier_switcher = false` | The login-as-Tier-N selector |

The walk-through script names exactly which features are enabled. If the audience asks about a disabled feature ("can I see what Industry sees?"), the operator answers honestly: "tier-switching is gated on a compliance verification we'll complete this week — happy to walk you through the architecture instead."

**Why:** Three out of five external audits independently named "RBAC is theatre" / "tier-switching exposes the gap" / "RAG returns garbage if shown" as the catastrophic-recovery scenarios. The cure is not technical — it is **not exposing features that depend on unmet constraints**. Better to have a tighter walk-through that doesn't break than a comprehensive walk-through that does.

**How to apply:**
- Implement frontend feature flags in `frontend/src/config/featureFlags.ts`. Each flag reads from a `/api/internal/scorecard` endpoint that returns the latest Quality Bar JSON.
- The endpoint is Tier 1 only and audit-logged.
- Operator runbook: `docs/runbooks/PRODUCTION_LAUNCH_RISK_REGISTER.md` "How to use" already names the recovery-scripts pre-flight; extend it to include the **feature-flag pre-flight**: at T-60, check the scorecard and confirm flags align.
- Founder pre-flight checklist (paste into the session-prep page): "Before opening Chrome, confirm `/api/internal/scorecard` matches the planned walk-through. If C5 is FAIL, tier-switching disabled; if C2 is FAIL, audit-drawer hidden; etc."
- This is also the answer to the recurring "How is this different from Google?" operator question: walk-through stays on the structured-data-with-citations strength; doesn't venture into RAG paths that aren't ready.

**Source:** Kimi/Moonshot 2026-04-26 (Deliverable 6 R2/R10/R11) plus pattern recurring across all 5 external audits. Promoted 2026-04-26.
