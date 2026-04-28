# Pydantic V2 / Python 3.14 Migration Plan

Prepared: 2026-04-28

## Current State

- Runtime target in required CI jobs: Python 3.11.
- Pydantic package: `pydantic==2.13.2`.
- Direct repository imports of `pydantic.v1`: zero.
- Known compatibility risk: transitive `langchain_core` imports can still emit Pydantic V1 compatibility warnings under Python 3.14.

## Direct Import Inventory

Direct `pydantic.v1` imports are blocked by `scripts/check_pydantic_migration_guard.py`.

Current direct V1 import count:

```text
0
```

Current V2 import locations:

- `src/api/main.py`
- `src/orchestration/nodes/planner.py`
- `scripts/start_local_llm.py`
- `tests/contract/test_api_schema.py`

## Guardrails

- Required CI jobs stay pinned below Python 3.14.
- `python-314-compat` runs as an allowed-to-fail compatibility lane.
- Pre-commit and CI run `scripts/check_pydantic_migration_guard.py`.
- New code must import from `pydantic`, not `pydantic.v1`.

## Migration Branch Procedure

Create the migration branch from a clean `main` after the current local protocol changes are committed:

```bash
git checkout main
git pull --ff-only
git checkout -b pydantic-v2-migration
```

Work items for that branch:

1. Upgrade transitive LangChain packages to versions that do not rely on Pydantic V1 compatibility paths.
2. Run `python scripts/check_pydantic_migration_guard.py --json`.
3. Run the Python 3.14 compatibility lane locally if Python 3.14 is available:

   ```bash
   python -W error -c "import pydantic; import langchain_core; import src.api.main"
   pytest tests/contract/test_pipeline_contracts.py -q --no-cov
   ```

4. Promote `python-314-compat` from allowed-to-fail to required after the import smoke test and focused contract suite pass without warnings.

## V2 Patterns

- Use `field_validator` and `model_validator`; do not add new `@validator` or `@root_validator` usage.
- Use `ConfigDict` through `model_config`, not nested `class Config`.
- Use `model_dump()` and `model_validate()` rather than `dict()` and `parse_obj()` in new code.
- Keep FastAPI request and response schemas as V2 `BaseModel` classes.
