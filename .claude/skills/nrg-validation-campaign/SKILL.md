---
name: nrg-validation-campaign
description: Use when NRG needs broad proof across query quality, tiers, security, UI workflows, audit evidence, and performance; especially before any whole-product readiness or superiority claim.
---

# NRG Validation Campaign

Use this skill when an agent is asked to prove NRG quality across many surfaces,
validate a release candidate, compare an external bundle against NRG, or answer
whether the running product is proven across UI/UX, backend, data, audit,
accessibility, speed, and tier safety.

## Required Reading

Read these first:

1. `.claude/CURRENT_STATE.md`
2. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
3. `Core_Idea_Clean.md`
4. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
5. `db_struct.sql`
6. `prompts_hybrid/00_INDEX.md`
7. `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
8. `prompts_hybrid/06_evidence_acceptance_stone.md`

If external source material is involved, also read
`.claude/skills/hybrid-mvp-fusion/SKILL.md` and the latest external fusion
matrix under `evidence/YYYY-MM-DD/`.

If `CORPUS/` is used, run:

```bash
python3 scripts/verify_corpus_sync.py
```

## Claim Boundary

Do not present external source accounting as product proof.

Separate these statuses:

- `inventory-accounted`: external files were reviewed and classified.
- `value-integrated`: useful ideas were transformed into NRG-native work.
- `product-proven`: the running product passed the declared validation matrix.

A claim that NRG is better across appearance, UI/UX, database, backend,
accessibility, speed, tier safety, audit, and every corner requires current
evidence from the validation campaign stone. Otherwise mark the claim
`UNKNOWN`, `BLOCKED`, or `PARTIAL`, with the exact missing gates.

## Output Required

Report:

- campaign mode and scope
- source-truth files read
- commands run
- evidence paths
- matrix rows passed, failed, blocked, and unknown
- CRITICAL/HIGH findings and fixes
- product validation status
- commit SHA if committed, otherwise `not committed`
