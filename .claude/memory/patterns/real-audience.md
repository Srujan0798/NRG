---
name: Real audience for v1.0 showing
description: The first user-acceptance audience is the IIT-GN professor's assistant clicking through the product on a laptop — not a formal UAT panel, not a ministry session, not a DPDP audit committee
type: feedback
---

The professor's assistant is the audience for the v1.0 showing. One person, one session, one laptop. That is it.

**Why:** Founder edict 2026-04-26. NRG is still production software (the production_only.md rule stands), but the formal trappings — UAT scripts, ministry liaison meetings, DPDP appointment scheduling, signed acceptance reports — are not the path. The product itself is the artifact. The assistant either gets it in 3 minutes or doesn't.

**How to apply:**
- When the founder asks "what's next" and agents are mid-sprint, do NOT default to UAT scheduling, vendor decision ADRs, or compliance appointment drafting. Those exist as long-term tracks but are not what to push the founder toward.
- Real next-tracks while agents work:
  1. Run the stack locally end-to-end and rehearse the click-through (`/deploy-local`).
  2. Sharpen the first 3 minutes of the assistant's flow — login → 1 killer query → see something they cannot get elsewhere.
  3. Do nothing — founder rest is valid output.
- The 3 KILLER queries from `tests/benchmarks/killer_queries.yaml` ARE the showing. If LB-3 evidence shows them working end-to-end with citations, the showing is technically ready. Everything past that is polish.
- Drop "schedule UAT sessions T1/T2/T3" framing unless the founder explicitly asks.
- Cluster deploy, vendor selection, DPDP audit, ministry meetings remain in the long-term backlog (master plan M1, GO/NO-GO gate) but are NOT recommended as parallel founder work right now.

**Source:** Founder direct correction 2026-04-26 — promoted to permanent rule.
