# Fusion Claim Boundary

## Context

On 2026-05-01, the founder corrected a workflow failure: external source
fusion was reported too broadly, which made it sound like the entire running
product had been proven better across every surface.

## Constraint

Never treat external inventory accounting or idea integration as whole-product
readiness. Keep these statuses separate:

- `inventory-accounted`
- `value-integrated`
- `product-proven`

## Enforcement

When asked whether NRG is better across appearance, UI/UX, database, backend,
accessibility, speed, tier safety, audit proof, and every corner, answer only
from current validation evidence. If a surface has not been freshly tested,
mark it `UNKNOWN`, `BLOCKED`, or `PARTIAL`.

Use `.claude/skills/hybrid-mvp-fusion/SKILL.md` for external value extraction
and `prompts_hybrid/08_full_coverage_validation_campaign_stone.md` for product
proof.
