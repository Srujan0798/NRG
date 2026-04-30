# Wave 3 Security, Tier, and Audit Evidence

Date: 2026-04-30

## Scope

Wave 3 verified the local FastAPI/TestClient security path after Wave 1 query-contract hardening and Wave 2 frontend proof flow. This report covers:

- Tier 1, Tier 2, and Tier 3 raw query JSON evidence.
- Blocked prompt injection, direct-contact PII request, tier escalation, and SQL injection attempts.
- HMAC audit-chain verification after fresh query and blocked-query events.
- Regression tests for sanitizer, tier filtering, k-anonymity boundaries, audit chain, and HMAC validation.

This is local TestClient evidence, not live deployed API evidence.

## Code Change

`PromptSanitiserMiddleware` now carries the anomaly audit event ID into blocked `/query` answer envelopes. Before this fix, blocked attempts were audited internally but the user-visible blocked response had `audit_event_id: null`, making the blocked attempt harder to trace from the UI/API response.

The blocked answer contract now remains:

- `route: "blocked"`
- `blocked: true`
- `status: "blocked"`
- `audit_event_id: <hash>`
- `verification.audit_event_id: <same hash>`
- `citations: []`
- `source_data.rows: []`

## Raw Tier Evidence

Saved raw query responses:

- `evidence/2026-04-30/09_tier1_query_response.json`
- `evidence/2026-04-30/10_tier2_query_response.json`
- `evidence/2026-04-30/11_tier3_query_response.json`

Observed tier controls:

- Tier 1 response includes SQL visibility and detailed aggregate rows.
- Tier 2 response keeps government aggregate behavior.
- Tier 3 response removes SQL query visibility, includes restricted-access warning, and keeps institution-level aggregate rows only.

Tier 3 evidence contains no researcher names, emails, phone numbers, or direct personal identifiers in the saved response.

## Blocked Query Evidence

Saved blocked response evidence:

- `evidence/2026-04-30/wave3_blocked_query_responses.json`

Cases verified:

| Case | HTTP | Route | Audit ID |
|------|------|-------|----------|
| prompt_injection | 400 | blocked | `97d9574d17ec2310cb94816066d8040b11d0d62a01938a77d4ee17e3f288f4e9` |
| pii_phone_numbers | 400 | blocked | `fc042e1cfafeddd0d32d8be12fa810a763377950ba493d8f0ef593691c5605a6` |
| tier_escalation | 400 | blocked | `1795774a38c3ba00872d63074f7eef1aede61e48992fe641fab2ca5e7d85ddd5` |
| sql_injection | 400 | blocked | `f9f040cd98c53c41ead5c9a0a3f1534009fd8ec908d009a980a035d1ae6d925b` |

Each blocked response mirrors the same ID in `verification.audit_event_id`.

## Tests Run

```bash
.venv/bin/python -m pytest tests/api/test_query_security_validation.py -q
```

Result:

```text
7 passed in 3.94s
```

```bash
.venv/bin/python -m pytest tests/api/test_query_security_validation.py tests/api/test_tier_response_filtering.py tests/api/test_k_anonymity_response_boundary.py tests/security/test_sanitiser.py tests/security/test_prompt_sanitiser_middleware.py tests/security/test_zero_leakage.py tests/security/test_tier_filtering_properties.py tests/audit/test_audit_singleton_reset.py tests/audit/test_chain_integrity.py tests/security/test_p0_security_regressions.py tests/security/test_prompt_injection.py tests/security/test_sql_injection_blocked.py tests/security/test_hmac_validation.py -q
```

Result:

```text
134 passed, 1 skipped in 4.22s
```

```bash
.venv/bin/python scripts/audit_investigate.py
```

Result:

```json
{
  "ok": true,
  "events_checked": 33662,
  "broken_indices": []
}
```

## Acceptance Status

| Requirement | Status |
|-------------|--------|
| Raw JSON evidence for all 3 tiers | PASS |
| Tier 3 has no PII or small-cohort detail in saved evidence | PASS |
| PII/direct-contact request is blocked | PASS |
| Prompt injection is blocked | PASS |
| SQL injection is blocked | PASS |
| Tier escalation attempt is blocked | PASS |
| Allowed and blocked query attempts have audit event IDs | PASS |
| HMAC audit chain verifies after fresh events | PASS |

## Remaining Blockers

- This is not a live deployed API proof. A running-stack curl/browser replay should be performed before final handover.
- Blocked middleware audit events may use `anonymous` when auth state has not yet been attached before sanitizer rejection. The event remains traceable by audit hash and request metadata, but user binding can be improved later by moving auth claims earlier in middleware order.
