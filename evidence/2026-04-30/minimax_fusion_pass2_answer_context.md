# Minimax External Fusion Pass 2 - Answer Context

Date: 2026-04-30

## Scope

External source inspected:

- `/Users/srujansai/Desktop/Minimax_mvp/nrg-frontend/src/pages/SearchPage.tsx`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-frontend/src/layouts/DashboardLayout.tsx`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-frontend/src/pages/LoginPage.tsx`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-frontend/src/services/api.ts`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-backend/src/api/main.py`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-backend/src/api/models.py`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-backend/src/skills/text_to_sql/sql_generator.py`
- `/Users/srujansai/Desktop/Minimax_mvp/nrg-backend/src/security/security.py`

## Value Matrix

| Source | Useful idea | Decision | NRG target | Verification gate |
| --- | --- | --- | --- | --- |
| `SearchPage.tsx` | Compact answer context showing process metadata near the answer | Adapt into NRG | `frontend/src/components/StreamingAnswerPanel.tsx` | Component test and frontend build |
| `SearchPage.tsx` | Source proof button and SQL/audit display | Already covered; no direct merge | Existing source and audit drawers | Existing live proof remains source of truth |
| `SearchPage.tsx` | Data preview table | Reject direct merge | None | External table used synthetic/random values and would weaken evidence truth |
| `SearchPage.tsx` | Role-specific starter questions | Already adapted in `312c6f3` | `frontend/src/views/AnswerEngine.tsx` | Existing component test and build |
| `DashboardLayout.tsx` | Sidebar/card visual energy | Park as design input | Future NRG shell polish only | Needs design review before code changes |
| `LoginPage.tsx` | Account picker flow | Reject direct merge | None | Existing NRG login already has persona defaults and avoids external credential copy |
| `api.ts` | Typed response shape and error normalization | Already aligned conceptually | Existing `frontend/src/services/queryService.ts` | No change needed this pass |
| external backend files | Simplified query/security stack | Reject direct merge | None | Conflicts with NRG schema, Dhairya audit, tier policy, and audit chain |
| external backend files | Query/security examples | Convert to future validation input | Future query/security corpus | Not implemented in this pass |

## Accepted Adaptation

Added a compact `Answer context` grid to the verified streaming answer view.
It surfaces values already produced by NRG:

- source rows
- citation count
- synthesis path
- audit binding state

This makes the answer feel more inspectable without hiding or replacing the
existing source-data and audit drawers.

## Files Changed

- `frontend/src/components/StreamingAnswerPanel.tsx`
- `frontend/tests/components/StreamingAnswerPanel.test.tsx`

## Verification

Command:

```bash
npm test -- --runInBand tests/components/StreamingAnswerPanel.test.tsx
```

Result:

```text
PASS tests/components/StreamingAnswerPanel.test.tsx
Test Suites: 1 passed, 1 total
Tests: 1 passed, 1 total
```

Command:

```bash
npm run build
```

Result:

```text
tsc && vite build --emptyOutDir
2636 modules transformed
built in 1m 35s
```

Command:

```bash
npm test -- --runInBand tests/components/StreamingAnswerPanel.test.tsx tests/components/AnswerEngineSurface.test.tsx
```

Result:

```text
PASS tests/components/StreamingAnswerPanel.test.tsx
PASS tests/components/AnswerEngineSurface.test.tsx
Test Suites: 2 passed, 2 total
Tests: 9 passed, 9 total
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
npm test -- --runInBand tests/i18n/no_raw_strings.test.ts
```

Result:

```text
FAILED: baseline i18n source-discipline failures remain across existing files.
The failure list did not include `src/components/StreamingAnswerPanel.tsx`.
```

## Blockers

No blocker for this selective fusion pass.

The broad i18n source-discipline gate remains a separate existing cleanup item.
