# Agent 2: Orchestration Runtime Fix

## Objective
Eliminate /query runtime failures and make LLM failure-safe path truthful.

## Must Fix
- name 'logger' is not defined in src/orchestration/nodes/synthesizer.py
- /query should never return 500 due to provider/key failure

## Scope
- src/orchestration/nodes/synthesizer.py
- src/config/llm_config.py
- src/api/main.py (only if needed)

## Constraints
- no fabricated hardcoded LLM answer fallback
- if provider invalid/unavailable, return safe fallback synthesis, not crash

## Done Criteria
1. direct API /query returns 200 with token
2. missing/invalid LLM config still returns stable fallback response
3. add/adjust tests for failure-safe behavior

## Current State (from CFO Assessment)
- API /query returns 500 with "name 'logger' is not defined"

## Action Required
1. Ensure logger is properly initialized in synthesizer.py
   - Should already be: logger = logging.getLogger(__name__)
2. Check for circular imports or module loading issues
3. Test fallback path when LLM is unavailable:
   - _fallback_synthesis should return truthful message about service unavailability
4. Verify /query endpoint returns 200 even when LLM fails

## Key Files to Modify
- src/orchestration/nodes/synthesizer.py - Ensure logger is imported and used correctly
- src/config/llm_config.py - Ensure fallback client works when primary fails
- src/api/main.py - Ensure error handling returns 200 with fallback response