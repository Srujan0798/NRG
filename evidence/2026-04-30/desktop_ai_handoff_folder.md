# Desktop AI Handoff Folder

Date: 2026-04-30

## Output

Created Desktop handoff folder:

```text
/Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30
```

The folder is a compact AI handoff pack. It is not the live source tree.

## Included Groups

- `01_START_HERE/`: `Core_Idea_Clean.md`, source-truth map, `.claude/CLAUDE.md`, `.claude/CURRENT_STATE.md`.
- `02_PROMPTS/`: consolidated all-prompts file and original `prompts_hybrid/` files.
- `03_CORPUS_AND_AUDIT/`: full `CORPUS/`, official Dhairya report, raw Dhairya SQL audit.
- `04_SCHEMA/`: authoritative `db_struct.sql`.
- `05_EVIDENCE_SUMMARY/`: final evidence index, Dhairya benchmark closure, corpus cleanup note, validation campaign report, and live quantum query recheck summary.

## Verification

Ran:

```bash
find /Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30 -maxdepth 3 -type f
du -sh /Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30
python3 scripts/verify_corpus_sync.py
```

Result:

- Desktop folder size: `892K`.
- `python3 scripts/verify_corpus_sync.py`: `ok=true`.
- Corpus mirrors match canonical sources for `Core_Idea_Clean.md`, `db_struct.sql`, raw Dhairya SQL audit, killer queries, and schema hint files.

## Handoff Rule

Agents must treat `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` and `CORPUS/killer_queries.yaml` as mandatory verification sources. `CORPUS/` is a mirror for portability; canonical repo paths still win when conflicts exist.
