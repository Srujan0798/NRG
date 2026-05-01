# Final Local Verification After C4 Runner Fixes

Date: 2026-05-02

This note records the final focused checks after the C4 scorecard/Locust runner
fixes and the consent hot-path cache. It is not a C4 pass certificate.

## Commands

| Command | Result |
| --- | --- |
| `PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py tests/services/test_consent.py tests/services/test_consent_extended.py -q` | PASS: 30 passed in 0.30s |
| `.venv/bin/python -m compileall scripts/quality_bar_scorecard.py tests/load/locustfile_c4.py src/services/consent.py` | PASS: exit 0 |
| `git diff --check` | PASS: exit 0 |
| `python3 scripts/verify_corpus_sync.py` | PASS: `"ok": true`, all canonical/mirror pairs matched |
| `bash scripts/forbidden_vocab_check.sh --all` | PASS: exit 0 |
| `pgrep -af 'quality_bar_scorecard|locust|uvicorn'` | PASS: no leftover scorecard, Locust, or uvicorn process |

## Current Boundary

C4 remains FAIL. The runner now measures the maintained C4 Locust workload with
preissued tokens and strict numeric metric parsing, and the replay storm is fixed.
Fresh local 1000-user runs show zero request failures but P99 remains about
4.5-4.6 seconds, above the configured 500 ms target.
