# LB-4 Test Suite Final Green Evidence

Date: 2026-04-26

## Acceptance Criteria

- [x] Fast local gate finishes under 15 minutes and is green.
  Evidence: `evidence/2026-04-26/test_suite_full_final.xml`
  Log: `evidence/2026-04-26/test_suite_full_final.log`
  Result: 1413 passed, 57 skipped, 218 deselected in 38 seconds.

- [x] Slow-marked local gate is green.
  Evidence: `evidence/2026-04-26/test_suite_full_final_slow.xml`
  Log: `evidence/2026-04-26/test_suite_full_final_slow.log`
  Result: 174 passed, 44 skipped, 1470 deselected in 35 seconds.

- [x] Pre-commit slow-marker and vocabulary hooks pass.
  Evidence: terminal run on 2026-04-26.
  Result: production vocabulary gate passed; slow-test marker gate passed.

## Notes

Live browser/API/UAT and volumetric checks are explicitly gated behind
`NRG_RUN_LIVE_E2E=1`. This keeps the laptop gate deterministic while preserving
the ability to run those checks against a live stack.

Full pre-commit did not fully complete because the cached `gitleaks` binary in
`~/.cache/pre-commit` is not runnable on this macOS installation. With the venv
on `PATH`, the Python-backed hooks passed.

Audit chain was rebuilt and verified after tests.
Evidence:
- `evidence/2026-04-26/22_audit_chain_rebuild_post_shutdown.log`
- `evidence/2026-04-26/23_audit_chain_verify_post_shutdown.log`

```
OVERALL READINESS: 8.4 / 10
LAUNCH-READY:      NO — run live E2E with NRG_RUN_LIVE_E2E=1 against the deployed stack; replace the broken local gitleaks binary; capture staging PostgreSQL/Qdrant evidence for live-volume Quality Bar claims
PRODUCTION-READY:  NO — same three items must close first
BIGGEST SINGLE RISK: Live-stack checks are skipped locally unless NRG_RUN_LIVE_E2E=1, traced to evidence/2026-04-26/test_suite_full_final_slow.xml.
WHAT WILL IMPRESS THE USER: The deterministic fast and slow local gates are green and complete in under two minutes combined.
WHAT WILL EMBARRASS THE TEAM: The local pre-commit secret scanner cache is broken outside the repo and still needs repair before a clean hook transcript can be produced.
```
