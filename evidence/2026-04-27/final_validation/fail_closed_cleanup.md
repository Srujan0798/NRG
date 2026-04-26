# Fail-Closed Cleanup Evidence — 2026-04-27

## Scope

Production-code hygiene sweep for legacy synthetic outputs and raw PII recovery paths.

## Changes Verified

- `src/orchestration/workflows/multi_hop.py`
  - Removed fabricated multi-hop result output.
  - Removed import-time `multi_hop.log` file creation.
  - Legacy direct execution now raises `RuntimeError` with an actionable migration path to `NRGWorkflow`.
- `src/security/pii/fpe_engine.py`
  - Aadhaar, PAN, and phone decrypt methods now fail closed.
  - No fake `[DECRYPTED_*]` values are returned.
- `src/security/pii/tokenizer.py`
  - Format-preserving token detokenization now requires an approved token-vault process.
  - Runtime recovery for Aadhaar, PAN, and phone tokens raises `NotImplementedError`.
- `src/db/seed.py` and `src/data/schema/schema_hints.md`
  - Removed misleading production-language references to placeholder seeding/support fields.

## Test-First Failure

Command:

```bash
.venv/bin/python -m pytest tests/misc/test_zero_coverage_modules.py::TestMultiHopWorkflow tests/security/test_pii_compliance.py -q
```

Result before implementation:

```text
3 failed, 8 passed
```

Failures proved:

- `MultiHopWorkflow.execute_multi_hop_query` did not raise.
- `MultiHopWorkflow.validate_multi_hop_results` did not raise.
- `FPEEngine.decrypt_*` did not raise.

## Final Passing Evidence

Command:

```bash
.venv/bin/python -m pytest tests/misc/test_zero_coverage_modules.py tests/security/test_pii_compliance.py -q
```

Result:

```text
29 passed in 6.57s
```

Full backend suite after the fail-closed cleanup:

Command:

```bash
.venv/bin/python -m pytest tests/ -q
```

Result:

```text
1581 passed, 63 skipped, 219 deselected in 97.66s
```

## Production-Code Sweep

Command:

```bash
rg -n "TODO|coming soon|lorem|fake data|dummy data|DECRYPTED_|deprecated_stub" \
  src frontend/src docker-compose.yml Dockerfile.api Dockerfile.frontend README.md \
  docs/handover docs/PRODUCTION_READINESS_SUMMARY.md docs/PRODUCTION_WALKTHROUGH.md
```

Remaining hit:

```text
src/skills/text_to_sql/validator.py:140:        r"--\s*TODO",
```

Assessment: this is an intentional validator rule that rejects incomplete generated SQL containing `-- TODO`; it is not a production TODO.

Command:

```bash
rg -n "placeholder" src/security src/orchestration src/db src/api src/skills/text_to_sql/validator.py
```

Remaining hits are legitimate implementation terms:

- PII redaction placeholders in prompt sanitisation/API scrubbing.
- SQL bind placeholders for parameterized queries.
