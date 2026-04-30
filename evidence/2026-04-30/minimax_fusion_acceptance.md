# External Minimax Fusion Acceptance

Date: 2026-04-30

## Governing Skill

The merge followed `.claude/skills/hybrid-mvp-fusion/SKILL.md`.

Required source-truth checks were used before accepting changes:

- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `Core_Idea_Clean.md`
- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `db_struct.sql`
- `prompts_hybrid/00_INDEX.md`
- `prompts_hybrid/02_main_flow_stone.md`
- `prompts_hybrid/04_backend_security_data_stone.md`

## Accepted Idea

Accepted the external bundle's useful pattern of role-aware starter questions, but implemented it inside the existing NRG answer-engine surface instead of replacing any NRG route, backend, schema, authentication, tier logic, or audit path.

The visible result:

- Researcher users see source-level research questions.
- Government users see state, TRL, funding, and policy-level questions.
- Industry users see anonymized capability and partnership questions.
- The primary query box remains unchanged.
- The selected suggestion still submits through the existing NRG query flow.

## Rejected Ideas

Rejected direct backend merge because the external backend used a simplified query stack and did not preserve the NRG source-truth requirements around `db_struct.sql`, Dhairya SQL audit patterns, tier filtering, citations, source rows, and HMAC audit proof.

Rejected direct auth/schema merge because NRG already has the required role, tier, JWT, and audit behavior.

Rejected static dashboard and analytics material because it would weaken the query-first product path and risk showing data not backed by the current answer contract.

Rejected any hardcoded answer, replacement API adapter, or alternate response contract. NRG's current answer path must continue to return query, SQL/source evidence, citations, tier, timing, verification, and audit event ID.

## Files Changed

- `frontend/src/views/AnswerEngine.tsx`
- `frontend/tests/components/AnswerEngineSurface.test.tsx`

## Verification

Command:

```bash
npm test -- --runInBand tests/components/AnswerEngineSurface.test.tsx
```

Result:

```text
PASS tests/components/AnswerEngineSurface.test.tsx
Test Suites: 1 passed, 1 total
Tests: 8 passed, 8 total
```

Command:

```bash
python3 scripts/verify_corpus_sync.py
```

Result:

```text
ok: true
```

Command:

```bash
npm run build
```

Result:

```text
tsc && vite build --emptyOutDir
2636 modules transformed
built in 59.81s
```

## Blockers

No blocker for this selective fusion.

This change does not claim to close the external gates already listed in `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md`, including deployed-environment replay, production Qdrant baseline, 1000-user cluster load proof, and founder signing.
