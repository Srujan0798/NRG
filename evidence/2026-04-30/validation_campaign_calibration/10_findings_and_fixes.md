# Findings And Fixes

- Total recorded steps: 20
- PASS: 20
- FAIL: 0
- Slow checks >= 5000ms: 4
- Critical failures: 0

## HIGH - Slow Non-Fast-Path/RAG Or Health Dependencies
These checks passed functionally but exceeded the calibration latency budget. They should be profiled before larger acceptance campaigns.
- VC-API-004 `best quantum researchers....` elapsed_ms=12469.61 evidence=evidence/2026-04-30/validation_campaign_calibration/raw_json/vc-api-004_researcher.json
- VC-API-010 `which projects are closest to TRL 7 in clean energy` elapsed_ms=10235.32 evidence=evidence/2026-04-30/validation_campaign_calibration/raw_json/vc-api-010_researcher.json
- VC-API-013 `who will win the next cricket world cup` elapsed_ms=376187.73 evidence=evidence/2026-04-30/validation_campaign_calibration/raw_json/vc-api-013_researcher.json
- VC-API-018 `/health` elapsed_ms=37131.3 evidence=evidence/2026-04-30/validation_campaign_calibration/raw_json/vc-api-018_health.json

## Failures

No API assertion failures in the recorded calibration slice.

## Fixes This Campaign

- Fixed the browser login stall by changing the frontend backend availability poll from deep root `/health` to lightweight `/health/db` in `frontend/src/hooks/useAuth.tsx`.
- Rebuilt the frontend after the fix: `npm run build` PASS.
- Retested the live browser proof after the fix: Playwright PASS, 1 test passed in 50.1s.
- The remaining slow-path finding is documented for the next backend performance/retrieval pass.
