# Final Verification After ASGI Hot-Path Pass

Date: 2026-05-02

## Commands Run

- `.venv/bin/python -m py_compile src/api/main.py src/api/middleware/security.py src/auth/middleware.py scripts/quality_bar_scorecard.py tests/load/locustfile_c4.py`
  - Result: PASS
- `git diff --check`
  - Result: PASS after removing a trailing blank line in `tests/api/test_request_logging_middleware.py`
- `.venv/bin/python -m pytest tests/auth/test_auth_context_cache.py tests/security/test_prompt_sanitiser_middleware.py tests/api/test_request_logging_middleware.py tests/security/test_security_regression.py::TestSecurityHeaders tests/api/test_query_security_validation.py tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py -q -o addopts= --tb=short`
  - Result: PASS, 39 passed, 1 warning
- `python3 scripts/verify_corpus_sync.py`
  - Result: PASS, source-of-truth mirrors match
- `bash scripts/forbidden_vocab_check.sh`
  - Result: PASS
- `lsof -nP -iTCP:8000 -sTCP:LISTEN || true`
  - Result: no listener after cleanup

## C4 Status

C4 remains a known gap, not a pass. Best stable local evidence from this pass:

- `133_quality_bar_scorecard_60s_asgi_middleware_4workers.json`
- 1000 users
- 47,233 samples
- 0 failures
- aggregate P99 970 ms
- required P99 < 500 ms

The hot-path work improved the local result materially, but the release gate is still open.
