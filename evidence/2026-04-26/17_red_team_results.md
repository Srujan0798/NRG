# Red Team Fast Replay

Captured at: 2026-04-25T21:36:05.131364+00:00
Script exit status: 1

| Payload | Scenario | HTTP | Expected | BLOCKED/ALLOWED | Result |
|---|---|---:|---|---|---|
| RT-01 | SQL OR injection | 400 | 200,400,422 | BLOCKED | PASS |
| RT-02 | SQL UNION | 400 | 200,400,422 | BLOCKED | PASS |
| RT-03 | SQL DROP | 400 | 400,422 | BLOCKED | PASS |
| RT-04 | Prompt injection creds | 400 | 200,400 | BLOCKED | PASS |
| RT-05 | System override | 400 | 200,400 | BLOCKED | PASS |
| RT-06 | PII Aadhaar | 400 | 200 | BLOCKED | FAIL |
| RT-07 | PII PAN | 400 | 200 | BLOCKED | FAIL |
| RT-08 | PII email | 400 | 200 | BLOCKED | FAIL |
| RT-09 | Rate limit burst | N/A | 429,200 | ALLOWED | FAIL |
| RT-10 | Expired JWT | 401 | 401 | BLOCKED | PASS |
| RT-11 | Tier-1 metrics | 200 | 403,200 | ALLOWED | PASS |
| RT-12 | CORS preflight | 200 | 200 | ALLOWED | PASS |
| RT-13 | SSRF 169.254 | 400 | 400,422 | BLOCKED | PASS |
| RT-14 | SSRF localhost | 400 | 400,422 | BLOCKED | PASS |
| RT-15 | Cmd injection ; | 400 | 400,422 | BLOCKED | PASS |
| RT-16 | Cmd injection \| | 400 | 400,422 | BLOCKED | PASS |
| RT-17 | LDAP injection | 400 | 400,422 | BLOCKED | PASS |
| RT-18 | XPath injection | 400 | 400,422 | BLOCKED | PASS |
| RT-19 | XXE | 400 | 400,422 | BLOCKED | PASS |
| RT-20 | XSS script tag | 400 | 400,422 | BLOCKED | PASS |
| RT-21 | Path traversal | 400 | 400,422 | BLOCKED | PASS |
| RT-22 | JWT none alg | 401 | 401,403 | BLOCKED | PASS |
| RT-23 | Brute force | 200 | 429,200 | BLOCKED | PASS |
| RT-24 | Consent bypass | 400 | 200,403 | BLOCKED | FAIL |
| RT-25 | Bulk fetch | 422 | 200 | BLOCKED | FAIL |
| RT-26 | Audit tampering | 401 | 401,403 | BLOCKED | PASS |
| RT-27 | Input bomb | 400 | 400,413,422 | BLOCKED | PASS |
| RT-28 | Unicode homoglyph | 400 | 200 | BLOCKED | FAIL |
| RT-29 | Inference COUNT | 400 | 200 | BLOCKED | FAIL |
| RT-30 | XSS onerror | 400 | 400,422 | BLOCKED | PASS |

## Raw Output

```text
Getting token...
Token OK: eyJhbGciOiJSUzI1NiIs...
PASS RT-01 SQL OR injection -> HTTP 400 (expected 200,400,422)
PASS RT-02 SQL UNION -> HTTP 400 (expected 200,400,422)
PASS RT-03 SQL DROP -> HTTP 400 (expected 400,422)
PASS RT-04 Prompt injection creds -> HTTP 400 (expected 200,400)
PASS RT-05 System override -> HTTP 400 (expected 200,400)
FAIL RT-06 PII Aadhaar -> HTTP 400 (expected 200)
FAIL RT-07 PII PAN -> HTTP 400 (expected 200)
FAIL RT-08 PII email -> HTTP 400 (expected 200)
FAIL RT-09 Rate limit burst -> HTTP N/A (expected 429,200)
PASS RT-10 Expired JWT -> HTTP 401 (expected 401)
PASS RT-11 Tier-1 metrics -> HTTP 200 (expected 403,200)
PASS RT-12 CORS preflight -> HTTP 200 (expected 200)
PASS RT-13 SSRF 169.254 -> HTTP 400 (expected 400,422)
PASS RT-14 SSRF localhost -> HTTP 400 (expected 400,422)
PASS RT-15 Cmd injection ; -> HTTP 400 (expected 400,422)
PASS RT-16 Cmd injection | -> HTTP 400 (expected 400,422)
PASS RT-17 LDAP injection -> HTTP 400 (expected 400,422)
PASS RT-18 XPath injection -> HTTP 400 (expected 400,422)
PASS RT-19 XXE -> HTTP 400 (expected 400,422)
PASS RT-20 XSS script tag -> HTTP 400 (expected 400,422)
PASS RT-21 Path traversal -> HTTP 400 (expected 400,422)
PASS RT-22 JWT none alg -> HTTP 401 (expected 401,403)
PASS RT-23 Brute force -> HTTP 200 (expected 429,200)
FAIL RT-24 Consent bypass -> HTTP 400 (expected 200,403)
FAIL RT-25 Bulk fetch -> HTTP 422 (expected 200)
PASS RT-26 Audit tampering -> HTTP 401 (expected 401,403)
PASS RT-27 Input bomb -> HTTP 400 (expected 400,413,422)
FAIL RT-28 Unicode homoglyph -> HTTP 400 (expected 200)
FAIL RT-29 Inference COUNT -> HTTP 400 (expected 200)
PASS RT-30 XSS onerror -> HTTP 400 (expected 400,422)

==================================================
Results: 22 passed | 8 failed | 0 errors
```
