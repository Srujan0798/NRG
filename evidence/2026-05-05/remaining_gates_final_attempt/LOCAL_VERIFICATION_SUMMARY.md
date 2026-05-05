# Local Verification Summary

Generated: 2026-05-05T13:47:36Z
Status: PARTIAL

## PASS

- `ruby -e 'require "yaml"; ...' .github/workflows/ci.yml .github/workflows/deploy.yml .github/workflows/cd.yml`
  passed.
- `.venv/bin/python -m py_compile scripts/quality_bar_scorecard.py src/api/query_response_utils.py src/api/query_service.py src/api/response_filter.py src/api/routes/health.py src/auth/rbac.py`
  passed.
- `git diff --check` passed.
- `python3 .claude/scripts/nrg-skill-count.py` reported 86 `.claude`
  skills, 50 `.agents` skills, 136 total, and no duplicates.
- `python3 .claude/scripts/nrg-verify-workflow.py` passed all workflow
  checks.
- `bash scripts/check_workflow_links.sh` passed.
- `.venv/bin/python scripts/check_docs_links.py` passed with 146 files and
  29 internal links.
- `bash scripts/forbidden_vocab_check.sh --all` passed.
- Focused response-filter/RBAC suite passed: 66 passed, 13 deselected.
- `tests/api/test_critical_path_stream.py` passed: 4 passed.
- Focused Qdrant health contract suite passed: 5 passed.
- Focused killer-query routing suite passed: 3 passed.
- Focused SLO health slice passed: 3 passed.
- Async audit append queue tests passed: 2 passed.
- Focused Dhairya regression passed: 43 passed in 180.91s
  (`evidence/2026-05-05/dhairya_regression_full/01_full_run.log`).
- Credential history scan evidence reports PASS with zero findings:
  `evidence/2026-05-05/credential_rotation/02_all_refs_scan.json`.

## FAIL

- `scripts/quality_bar_scorecard.json` is 5/6; C4 is FAIL.
- `.venv/bin/python -m pytest tests/performance/test_slo_compliance.py -m 'slow or not slow' -q --tb=short --no-cov`
  failed strict local SLO checks: P95 343ms >300ms and P99 2007ms >500ms.

## BLOCKED

- Docker/Colima runtime is unstable. `docker ps` timed out even after Colima
  reported the VM running.
- `/health/db` briefly responded healthy with zero row counts, then
  `localhost:8000` became unreachable again; `/health/all` timed out.
- Frontend Docker image verification was canceled after Buildx reached
  `npm ci` and stalled.
- `cd frontend && npm run build` did not complete during the verification
  window; `dist/frontend` remained at the earlier 18:03 build.
- External gates remain blocked on deployed URLs, production API/Qdrant target,
  usable `KUBECONFIG`, founder GPG signatures, and credential rotation.
- `evidence/2026-05-05/core_verification/03_dhairya_all.log` is an older broad
  SQL accuracy command that failed when local PostgreSQL refused connections;
  the focused Dhairya regression pass above is the current query-regression
  evidence.
