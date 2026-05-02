# API Endpoint Matrix Closure

Date: 2026-05-03

## Scope

Closed the local H7-07 documentation gap by adding a machine-checked endpoint
inventory.

Changed surfaces:

- `docs/specs/API_ENDPOINT_MATRIX.md`
- `tests/api/test_api_endpoint_matrix.py`

Related same-pass surfaces checked with the combined guard:

- `scripts/scan_env_history_secrets.py`
- `tests/scripts/test_scan_env_history_secrets.py`

## Behavior

- Documents all project `APIRoute` method/path pairs except framework docs
  routes: `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, and `/redoc`.
- Records owner module, access guard, and route purpose for 59 registered route
  operations.
- Adds a regression that compares the matrix table to `src.api.main.app`.

## Evidence

| Check | Result | File |
|---|---:|---|
| Registered route inventory | RECORDED, 59 operations | `01_registered_route_inventory.txt` |
| Matrix test py_compile | PASS | `02_py_compile.txt` |
| Matrix test Ruff | PASS | `03_ruff.txt` |
| Matrix plus route registration pytest | PASS, 4 tests | `04_matrix_and_route_registration_pytest.txt` |
| Corpus sync | PASS | `05_corpus_sync.txt` |
| Forbidden-vocabulary guard | PASS | `06_forbidden_vocab_check.txt` |
| Git diff whitespace guard | PASS | `07_git_diff_check.txt` |
| Audit chain verification | PASS, valid chain with 308110 events | `08_audit_chain_verify.txt` |
| Endpoint/S3/route combined pytest | PASS, 10 tests | `09_combined_endpoint_s3_route_pytest.txt` |
| Combined Ruff | PASS | `10_ruff_combined.txt` |
| Final targeted pytest after doc edits | PASS, 10 tests | `11_final_targeted_pytest.txt` |
| Final Ruff after doc edits | PASS | `12_final_ruff.txt` |
| Final corpus sync | PASS | `13_final_corpus_sync.txt` |
| Final forbidden-vocabulary guard | PASS | `14_final_forbidden_vocab_check.txt` |
| Final git diff whitespace guard | PASS | `15_final_git_diff_check.txt` |
| Post-README forbidden-vocabulary guard | PASS | `16_post_readme_forbidden_vocab_check.txt` |
| Post-README git diff whitespace guard | PASS | `17_post_readme_git_diff_check.txt` |
| Git status before commit | RECORDED | `18_git_status_before_commit.txt` |
| Final forbidden-vocabulary guard after S3 README update | PASS | `19_final_forbidden_after_s3_readme.txt` |
| Final git diff whitespace guard after S3 README update | PASS | `20_final_diff_after_s3_readme.txt` |
| Final git status before commit | RECORDED | `21_final_status_before_commit.txt` |

## Boundary

This closes the local endpoint-inventory gap. It does not change route behavior
or close deployed API/UAT/cluster gates.
