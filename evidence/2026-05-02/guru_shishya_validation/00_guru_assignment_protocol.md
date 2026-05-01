# Guru/Shishya Validation Campaign Protocol

Date: 2026-05-02
Mode: acceptance-local
Base commit: 0db43517d47e3d69cb6b2720842b9b1edeaa277c

## Guru Assignment Note

NRG cannot be called stronger, complete, or production-ready from intent alone.
This campaign converts the founder's "use all relevant skills" request into an
evidence matrix across the product surfaces that decide whether the current
checkout is locally acceptable and which gates remain blocked by external
infrastructure.

## Task

Validate the current NRG checkout as both Guru and Shishya without overwriting
existing uncommitted work. Apply only narrow fixes if a fresh local gate exposes
a root-caused failure that can be repaired safely in this session.

## Files

- Read: `.claude/CLAUDE.md`, `.agents/AGENTS.md`, `.claude/CURRENT_STATE.md`
- Read: `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- Read: `Core_Idea_Clean.md`, `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`, `db_struct.sql`
- Read: `prompts_hybrid/00_INDEX.md`, `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- Evidence: `evidence/2026-05-02/guru_shishya_validation/`
- Code changes: none unless a local gate fails and root cause is proven

## Phased Action

### Phase 1 - Fortify

- Lock source truth and git state.
- Inventory external audit files.
- Run corpus sync, backend/API/security/query tests, audit-chain verification,
  and forbidden-vocabulary guard.
- Preserve all logs under the current evidence folder.

### Phase 2 - Elevate

- Run frontend unit/accessibility/build gates.
- Run killer-query or critical query evidence capture if the local stack permits.
- Run live API/UI checks only against a known local backend, never an unknown
  listener.
- Mark unsupported external gates as `BLOCKED`, not pass.

### Phase 3 - Immortalize

- Produce a final validation matrix with `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`
  for each required surface.
- Update `BACKLOG.md` and `.claude/CURRENT_STATE.md` only with durable findings
  from this session.
- If new reusable learning appears, update `.claude/memory/`.

## Skills To Use

- `nrg-validation-campaign` - whole-product proof matrix and evidence shape.
- `hybrid-mvp-fusion` - convert broad/hybrid prompts into NRG-native gates, not direct replacements.
- `writing-plans` - bound the campaign into executable phases before edits.
- `systematic-debugging` - required before any fix after a failed gate.
- `test-suite` - backend and focused regression gates.
- `pre-commit` - quality gate before any commit.
- `audit-check` - HMAC chain integrity proof.
- `performance` - local timing scope and cluster-proof boundary.
- `verification-before-completion` - no completion claim without fresh command output.

## Acceptance Criteria

- [ ] Fresh git state recorded.
- [ ] Corpus mirror sync result recorded.
- [ ] Backend/security/query/audit regression result recorded.
- [ ] Frontend Jest/build/a11y result recorded.
- [ ] Audit chain result recorded.
- [ ] Forbidden vocabulary guard result recorded.
- [ ] Live API/browser result recorded or explicitly blocked with reason.
- [ ] Final proof matrix includes appearance, UI/UX, query intelligence,
      database/schema, Dhairya audit, backend/API, retrieval, security/tier,
      audit, accessibility, performance, evidence, and production.
- [ ] Report says `not committed` unless a verified commit is actually made.

## Agent Instructions

- First read `.agents/AGENTS.md`.
- Then read `.agents/prompts/shishya_universal.md`.
- Read each listed `SKILL.md` before applying it.
- Do not claim NRG is perfect, 100% complete, or production-ready without a
  current evidence row for every claimed surface.
- If one row lacks current proof, mark it `UNKNOWN` or `BLOCKED`.
- Preserve existing uncommitted user or agent changes unless explicitly directed.
