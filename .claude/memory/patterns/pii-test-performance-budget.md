# PII Test Performance Budget

## Context

PII tests are security gates. If they take too long, developers skip them and PII regressions can reach production.

## Constraint

Keep the fast Indian PII suite under 10 seconds in the default pytest path. Regex-only unit tests should use the lightweight `scan()` path and compact fixtures. Expensive helper objects such as tokenizers, FPE engines, and Presidio wrappers should be reused at class or fixture scope when test isolation does not require rebuilding them.

## Enforcement

`tests/security/test_pii_indian.py` includes a scan budget test that covers every Indian PII pattern and fails when the scan loop exceeds `PII_TEST_BUDGET_SECONDS` (default 2 seconds). Default pytest still writes `coverage.xml`, but avoids repo-wide terminal coverage tables during targeted runs because that reporting cost can dominate the actual PII checks. Any genuinely model-backed NLP or integration test that cannot stay inside the fast path should be marked `pytest.mark.slow` and kept out of the default unit feedback loop.
