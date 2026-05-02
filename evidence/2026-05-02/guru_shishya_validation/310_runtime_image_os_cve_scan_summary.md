# Runtime Image OS CVE Scan Summary

Date: 2026-05-02

Scanner: Trivy 0.70.0 via `aquasec/trivy:latest` container against Colima
Docker images.

## Verdict

| Image | Status | Evidence |
| --- | --- | --- |
| Frontend runtime before OS hardening | FAIL | `276_frontend_runtime_image_trivy_scan.json`, `282_frontend_runtime_image_trivy_scan_after_os_base_update_summary.log` |
| Frontend runtime after OS hardening | PASS | `283_frontend_runtime_image_build_after_apk_upgrade.log`, `285_frontend_runtime_image_smoke_after_apk_upgrade.log`, `287_frontend_runtime_image_trivy_scan_after_apk_upgrade.json`, `288_frontend_runtime_image_trivy_scan_after_apk_upgrade_summary.log` |
| Reverse-proxy nginx runtime after OS hardening | PASS | `304_nginx_runtime_image_build_after_os_base_update.log`, `306_nginx_runtime_image_smoke_after_os_base_update.log`, `308_nginx_runtime_image_trivy_scan_after_os_base_update.json`, `309_nginx_runtime_image_trivy_scan_after_os_base_update_summary.log` |
| API runtime before OS hardening | FAIL | `289_api_runtime_image_trivy_scan_after_dependency_audit_fix.json`, `290_api_runtime_image_trivy_scan_after_dependency_audit_fix_summary.log` |
| API runtime after OS hardening, strict Trivy | PARTIAL | `291_api_runtime_image_build_after_multistage_os_hardening.log`, `294_api_runtime_image_smoke_after_multistage_os_hardening.log`, `299_api_runtime_image_trivy_scan_after_multistage_os_hardening.json`, `300_api_runtime_image_trivy_scan_after_multistage_os_hardening_summary.log` |
| API runtime after OS hardening, fixable-only Trivy | PASS | `301_api_runtime_image_trivy_scan_after_multistage_os_hardening_ignore_unfixed.json`, `302_api_runtime_image_trivy_scan_after_multistage_os_hardening_ignore_unfixed_summary.log` |
| Runtime image scan claim gate | PASS with API strict boundary | `scripts/runtime_image_scan_gate.py`, `317_runtime_image_scan_gate_summary.md` |

## Changes Made

- `Dockerfile.frontend` now uses `nginx:1.29-alpine` and runs
  `apk upgrade --no-cache` before serving the built frontend.
- `docker-compose.yml` now builds the reverse proxy from `Dockerfile.nginx`
  instead of running the raw upstream nginx tag.
- `Dockerfile.nginx` patches the nginx reverse-proxy base with
  `apk upgrade --no-cache`.
- `Dockerfile.api` now uses a true multi-stage runtime so build dependencies do
  not ship into the final API image, upgrades global scanner-visible Python
  tooling in the runner, and uses a Python stdlib healthcheck instead of adding
  `curl` to runtime.

## Scan Delta

| Image | Before | After |
| --- | ---: | ---: |
| Frontend runtime strict Trivy | 93 total, 3 critical, 19 high | 0 total |
| Reverse-proxy nginx strict Trivy | raw upstream tag had the same Alpine base risk | 0 total |
| API runtime strict Trivy | 1,399 total, 146 high | 112 total, 7 high |
| API runtime fixable-only Trivy | not recorded | 0 total |

API strict remaining high findings are Debian runtime packages with no fixed
version reported by Trivy:

- `libcap2` / `CVE-2026-4878`
- `libncursesw6`, `libtinfo6`, `ncurses-base`, `ncurses-bin` /
  `CVE-2025-69720`
- `libsystemd0`, `libudev1` / `CVE-2026-29111`

## Remaining Boundary

Frontend and reverse-proxy local runtime OS scans now pass with zero findings.
The API image has no fixable Trivy findings and no Python-package findings, but
strict Trivy still reports 112 Debian findings including 7 high findings with no
fixed version. Treat the API strict OS scan as PARTIAL until an upstream base
image or approved alternate runtime base removes those no-fix findings. Deployed
image scans remain external and must be rerun against the registry/deployment
artifacts.

## Reproducible Gate Command

```bash
python3 scripts/runtime_image_scan_gate.py \
  --frontend-trivy evidence/2026-05-02/guru_shishya_validation/287_frontend_runtime_image_trivy_scan_after_apk_upgrade.json \
  --nginx-trivy evidence/2026-05-02/guru_shishya_validation/308_nginx_runtime_image_trivy_scan_after_os_base_update.json \
  --api-pip-audit evidence/2026-05-02/guru_shishya_validation/295_api_runtime_image_pip_audit_after_multistage_os_hardening.json \
  --api-trivy-strict evidence/2026-05-02/guru_shishya_validation/299_api_runtime_image_trivy_scan_after_multistage_os_hardening.json \
  --api-trivy-fixable evidence/2026-05-02/guru_shishya_validation/301_api_runtime_image_trivy_scan_after_multistage_os_hardening_ignore_unfixed.json \
  --summary-out evidence/2026-05-02/guru_shishya_validation/317_runtime_image_scan_gate_summary.md
```
