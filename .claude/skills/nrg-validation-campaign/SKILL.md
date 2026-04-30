---
name: nrg-validation-campaign
description: Use when NRG needs broad validation across many queries, tiers, workflows, UI states, security probes, audit proof, evidence indexing, or deployed performance proof.
---

# NRG Validation Campaign

Use this skill when the task is not one focused fix, but a broad confidence
campaign before review, release, handover, or cluster proof.

## Required Source

Read and follow:

- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`
- latest relevant `evidence/2026-04-30/`

## Core Rule

Do not convert broad validation into arbitrary screenshots or inflated step
counts. Declare a campaign mode and coverage matrix, then prove that exact
matrix.

Campaign modes:

- `calibration`: small confidence pass after focused changes
- `acceptance`: reviewer-ready pass across tiers, workflow, security, audit
- `release-candidate`: broad query/workflow/security/UI/performance pass
- `cluster-proof`: deployed 1000-user C4, deployed replay, production RAG/Qdrant

## Current NRG Boundary

Local 100-user C4 passed in
`evidence/2026-04-30/live_c4_local_smoke_after_read_model_final/`.

Production readiness still needs:

- 1000-user sovereign-cluster/deployed C4 proof
- deployed browser replay
- production Qdrant baseline
- founder signing

## Final Report Must Include

- campaign mode and scope
- query corpus and tier matrix
- workflow/security/UI/performance coverage
- commands run
- evidence paths
- CRITICAL/HIGH findings
- fixes and retests
- cluster-blocked or unknown claims
- commit SHA if committed, or `not committed`
