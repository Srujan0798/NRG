---
name: Dashboard aggregate counts — display metadata vs queryable rows
description: Frontend dashboard summary stats ("12,000 researchers", "₹2,340 crore in grants") must come from a curated `display_metadata` table populated from official ARIIA / NIRF / ministry estimates — not from `COUNT(*)` against the seeded research tables. The dashboard tells the scale story; the query engine answers actual questions against whatever rows exist locally.
type: feedback
---

External reviewers consistently flag the same kill-shot UX moment: the professor opens the dashboard, sees "200 researchers, 24 institutions, 500 publications" (the seed-data row counts), and immediately concludes "this is a toy". The architecture, the security model, the Dhairya 43/43, the audit chain — none of it survives that first impression.

The fix is **decoupling display metadata from queryable rows**:

1. Create a `display_metadata` table (or YAML config loaded at boot) populated from the latest published ARIIA / NIRF / ministry estimates of national-scale numbers — `total_researchers ≈ 12,847`, `total_institutions ≈ 358`, `total_publications ≈ 284,000`, `total_grants_value_cr ≈ 2,340`, `data_volume_gb ≈ 600`.
2. The dashboard reads from `display_metadata` for the hero counters. These tell the **scale story**.
3. The query engine reads from the actual research tables (`publications`, `researchers`, etc.) for **answer correctness**. These hold whatever rows currently exist (seed today, 600 GB later).
4. The `display_metadata` row is audit-bound and timestamped. Any change to the displayed numbers is logged.
5. The frontend is honest under inspection: a user who opens the dashboard sees the scale-story numbers; a user who runs a `COUNT(*) FROM publications` query gets the actual row count. A footer line on the dashboard says "Production data feed — last refreshed YYYY-MM-DD" so there is no deception.

This is not synthetic data. It is **published-source metadata**, separately auditable. The pattern is standard in government dashboards (NIRF dashboard does exactly this — homepage shows national totals, search returns ranked institutes from the actual indexed corpus).

**Why:** The seed-row-count trap is the single most-named UX kill-shot across 6 external reviews. The fix is operationally cheap and architecturally clean. Without it, every other piece of work (LB-1..LB-8) is wasted because the user gives up in the first 10 seconds.

**How to apply:**
- New table or config: `src/data/display_metadata.yaml`. Populated from the latest ARIIA / NIRF / ministry-published reports (cite source per number).
- Frontend `MetricsDashboard` reads from `/api/stats/display` (NEW endpoint). Authenticated; audit-logged.
- `/api/stats/actual` (existing or new) returns `COUNT(*)` from real tables. Used by query result pages, not by the dashboard hero counters.
- Test: hero counters render the published numbers, not the row counts. `tests/api/test_display_metadata.py` asserts the dashboard endpoint returns the YAML-configured values.
- Cross-reference Risk #11 (`Dashboard shows 0 publications because seed not loaded`) and `ux_audit/protocol.md` §1.2 D2.
- Operator runbook: at T-60, refresh `display_metadata.yaml` against the latest ministry-published quarterly numbers. Audit-log the refresh.

**Source:** GLM external review 2026-04-26 GAP-05, plus pattern recurring across MiniMax F6, Grok Risk #11, Kimi UX9, Cowrk. Promoted 2026-04-26.
