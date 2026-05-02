# NRG Current State — 2026-05-02

## Status

This wrap-up focused on repo hygiene, safe query-helper extraction, and fresh
validation evidence. It did not claim whole-product completion or production
readiness.

## Changes

- Removed 85 untracked `.agents/skills/*` duplicate directories after verifying
  each had a matching `.claude/skills/<name>/SKILL.md`.
- Removed untracked `.codex/` local hook files after verifying
  `.codex/hooks/security_reminder_hook.py` was byte-identical to
  `.claude/hooks/security_reminder_hook.py`.
- Replaced root `AGENTS.md` with a concise execution-agent entry point that
  points future agents to `.agents/AGENTS.md`, source-truth docs, and proof
  requirements.
- Added `.codex/` and `.npm-cache/` to `.gitignore` as local tool/cache
  artifacts.
- Extracted query response utilities from `src/api/main.py` into
  `src/api/query_response_utils.py`.
- Updated `docs/REPOSITORY_STRUCTURE_AND_CLEANUP_PLAN.md` and
  `.claude/CURRENT_STATE.md`.

## Verification

| Check | Result | Evidence |
| --- | --- | --- |
| API/routes compile | PASS | `wrapup_py_compile.log` |
| Diff hygiene | PASS | `wrapup_diff_check.log` |
| Corpus sync | PASS | `wrapup_corpus_sync.log` |
| Forbidden vocabulary guard | PASS | `wrapup_forbidden_vocab.log` |
| Targeted backend/API/security/query tests | PASS after one extraction fix | `wrapup_backend_targeted.log`, `wrapup_backend_targeted_rerun.log` |
| Frontend build | PASS after local dependency install | `wrapup_frontend_build.log`, `wrapup_frontend_npm_install.log`, `wrapup_frontend_npm_install_local_cache.log`, `wrapup_frontend_build_rerun2.log` |
| Frontend dependency audit | PASS local clean audit | `guru_shishya_validation/240_frontend_npm_audit_after_storybook_essentials_removal.json`, `guru_shishya_validation/247_frontend_dependency_full_audit_closure_summary.md` |

## Notes

- First backend test run failed because the extracted helper used printf-style
  logger arguments that `StructuredLogger.debug` does not support. The helper
  was changed back to f-string logging and the same test slice passed.
- First frontend build failed because `frontend/node_modules` was missing. A
  normal `npm install` was blocked by user-level npm cache permissions; rerun
  with a project-local npm cache succeeded.
- Follow-up frontend dependency work closed the local npm audit to 0 total
  vulnerabilities by removing unused Loki, upgrading Storybook/Vite/Jest, and
  removing the unused Storybook essentials/actions chain. Production image audit
  replay is still required before deployed dependency claims.
- The next safe backend split is to reconcile the existing
  `src/api/query_helpers.py` against the live fast-path logic in
  `src/api/main.py`; do not switch query execution to that helper module until
  parity is proven by messy-query, Dhairya, GLM, Minimax, tier, and stream tests.
