# Batch 3 Security And Compliance Evidence

Date: 2026-05-02

## Status Matrix

| Task | Status | Evidence |
| --- | --- | --- |
| S3-01 frontend npm audit | PASS | `S3-01_npm_audit_full.log`: `found 0 vulnerabilities` |
| S3-02 Indian PII coverage | PASS | `S3-02_08_10_11_security_tests.log`: PII suite included Aadhaar, PAN, phone, email, bank account, passport, GSTIN |
| S3-03 500 audit event ID | PASS | `S3-03_500_audit_event.log`: forced 500 returned non-`audit_unavailable` audit event ID |
| S3-04 Tier 3 admin RBAC | PASS | `S3-04_admin_rbac_tests_rerun.log`: 27 admin/RBAC tests passed; Tier 3 blocked from six admin/metrics routes |
| S3-05 SQL injection | PASS | `S3-05_sql_injection_tests.log`: 41 SQL injection/query security tests passed; `S3-05_10_adversarial_inputs.log`: 38 adversarial tests passed |
| S3-06 JWT rotation grace | PASS | `S3-06_jwt_rotation_tests.log`: 4 JWT refresh/rotation tests passed, including 300s grace for in-flight access token |
| S3-07 revoked consent export | PASS | `S3-07_dpdp_revoked_export_attempt2.log`: revoked `research_access` returns 403 for export endpoints |
| S3-08 HMAC compare timing | PASS | `S3-08_hmac_validation_rerun.log`: 11 HMAC/request signer tests passed; malformed signatures compare with fixed-length candidate |
| S3-09 committed `.env*` secrets | FAIL local history | Current tracked `.env*`: none; `.gitignore` covers `.env*` targets. History scan found 11,109 redacted secret-like assignments in deleted env files. Requires history purge plus credential rotation outside this code batch. |
| S3-10 XSS vectors | PASS | `S3-02_08_10_11_security_tests.log` and `S3-05_10_adversarial_inputs.log`: script tag, `javascript:`, SVG/onload, iframe URI vectors blocked |
| S3-11 egress allowlist | PASS | `S3-11_egress_allowlist_baseline.log` and `S3-02_08_10_11_security_tests.log`: 35 egress allowlist tests passed |

## Additional Checks

- `changed_python_py_compile_rerun.log`: all currently modified Python files compile.
- `git_diff_check.log`: no diff whitespace errors.
- `audit_chain_verify.log`: `(True, [], 288128)`.
- `audit_investigate.log`: audit chain investigation OK with 288,128 events checked.

## Final Check Rerun

- `finalcheck_S3-01_npm_audit_high.log`: `found 0 vulnerabilities`.
- `finalcheck_batch3_targeted_pytest.log`: 334 passed, 22 deselected, 118 warnings across the targeted Batch 3 security slice.
- `finalcheck_S3-07_revoked_export_slow.log`: 1 passed for revoked consent blocking `/me/data` and `/dpdp/export`.
- `finalcheck_S3-09_scanner_tests.log`: 3 passed for the redacted env-history scanner.
- `finalcheck_S3-09_env_history_secret_scan.log`: scanner exited 1 with 286 redacted secret-like assignments across 41 runtime env file versions.
- `finalcheck_S3-09_env_history_secret_scan.json`: full redacted scanner output; no secret values are printed.
- `finalcheck_python_compileall.log`: `src` and `tests` compile successfully.
- `finalcheck_git_diff_check.log`: no diff whitespace errors.
- `finalcheck_forbidden_vocab.log`: production-vocabulary gate exited 0.
- `finalcheck_git_diff_check_after_docs.log`: no diff whitespace errors after evidence/runbook updates.
- `finalcheck_forbidden_vocab_after_readme.log`: production-vocabulary gate exited 0 after README update.
- `finalcheck_git_diff_check_final.log`: final diff whitespace check exited 0.
- `finalcheck_S3-09_env_history.log`: deleted runtime `.env*` files remain visible in Git history.
- `finalcheck2_S3-01_npm_audit_high.log`: `found 0 vulnerabilities` after scanner/runbook updates.
- `finalcheck2_batch3_targeted_pytest.log`: 337 passed, 118 warnings across the targeted Batch 3 security slice plus scanner tests.
- `finalcheck2_S3-07_revoked_export_slow.log`: 1 passed for revoked consent blocking export endpoints.
- `finalcheck2_python_compileall.log`: `scripts`, `src`, and `tests` compile successfully.
- `finalcheck2_forbidden_vocab.log`: production-vocabulary gate exited 0.
- `finalcheck2_git_diff_check.log`: no diff whitespace errors.

## Known Gaps

- S3-09 cannot be closed by normal source edits. The repository history still contains redacted secret-like `.env*` values. Treat all matching historical credentials as exposed until rotated, and clean history with an approved secret-removal procedure.
- S3-09 remediation runbook: `docs/security/ENV_HISTORY_SECRET_REMEDIATION_2026-05-02.md`.
- Deployed/cluster egress and dependency claims were not made; this is local checkout evidence only.
