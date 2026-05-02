# Runtime Image Scan Gate

| Gate | Status | Detail |
| --- | --- | --- |
| Frontend runtime strict Trivy | PASS | total=0 |
| Reverse-proxy runtime strict Trivy | PASS | total=0 |
| API runtime pip-audit | PASS | dependencies=122, vulnerable_packages=0, vulnerabilities=0 |
| API runtime fixable HIGH/CRITICAL Trivy | PASS | total=0 |
| API runtime strict Trivy boundary | PARTIAL | total=112, critical=0, high=7, fixable_high_critical=0 |

## Claim Boundary

This gate passes only for local package scans, frontend/reverse-proxy strict OS scans, and API fixable HIGH/CRITICAL findings. It does not certify a zero-CVE API OS image when strict Trivy still reports unfixed vendor CVEs.
