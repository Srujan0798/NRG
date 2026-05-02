# Final Verification After Isolated Rerun Evidence Capture

Date: 2026-05-02

## Commands Run

| Check | Command | Result |
| --- | --- | --- |
| Compile | `python3 -m py_compile scripts/quality_bar_scorecard.py tests/load/locustfile_c4.py` | PASS, exit 0 |
| Scorecard contracts | `.venv/bin/python -m pytest tests/scripts/test_quality_bar_scorecard.py tests/config/test_locustfile_contract.py -q -o addopts= --tb=short` | PASS, 17 passed |
| Corpus sync | `python3 scripts/verify_corpus_sync.py` | PASS, JSON returned `"ok": true` |
| Forbidden vocabulary | `bash scripts/forbidden_vocab_check.sh` | PASS, exit 0 |
| Cached diff whitespace | `git diff --cached --check` | PASS after trimming generated Locust HTML trailing whitespace |
| Port cleanup | `lsof -nP -iTCP:8000 -sTCP:LISTEN` | PASS after stopping leftover local API workers from the load run |

## Corrections Made During Verification

The first cached diff check reported trailing whitespace in `150_locust_report_60s_4workers_uvloop_httptools_isolated_rerun.html`. The generated HTML was mechanically trimmed and the cached diff check was rerun successfully.

The first port check found leftover local API workers listening on `127.0.0.1:8000` from the C4 rerun. Those workers were stopped and the port check was rerun with no listener output.

An additional isolated 8-worker prewarm artifact appeared during cleanup. It was reviewed and retained as negative evidence because it failed with 465 connection/reset failures out of 624 requests.

## Final Status

The evidence capture is clean to commit. C4 is still failed because the measured aggregate P99 is 1100 ms against the 500 ms target.
