---
name: nrg-validation-campaign
description: Run broad NRG validation across query quality, UI flows, tiers, security, audit proof, accessibility, performance, and evidence before any readiness or superiority claim.
---

# NRG Validation Campaign

Use this for whole-product validation or external-bundle comparison work.

## Read First

- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `Core_Idea_Clean.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `db_struct.sql`
- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `.claude/skills/hybrid-mvp-fusion/SKILL.md` when external source material is
  involved

## Rule

External source inventory and idea integration are not whole-product proof.
Whole-product claims need a current validation matrix with UI/UX, backend/API,
database/schema, tier safety, audit proof, accessibility, performance, and
evidence rows marked `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`.

Founder correction: if asked whether NRG is "100% better", "not partial",
"best in every point", or stronger than an external v1.0 app in every corner,
do not answer with reassurance. Return a proof matrix covering appearance,
UI/UX, query intelligence, DB/schema, Dhairya SQL audit, backend/API,
retrieval, security/tier, audit, accessibility, performance, evidence, and
deployed production proof. Any row without current evidence is `UNKNOWN` or
`BLOCKED`.

## Output

Return files changed, commands run, evidence paths, blockers, validation status,
and commit SHA if committed.
