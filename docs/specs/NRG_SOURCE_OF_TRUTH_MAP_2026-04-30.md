# NRG Source Of Truth Map

Date: 2026-04-30

This is the first-read source map for broad NRG work. It exists so agents do
not miss official files, confuse mirrors with canonical files, or validate the
project only from screenshots.

## Canonical Hierarchy

### Tier 0 - Operating Truth

1. `.claude/CLAUDE.md`
2. `.agents/AGENTS.md`
3. `.claude/CURRENT_STATE.md`
4. `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
5. `docs/specs/NRG_EXECUTION_FLOW_RULE_HIERARCHY_2026-05-02.md`
6. `prompts_hybrid/00_INDEX.md`
7. `docs/specs/NRG_ETERNAL_MASTER_AGENT_PROMPT.md`

### Tier 1 - Product And Verification Truth

1. `Core_Idea_Clean.md`
2. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
3. `docs/reports/SQL_AUDIT_RAW_dhairya.sql`
4. `db_struct.sql`
5. `docs/compliance/hall-of-shame.md`
6. `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md`
7. latest relevant `evidence/2026-04-30/`

### Tier 2 - Portable Mirror

`CORPUS/` is useful. Keep it. It is a portable mirror for AI handoff, not the
runtime source tree. Verify it before use:

```bash
python3 scripts/verify_corpus_sync.py
```

### Tier 3 - Active Implementation Roots

- `src/api/`
- `src/orchestration/`
- `src/skills/text_to_sql/`
- `src/skills/rag/`
- `src/security/`
- `src/audit/`
- `src/auth/`
- `src/data/`
- `frontend/src/`
- `tests/`
- `scripts/`
- `infrastructure/`

## Mandatory Discovery Commands

Run these before broad v1.0, validation, cleanup, handover, or source-map work:

```bash
git status --short
find . -path './.git' -prune -o -path './node_modules' -prune -o -path './.venv' -prune -o -path './frontend/node_modules' -prune -o -type f -print | sed 's#^./##' | sort > /tmp/nrg_file_inventory.txt
awk -F/ '{print $1}' /tmp/nrg_file_inventory.txt | sort | uniq -c | sort -nr
rg -n "Dhairya|SQL_AUDIT_REPORT_DHAIRYA|db_struct|Core_Idea|CORPUS|source of truth|validation|evidence|v1.0|query correctness|tier|PII|audit" .claude .agents prompts_hybrid docs CORPUS Core_Idea_Clean.md README.md
```

## v1.0-Making Minimum Pack

1. `Core_Idea_Clean.md`
2. `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
3. `docs/reports/SQL_AUDIT_RAW_dhairya.sql`
4. `db_struct.sql`
5. `CORPUS/`
6. `.claude/CURRENT_STATE.md`
7. `.claude/CLAUDE.md`
8. `.agents/AGENTS.md`
9. `prompts_hybrid/00_INDEX.md`
10. `prompts_hybrid/02_main_flow_stone.md`
11. `prompts_hybrid/03_frontend_zero_flaw_stone.md`
12. the hybrid release fusion skill under `.claude/skills/`
13. latest relevant `evidence/2026-04-30/`

## External App Fusion Rule

External apps, screenshots, agent-built bundles, and working examples are useful
input material. They are not canonical source trees. Agents must use
the hybrid release fusion skill under `.claude/skills/` to extract all useful value first,
then adapt only NRG-compatible pieces into the existing source tree.

Accepted external value can become product code, tests, prompt-stone updates,
evidence checklists, or backlog items. Direct replacement is blocked when it
conflicts with Core Idea, Dhairya SQL audit, `db_struct.sql`, tier safety,
citations/source rows, audit event IDs, or evidence gates.

## Query-Correctness Gate

Any task touching query behavior, Text-to-SQL, RAG/SQL hybrid answers,
citations, source rows, confidence, query UI, v1.0 release questions, validation,
or handover proof must read:

- `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md`
- `docs/reports/SQL_AUDIT_RAW_dhairya.sql`
- `db_struct.sql`
- `tests/benchmarks/killer_queries.yaml`

If the agent cannot run the relevant benchmark, the gate is `PENDING`; it must
not be replaced by release-only queries.
