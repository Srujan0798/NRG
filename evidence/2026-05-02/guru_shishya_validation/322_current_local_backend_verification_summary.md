# Current Local Backend Verification Summary

Date: 2026-05-02

This is a local current-tree verification summary. It is not deployed-production
or cluster proof.

## Status

| Surface | Status | Result |
| --- | --- | --- |
| Direct non-live backend suite | PASS | `1846 passed, 55 skipped, 261 deselected, 285 warnings in 108.44s` |
| Multi-hop planner slow slice | PASS | `30 passed` |
| Workflow pipeline slice | PASS | `2 passed` |
| Changed-file Python lint | PASS | Ruff reported `All checks passed!` |
| Python compile check | PASS | `compileall -q src tests scripts` exited 0 |
| Audit chain | PASS | `verify_chain()` returned `(True, [], 298919)` |
| Diff whitespace | PASS | `git diff --check` exited 0 |
| Forbidden vocabulary | PASS | `bash scripts/forbidden_vocab_check.sh --all` exited 0 |
| Corpus mirror sync | PASS | All canonical/mirror pairs matched |

## Commands

- `.venv/bin/python -m pytest tests/ -x --tb=short -q`
- `.venv/bin/python -m pytest tests/orchestration/test_multi_hop_planner.py -m slow -q --tb=short`
- `.venv/bin/python -m pytest tests/orchestration/test_workflow_pipeline.py -q --tb=short`
- `.venv/bin/ruff check $(git diff --name-only -- '*.py') $(git ls-files --others --exclude-standard -- '*.py')`
- `.venv/bin/python -m compileall -q src tests scripts`
- `.venv/bin/python -c "from src.audit import verify_chain; result = verify_chain(); print(result if isinstance(result, tuple) else result)"`
- `git diff --check`
- `bash scripts/forbidden_vocab_check.sh --all`
- `python3 scripts/verify_corpus_sync.py`

## Fixes Covered

- Restored planner `_build_dag` compatibility for older DAG callers.
- Kept single-hop planner fallback out of DAG execution while preserving
  comparison/multi-hop DAG behavior.
- Normalized router LLM classification handling so legacy bare-intent mocks and
  tuple-returning runtime classifiers both work.
- Repaired RAG retriever payload text fallback syntax.
- Removed changed-file lint blockers in ingestion imports, shared SQL-domain
  helpers, and slow planner test import order.

## Remaining Blockers

- Deployed frontend/API browser proof, production Qdrant/Redis replay,
  production data-quality replay, sovereign-cluster C4 replay, founder GPG
  signing, deployed image scans, and API strict no-fix Debian OS CVEs remain
  outside this local proof.
