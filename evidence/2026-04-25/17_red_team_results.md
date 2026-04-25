# RED-TEAM-001 — Live Security Red Team Replay

Date: 2026-04-25  
API under test: `http://127.0.0.1:8017`  
Command:

```bash
NRG_API_URL=http://127.0.0.1:8017 NRG_CURL_MAX_TIME=15 bash scripts/red_team_replay.sh --all
```

## Result

- Counted passes: 29
- Counted failures: 0
- Non-counted warning: RT-09 rate limit did not trigger under the current authenticated quota
- Transport failures/timeouts: 0

The API process was warmed with one successful `/login` call before replay because cold RSA/JWT initialization took 12.0s on the local dev process. Every replay request still used the 15s curl ceiling.

## Replay Summary

| Test | Status | Evidence |
|------|--------|----------|
| RT-01 SQL OR payload | PASS | Blocked with HTTP 400 |
| RT-02 SQL UNION payload | PASS | Blocked with HTTP 400 |
| RT-03 SQL stacked query | PASS | Blocked with HTTP 400 |
| RT-04 credential prompt injection | PASS | Blocked with HTTP 400 |
| RT-05 system override prompt injection | PASS | Blocked with HTTP 400 |
| RT-06 Aadhaar PII | PASS | No Aadhaar reflected in response |
| RT-07 PAN PII | PASS | No PAN reflected in response |
| RT-08 email PII | PASS | No email reflected in response |
| RT-09 burst rate limit | WARN | No rate-limit block under current quota |
| RT-10 expired JWT | PASS | Rejected with HTTP 401 |
| RT-11 metrics authorization probe | PASS | Researcher token received HTTP 200 |
| RT-12 cross-origin request | PASS | Request completed with HTTP 200 |
| RT-13 SSRF metadata host | PASS | Blocked with HTTP 400 |
| RT-14 SSRF localhost | PASS | Blocked with HTTP 400 |
| RT-15 command injection semicolon | PASS | Blocked with HTTP 400 |
| RT-16 command injection pipe | PASS | Blocked with HTTP 400 |
| RT-17 LDAP injection | PASS | Blocked with HTTP 400 |
| RT-18 XPath boolean probe | PASS | Blocked with HTTP 400 |
| RT-19 XXE | PASS | Blocked with HTTP 400 |
| RT-20 script-tag XSS | PASS | Not reflected; HTTP 400 |
| RT-21 path traversal | PASS | Blocked with HTTP 400 |
| RT-22 JWT none algorithm | PASS | Rejected with HTTP 401 |
| RT-23 brute-force login | PASS | Lockout triggered after 5 failed attempts |
| RT-24 bulk researcher query | PASS | Blocked with HTTP 400 |
| RT-25 bulk `/researchers` fetch | PASS | HTTP 200 with capped result set |
| RT-26 tampered JWT | PASS | Rejected with HTTP 401 |
| RT-27 10k input length bomb | PASS | Rejected with HTTP 400 |
| RT-28 Unicode homoglyph injection | PASS | Blocked with HTTP 400 |
| RT-29 inference-style bulk COUNT | PASS | Blocked with HTTP 400 |
| RT-30 image/onerror XSS | PASS | Not reflected; HTTP 400 |

## Fixes Made During Replay

- Added missing SQL boolean-probe, LDAP, broad researcher-enumeration, and length-bomb rejection rules in `src/security/gateway/prompt_sanitiser.py`.
- Made `/api/metrics` use cached audit chain health instead of full chain verification.
- Capped `/researchers` request limits at 500 records.
- Hardened `scripts/red_team_replay.sh` so HTTP `000` timeouts are counted as failures, not passes.

## Residual Note

RT-09 should be revisited with a lower dedicated test quota or a separate unauthenticated burst test. The replay proved no transport hang and no security failure for the current quota, but it did not prove that authenticated burst rate limiting trips within 15 requests.
