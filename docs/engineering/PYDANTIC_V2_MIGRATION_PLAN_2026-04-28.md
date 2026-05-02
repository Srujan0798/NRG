# Pydantic V2 And Python 3.14 Migration Plan

Date: 2026-04-28
Status: Active guardrail

## Current Decision

NRG runs on the supported production Python lane while keeping a separate
Python 3.14 compatibility lane in CI. Required CI jobs remain pinned below
Python 3.14 until the compatibility lane is clean enough to promote from
allowed-to-fail to required.

The current guardrail is enforced by:

- `.github/workflows/ci.yml` job `python-314-compat`
- `scripts/check_pydantic_migration_guard.py`
- `tests/scripts/test_pydantic_migration_guard.py`
- `.claude/rules/backend.md`

## Guardrails

- New source imports Pydantic directly from `pydantic`, never from
  `pydantic.v1`.
- New schemas use Pydantic V2 APIs such as `model_validator`, `field_validator`,
  `ConfigDict`, `model_dump()`, and `model_validate()` where applicable.
- Required CI jobs must stay below Python 3.14 until promotion is explicitly
  approved.
- The `python-314-compat` job must remain present and `continue-on-error: true`
  while it is exploratory.
- The compatibility job must exercise Python 3.14 or newer and run import plus
  contract smoke tests.

## Current Compatibility Lane

The active CI lane installs NRG with development dependencies, imports the
Pydantic/LangChain/API stack under Python 3.14, and runs pipeline contract
smoke tests:

```bash
python -W default -c "import pydantic; import langchain_core; import src.api.main"
pytest tests/contract/test_pipeline_contracts.py -q --no-cov
```

Local guard command:

```bash
.venv/bin/python scripts/check_pydantic_migration_guard.py --json
```

Expected local guard state:

- `ok: true`
- `direct_pydantic_v1_imports: []`
- `workflow: .github/workflows/ci.yml`
- `migration_doc: docs/engineering/PYDANTIC_V2_MIGRATION_PLAN_2026-04-28.md`

## Promotion Criteria

Promote the compatibility lane from allowed-to-fail to required only after all
of these are true in CI:

- Python 3.14 import smoke has no deprecation warnings that affect NRG-owned
  code.
- Pipeline contract tests pass under Python 3.14.
- Full backend tests that do not require external services pass under Python
  3.14.
- No source file imports `pydantic.v1`.
- Dependency pins are reviewed for Python 3.14 support.
- The promotion change updates this plan, `.claude/rules/backend.md`, and
  `docs/specs/SPRINT_PHASE2_2026-04-28.md`.

## Rollback

If Python 3.14 compatibility causes CI instability before promotion, keep
required jobs pinned to the production Python lane and leave
`python-314-compat` as allowed-to-fail. Do not remove the guard script or this
plan; update this file with the failing dependency or warning class and the
owner for follow-up.
