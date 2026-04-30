# Desktop AI Handoff Folder

Date: 2026-04-30

## Output

Created Desktop handoff folder:

```text
/Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30
```

The folder is a compact AI handoff pack. It is not the live source tree. It is
intentionally flat and contains exactly nine Markdown files.

## Included Files

1. `00_README_START_HERE.md`
2. `01_CORE_IDEA_STATE_SOURCE_TRUTH.md`
3. `02_HYBRID_PROMPTS_ALL.md`
4. `03_DHAIRYA_AUDIT_AND_KILLER_QUERIES.md`
5. `04_SCHEMA_AND_CORPUS_ALL.md`
6. `05_AGENT_OPERATING_SYSTEM.md`
7. `06_EVIDENCE_AND_SHOW_READINESS.md`
8. `07_HANDOVER_DOCS_ALL.md`
9. `08_FILE_MANIFEST_AND_HASHES.md`

## Verification

Ran:

```bash
find /Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30 -maxdepth 1 -type f
find /Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30 -maxdepth 1 -type f | wc -l
du -sh /Users/srujansai/Desktop/NRG_AI_HANDOFF_2026-04-30
python3 scripts/verify_corpus_sync.py
```

Result:

- Desktop folder file count: `9`.
- Desktop folder size: `960K`.
- `python3 scripts/verify_corpus_sync.py`: `ok=true`.
- Corpus mirrors match canonical sources for `Core_Idea_Clean.md`, `db_struct.sql`, raw Dhairya SQL audit, killer queries, and schema hint files.

## Handoff Rule

Agents must treat `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` and `CORPUS/killer_queries.yaml` as mandatory verification sources. `CORPUS/` is a mirror for portability; canonical repo paths still win when conflicts exist.
