# CORPUS Source-Of-Truth Cleanup

Date: 2026-04-30

## Decision

Keep `CORPUS/`. It is useful as a portable AI handoff pack, but it must be
treated as a mirror, not as the live canonical source tree.

## What Was Wrong

- `CORPUS/README.md` described the corpus as canonical instead of a mirror.
- `docs/schema/README.md` pointed agents to `CORPUS/` as the authoritative
  schema source.
- Several workflow files referenced the Dhairya audit path, but
  `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` and
  `docs/reports/SQL_AUDIT_RAW_dhairya.sql` were missing from `docs/reports/`.
- The workflow listed `hybrid-mvp-fusion`, but the skill folder did not exist in
  this checkout.

## Fixes

- Restored `docs/reports/SQL_AUDIT_RAW_dhairya.sql` from
  `CORPUS/SQL_AUDIT_RAW_dhairya.sql`.
- Restored `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` by extracting the official
  formatted Dhairya report section from the raw audit file.
- Rewrote `CORPUS/README.md` to define the corpus as a portable mirror and list
  canonical paths.
- Rewrote `docs/schema/README.md` to make `db_struct.sql` the schema source of
  truth and `src/data/schema/` the active Text-to-SQL support location.
- Added `scripts/verify_corpus_sync.py` to verify corpus mirrors against
  canonical files.
- Added `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`.
- Added `.claude/skills/hybrid-mvp-fusion/SKILL.md`.
- Updated `.claude/CLAUDE.md`, `.agents/AGENTS.md`, `.claude/CURRENT_STATE.md`,
  and the relevant prompt stones to require the source map, Dhairya audit,
  `db_struct.sql`, and corpus sync checks for v1.0/query/validation work.

## Verification

Run:

```bash
python3 scripts/verify_corpus_sync.py
```

Expected result:

- `ok: true`
- all mirrored files report `status: match`
- official Dhairya report and raw audit report are present

## Operating Rule Going Forward

For any AI agent building v1.0, fixing query behavior, validating the answer
engine, or doing handover work, the minimum context is:

1. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
2. `Core_Idea_Clean.md`
3. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
4. `db_struct.sql`
5. `CORPUS/` after `python3 scripts/verify_corpus_sync.py`
6. `.claude/CURRENT_STATE.md`
7. `prompts_hybrid/00_INDEX.md`
8. the task-specific prompt stone

Do not delete `CORPUS/`. Keep it synced.
