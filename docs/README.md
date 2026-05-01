# NRG Documentation Map

This directory is the documentation source tree for the National Research Graph.
Use this map before moving, deleting, or duplicating docs.

## Canonical Product And Verification Sources

These files are canonical and must not be deleted or replaced by `CORPUS/`
mirrors:

- `../Core_Idea_Clean.md` - product truth, visible UX contract, query behavior,
  tiers, trust model, and roadmap.
- `../db_struct.sql` - authoritative minimum PostgreSQL schema used by the
  Dhairya benchmark and schema-parity checks.
- `reports/SQL_AUDIT_REPORT_DHAIRYA.md` - official formatted Dhairya SQL audit.
- `reports/SQL_AUDIT_RAW_dhairya.sql` - raw Dhairya audit material.
- `specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md` - source hierarchy and handoff
  rules.

`../CORPUS/` is a portable AI handoff mirror. It is useful, but it is not the
runtime source tree.

## Directory Ownership

| Directory | Purpose | Cleanup Rule |
| --- | --- | --- |
| `api/` | API reference assets such as OpenAPI and Postman collections | Keep generated specs only when current; regenerate stale copies |
| `architecture/` | System design, orchestration, RBAC, and operations architecture | Keep canonical design docs here; avoid duplicating handover docs |
| `audits/` | Historical and current audit reports | Keep final reports; archive raw screenshots/videos outside git |
| `benchmarks/` | Benchmark summaries and reports | Keep reports that explain gates or regressions |
| `business/` | Commercial, pricing, buyer, and stakeholder material | Keep separate from engineering acceptance docs |
| `compliance/` | Compliance trackers and Hall of Shame links | Keep security/compliance references here |
| `handover/` | Professor/operator-ready final package | Keep only current release handoff material |
| `operations/` | Production run procedures and activation protocols | Keep operational runbooks and deployment procedures |
| `ops/` | Machine-readable operational outputs used by code | Do not delete; API health reads `data_quality_scorecard.json` here |
| `reports/` | Official analysis and audit reports | Dhairya report and raw SQL audit are canonical here |
| `runbooks/` | Incident and recovery runbooks | Keep action-oriented procedures here |
| `schema/` | Schema explanations and data-model notes | Keep generated schema docs aligned with `db_struct.sql` |
| `security/` | Security posture, red-team, threat model, and perimeter guides | Keep security evidence and policy docs here |
| `specs/` | Product, execution, and feature specs | Keep active specs; archive superseded protocol dumps |
| `uat/` | User acceptance scripts and reports | Keep scenario scripts and final reports |

## Cleanup Policy

1. Link instead of copying. When two docs say the same thing, keep the canonical
   one and replace the duplicate with a pointer or remove it after reference
   search.
2. Keep dated final reports when they close a gate. Move intermediate logs,
   screenshots, and videos to `evidence/` or external artifact storage.
3. Do not move canonical files without updating
   `specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`,
   `scripts/verify_corpus_sync.py`, and every test or script that references
   the path.
4. Do not delete `docs/ops/`; it contains generated operational scorecards used
   by the API health path.
5. Any cleanup PR must run `python3 scripts/verify_corpus_sync.py` before
   claiming the source-truth pack is valid.
