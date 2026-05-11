# External Import Ignore Closure

Date: 2026-05-11

## Problem

`python3 .claude/scripts/nrg-verify-workflow.py` failed because untracked
root-level external/import directories were included in the full vocabulary
scan. Those directories are not canonical NRG source roots and contain upstream
language that is blocked for active production files.

## Closure

Verified root-level ignore rules already present in `.gitignore` for:

- `Glm_mvp/`
- `Minimax_mvp/`
- `NRG DB/`
- `NRG_HISTORY_BACKUP_BEFORE_S3_09_PURGE_*.git/`

The external/import directories were not edited, deleted, or imported into the
canonical NRG source tree.

## Verification

| Check | Status | Evidence |
|---|---:|---|
| Git status with normal untracked files | PASS | `git_status_normal.log` |
| Forbidden vocabulary full scan | PASS | `forbidden_vocab_all.log` |
| Workflow validator | PASS | `nrg_verify_workflow.log` |
| Diff whitespace check | PASS | `git_diff_check.log` |
