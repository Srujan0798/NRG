---
name: hybrid-mvp-fusion
description: Use when building or improving an NRG v1.0 release from internal specs, external product ideas, screenshots, working apps, or agent-generated concepts; external value must be extracted, transformed, and validated against NRG source truth.
---

# Hybrid v1.0 Fusion

Use this skill when an agent is asked to make a v1.0 release, merge external
ideas, inspect a working app, or turn production-module material into the NRG
product path.

Core principle: **there is no restriction on learning from external material;
there are strict gates only on what can be merged directly.** Always extract
the value first, then adapt it to NRG's product, data, tier, and audit truth.

## Required Reading

Read these first, in order:

1. `.claude/CURRENT_STATE.md`
2. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
3. `Core_Idea_Clean.md`
4. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
5. `db_struct.sql`
6. `prompts_hybrid/00_INDEX.md`
7. the task-specific prompt stone

Run this before using `CORPUS/` as a handoff pack:

```bash
python3 scripts/verify_corpus_sync.py
```

## Value Extraction First

Do not start by asking whether the external app can replace NRG. Start by
mining it for reusable value. Useful value can appear as source code, UI
layout, copy, interaction behavior, query examples, test cases, screenshots,
state handling, API ideas, or evidence structure.

External prompt packs and generic application-builder guides are also valid
value sources. Even when their stack, scope, or language does not fit NRG, mine
them for requirement-mapping patterns, recovery loops, UX state coverage,
accessibility checks, chart-selection rules, query-corpus ideas, red-team probe
classes, evidence structures, and agent-operating constraints. The useful
thinking should be transformed into NRG-native instructions, tests, evidence, or
backlog items instead of copied as a new product frame.

For every external app, inspect and summarize:

- login, role/persona, tier, and session flow
- query input behavior, suggestions, shortcuts, validation, and follow-up flow
- streaming/progress states, loading, slow-query, empty, blocked, error, and
  recovery states
- answer layout, citations, source rows, SQL/proof drawer, confidence, copy,
  export, and audit proof
- dashboard cards, charts, tables, filters, mobile layout, and accessibility
- API adapter ideas, response-shape normalization, retry/timeout behavior, and
  error mapping
- query corpus, edge cases, red-team probes, and validation workflow
- copy or phrasing that improves clarity without weakening evidence

Never discard a useful idea just because the original implementation is unsafe.
Convert it into one of these outputs:

- production code inside the existing NRG stack
- focused test or benchmark case
- prompt-stone or skill instruction
- evidence checklist
- handover/workflow note
- backlog item with exact acceptance gate

## External Prompt Conversion Rules

When the source is a normal app-maker prompt, broad validation prompt, UI/UX
guide, or combined old NRG prompt pack, apply these conversions:

- generic stack/scaffold advice -> NRG surface map: data, API,
  orchestration, frontend, auth/tier, audit, evidence, and rollback impact
- generic design guidance -> NRG design-system checks: contrast, focus, touch
  target, responsive overflow, loading skeletons, chart integrity, and readable
  answer/proof layout
- huge-count validation demands -> campaign modes and useful step definitions;
  count only distinct risks, tiers, query classes, states, or workflows
- old NRG prompt packs -> deduplicate against current source-truth files, keep
  stronger acceptance gates, and reject stale paths or stale claims
- API examples -> response-contract or adapter tests only when they preserve
  `audit_event_id`, citations, source rows, tier, timing, and verification

Directly reject external defaults for stack, auth provider, database provider,
query schema, role model, or audit behavior unless a separate migration decision
and rollback plan already exists.

## Fusion Rule

Take only what improves NRG's real product path:

- clearer login/persona/query/answer/proof flow
- stronger answer layout, citations, source rows, SQL/proof drawer, audit ID
- better loading, error, blocked, empty, mobile, and follow-up states
- better API adapter or response contract clarity
- better query-corpus, validation, or evidence structure
- better reviewer-facing interaction patterns from working apps

Reject or isolate anything that weakens NRG:

- landing-page-only bundles
- fake dashboards without query truth
- UI polish that hides bad SQL/RAG answers
- release-only hardcoded answers
- schema guesses that ignore `db_struct.sql`
- query tests that ignore the Dhairya audit
- claims without evidence

## Fusion Decision Matrix

| Decision | Use when | Required output |
| --- | --- | --- |
| Adopt directly | Small UI copy, test query, state label, or interaction is already safe and stack-compatible | Code/test/doc change plus focused verification |
| Adapt into NRG | Idea is useful but source stack, contract, auth, schema, or styling conflicts with NRG | NRG-native implementation using existing files and contracts |
| Convert to tests | Idea is a query, workflow, bug, edge case, or red-team probe | Test, benchmark, validation-campaign row, or evidence checklist |
| Convert to docs | Idea clarifies workflow, handoff, acceptance, or operating instructions | Prompt-stone, skill, handover, or evidence-index update |
| Park as backlog | Idea is valuable but too large for the current session | Exact backlog item with owner, files, acceptance gate, and blocker |
| Reject direct merge | Source would break Core Idea, Dhairya, schema, tier, audit, security, or evidence truth | Explain the rejected direct path and the extracted value, if any |

## Non-Negotiable Gates

A v1.0 change is acceptable only when it preserves:

- `Core_Idea_Clean.md` product direction
- Dhairya SQL audit failure patterns
- `db_struct.sql` schema truth
- tier-safe responses for Researcher, Government, and Industry
- citations/source rows/audit event ID on answer paths
- no PII leak to Tier 3
- fresh evidence for build, tests, screenshots, or API JSON

## Claim Boundary

Keep three statuses separate in every report:

1. `inventory-accounted`: the external source was inventoried, reviewed, and
   every file was accepted, adapted, converted, parked, rejected, or ignored as
   generated/binary/local artifact.
2. `value-integrated`: useful external value was transformed into NRG-native
   code, tests, docs, evidence, workflow rules, or backlog items.
3. `product-proven`: the running NRG product was validated across UI/UX,
   backend/API, data/schema, tier safety, audit proof, accessibility,
   performance, and evidence gates.

Do not collapse these statuses. `inventory-accounted` or `value-integrated`
does not mean the live product is now better in every corner or fully proven.
A whole-product superiority or readiness claim requires a validation campaign
using `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`, with each
covered row marked `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`.

If the founder asks whether NRG is now better than the external bundle across
appearance, UI/UX, database, backend, accessibility, speed, and every other
corner, answer with exact evidence scope:

- fusion status
- product validation status
- unproven gates
- next command or campaign needed

Never answer that question with a blanket yes unless the product-proven matrix
has current evidence for the claimed surfaces.

## Founder Superiority Gate

The founder's intent is not "make a partial merge" or "say the workflow is
better." The intent is: extract every useful part from the external v1.0 app,
convert it into NRG-native value, then prove whether the resulting NRG product
is stronger across every important corner.

When the request includes language like "100% better", "not partial", "best in
every point", "appearance, UI/UX, DB, backend, accessibility, speed, every
corner", or "do not make me repeat this", treat it as this hard gate:

1. Do not reassure.
2. Do not claim superiority.
3. Build or update the fusion matrix.
4. Build or update the product-proof matrix.
5. Run the highest-risk validation slice that can be run locally.
6. Mark every untested surface `UNKNOWN` or `BLOCKED`, never implicitly pass.
7. Save the rule or missing gate back into the workflow so the founder does not
   need to repeat the same correction.

Whole-product superiority requires current evidence across all of these
surfaces:

| Surface | Minimum proof before claiming stronger than the external v1.0 app |
| --- | --- |
| Appearance | desktop and mobile screenshots or browser proof for the changed surface |
| UI/UX flow | login -> role/tier -> query -> answer -> citations/source -> audit proof |
| Query intelligence | messy/noisy, ambiguous, follow-up, out-of-corpus, and killer-query coverage |
| Database/schema | `db_struct.sql`, Dhairya SQL audit, corpus sync, and SQL regression proof |
| Backend/API | stable response contract with audit ID, citations, source rows, tier, timing, verification |
| Retrieval | SQL/RAG/hybrid health, no hidden dependency failure, explainable source evidence |
| Security/tier | PII, injection, tier escalation, small-cohort, and Tier 3 raw JSON proof |
| Audit | HMAC/audit event proof for allowed and blocked attempts |
| Accessibility | keyboard, focus, contrast, labels, touch targets, and mobile overflow checks |
| Performance | local profile plus cluster/deployed proof for production-speed claims |
| Evidence | committed report with commands, outputs, evidence paths, blockers, commit SHA |
| Production | deployed replay, production Qdrant baseline, 1000-user cluster C4, founder signing |

If any row lacks current evidence, the answer must say exactly that. The correct
response is a proof table and next command, not a confidence statement.

## External Bundle Closure Checklist

When the founder gives a working external v1.0 bundle and says to merge it
"fully", "without partial work", or "better in every corner", the agent must
close the bundle with an explicit matrix before making any claim:

- every reviewable source file is accounted for as accepted, adapted,
  converted, parked, rejected, or ignored as generated/binary/local artifact
- all query templates and suggested questions are converted into NRG regression
  tests, validation-campaign rows, or exact backlog items
- all UI/proof ideas are compared against the real NRG login -> tier -> query ->
  answer -> source/citation -> audit flow before any frontend copy is made
- all API/schema/auth/audit defaults from the external stack are rejected unless
  they preserve `db_struct.sql`, Dhairya, tier filtering, citations, source
  rows, and HMAC audit IDs
- the highest-risk failing slice is fixed first, then verified with fresh logs
- the final report separates `inventory-accounted`, `value-integrated`, and
  `product-proven`

Do not say the old bundle has been "fully replaced" unless the repo no longer
depends on it and current NRG tests/evidence prove the corresponding behavior
inside the real product.

## Integration Procedure

1. Read the required source-truth files.
2. Inventory the external material: frontend, backend, data, docs, screenshots,
   tests, scripts, and user-provided notes.
3. Build a value matrix before editing code:
   `source -> useful idea -> decision -> NRG target -> gate`.
4. Merge only through existing NRG boundaries unless an explicit migration
   decision exists.
5. If touching UI, keep the answer-engine path primary: login -> role/tier ->
   query -> verified answer -> citations/source rows -> audit proof.
6. If touching query behavior, read Dhairya audit and `db_struct.sql`; turn
   external query ideas into regression cases before trusting them.
7. If touching backend/auth/schema, prove the NRG contract with raw JSON and
   audit IDs; never let an external simplified backend replace source truth.
8. Save evidence that lists accepted, adapted, converted, parked, and rejected
   items.

## Output Required

Report:

- what external or production-module material was inspected
- what value was accepted directly
- what value was adapted into NRG
- what value was converted to tests/docs/evidence/backlog
- what direct merge was rejected and why
- files changed
- commands/tests run
- evidence paths
- blockers
- commit SHA if committed, otherwise `not committed`
