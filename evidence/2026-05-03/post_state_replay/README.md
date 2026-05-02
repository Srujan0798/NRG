# Post-State Replay Evidence

Date: 2026-05-03

## Scope

This folder preserves the replay checks and cleanup decisions after the May 3
state-sync commits.

## Results

| Check | Result | Evidence |
|---|---:|---|
| Requested frontend build plus Jest command | PASS, build + 32 suites / 107 tests | `00_requested_frontend_build_and_test.txt` |
| Frontend production build | PASS | `01_frontend_build.txt` |
| Frontend Jest suite | PASS, 32 suites / 107 tests | `02_frontend_jest.txt` |
| Batch 5 orchestration and skills replay | PASS, 419 passed / 6 skipped / 35 deselected | `02_batch5_orchestration_skills_pytest.txt` |
| Corpus mirror sync | PASS | `03_corpus_sync.txt` |
| Forbidden vocabulary guard | PASS | `04_forbidden_vocab_check.txt` |
| Current audit chain verification | PASS, valid chain with 308089 events | `05_current_chain_verify.txt` |
| Git diff whitespace check | PASS | `06_git_diff_check.txt` |
| Final git diff whitespace check after doc cleanup | PASS | `08_final_git_diff_check.txt` |
| Final corpus mirror sync after doc cleanup | PASS | `09_final_corpus_sync.txt` |
| Final forbidden-vocabulary guard after doc cleanup | PASS | `10_final_forbidden_vocab_check.txt` |
| Final pre-commit git status capture | RECORDED | `11_final_git_status_before_commit.txt` |
| Final README-inclusive git diff whitespace check | PASS | `12_final_git_diff_check_after_readme.txt` |
| Forbidden vocabulary guard after doc patch | PASS | `08_forbidden_vocab_after_doc_patch.txt` |
| Git diff whitespace check after doc patch | PASS | `09_git_diff_check_after_doc_patch.txt` |
| Git status before replay commit | INFO | `10_git_status_before_commit.txt` |

## Cleanup Decisions

- The partial `01_frontend_build_and_test.txt` command-header artifact was
  replaced by separate complete build and Jest logs.
- The generated root `memory/` tree was not kept. Durable project memory belongs
  under `.claude/memory/`; the useful session facts are already represented by
  current-state files, changelog entries, ADR-007, and this evidence note.
- The ADR created under `docs/specs/adr/` was moved into the canonical
  `docs/adr/` location and rewritten to match the implemented
  `QueryAnswerService` extraction.

## Remaining Known Gaps

- S3-09 remains an operational security finding until historical environment
  secrets are rotated and the approved history-remediation path is chosen.
- Deployed frontend/API URLs, production Qdrant/API target, explicit cluster
  load context, and founder detached signatures remain external gates.
