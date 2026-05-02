# Frontend Runtime Image Dependency Replay

Date: 2026-05-02

## Scope

This replay checks the deployable frontend runtime image after the local
dependency hardening pass. It does not scan the Python API image or the deployed
cluster image.

## Result

| Gate | Status | Evidence |
| --- | --- | --- |
| Colima Docker access | PASS inside VM | `colima ssh -- docker version` returned Docker `29.2.1` |
| Frontend runtime image build | PASS | `248_frontend_runtime_image_build_after_dependency_hardening.log` |
| Frontend runtime image smoke | PASS | `249_frontend_runtime_image_smoke_after_dependency_hardening.log` |

## Notes

- The host Docker socket was not reachable directly, but Colima reported the VM
  running and Docker worked through `colima ssh`.
- The frontend image is an nginx runtime image that serves the already-built
  `dist/frontend` output. It does not install or carry the frontend npm
  dependency tree.
- The smoke run verified nginx processes, port 80 listener, `wget` against
  `http://127.0.0.1/`, nginx version, image name, and non-root `nginx` user.
- `trivy`, `grype`, and `syft` were not installed on this machine, so this pass
  is a build/smoke replay, not a CVE scanner report.

## Follow-Up Verification

- `colima status`: Colima running with Docker runtime on arm64.
- `docker version`: host client present, but host daemon socket not reachable.
- `colima ssh -- docker version`: Docker client/server `29.2.1`.
- `colima ssh -- docker image inspect nrg-frontend:dependency-audit-20260502`:
  image `sha256:ce5a5d7ba3aed25b585dac46a6ae470a8d3190314559a24a21fe0a797e28d75e`,
  `linux/arm64`, user `nginx`.
- `colima ssh -- docker run --rm nrg-frontend:dependency-audit-20260502 ...`:
  `uid=101(nginx)`, nginx `1.25.5`, and `index.html` present.
- `command -v trivy grype syft`: no local scanner binary available.

## Remaining Boundary

The API image and production/deployed images still need their own dependency and
image scan on the release machine or cluster environment.
