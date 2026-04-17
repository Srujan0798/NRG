# Agent 4: Frontend Validation

## Objective
Frontend institutional E2E validation through Kong only.

## Scope
- frontend/vite.config.ts
- frontend/src/views/*
- tests/uat/*
- Playwright smoke if present

## Requirements
- use Kong (:8000) for auth/query/data, no direct API bypass
- verify researcher/government/industry flows
- verify DLP block shown as safe UI error

## Done Criteria
1. frontend on :3000 healthy
2. persona login + query + researchers path works
3. DLP blocked query visibly handled
4. UAT and smoke evidence saved in docs/uat/

## Current Status
- Frontend on :3000 was previously working
- Need to verify all persona flows work through Kong

## Action Required
1. Ensure frontend builds successfully
2. Configure vite.config.ts to proxy through Kong (:8000) not direct API (:8001)
3. Test each persona flow:
   - Researcher: can login, query, view publications
   - Government: can login, view national metrics
   - Industry: can login, view technology transfer
4. Verify DLP errors surface to UI (blocked queries show error message)
5. Save UAT evidence to docs/uat/

## Key Files to Modify
- frontend/vite.config.ts - Ensure Kong proxy configured correctly
- frontend/src/views/* - Ensure proper error handling for DLP blocks
- tests/uat/persona_tests.py - Add test for persona flows through Kong