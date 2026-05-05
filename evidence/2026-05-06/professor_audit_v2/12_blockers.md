# Blockers — Professor Audit v2

## CRITICAL (blocks funding, show, production)

| Blocker | Status | Evidence |
|---------|--------|----------|
| No staging URL | BLOCKED | CURRENT_STATE.md §Deployed URLs all BLOCKED |
| PostgreSQL empty (0 rows in killer-query tables) | BLOCKED | `evidence/2026-05-06/killer_queries_live/00_summary.md` lines 46-52 |
| Bundle size 476KB (exceeds 250KB target) | BLOCKED | `evidence/2026-05-06/bundle_diet_v2/00_summary.md` line 8 |
| No frontend production build output | BLOCKED | `frontend/dist/` does not exist |
| C4 fix unverified (P99 not measured post-fix) | BLOCKED | `evidence/2026-05-06/c4_p99_optimization/00_summary.md` line 33 "TBD after re-run" |
| Zero GPG signatures on audit chain | BLOCKED | `07_gpg_count.log` — 0 signatures |

## HIGH (significant impact)

| Blocker | Status | Evidence |
|---------|--------|----------|
| C5 FAIL (vector drift check timeout) | FAIL | `scripts/quality_bar_scorecard.json` C5 0/1 passed |
| Credential rotation evidence folder empty | UNKNOWN | No evidence at `evidence/2026-05-06/credential_rotation/` |
| No live C4 load test executed | PARTIAL | quality_bar_scorecard.json C4 = "PARTIAL" |

## MEDIUM

| Blocker | Status | Evidence |
|---------|--------|----------|
| Dhairya benchmark only 41% on original audit | Historical | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` — local reg now 43/43 |
| Evidence files not committed to git | PENDING | git status shows untracked files |

---

*All 13 mandatory files read. Audit completed 2026-05-06.*