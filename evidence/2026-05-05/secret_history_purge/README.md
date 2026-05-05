# Secret History Purge Status

Date: 2026-05-05

## Status

Local history remediation evidence exists, but remote `nrg/main` still requires
operator/founder coordination. The latest remote-history scan evidence records
286 secret-like assignments on the remote history and remains `BLOCKED` until
the approved history rewrite and credential rotation are completed.

## Required Remote Action

1. Preserve and review the current remote refs.
2. Rotate any credential class identified by the scanner before publishing a
   rewritten remote history.
3. Run `scripts/scan_env_history_secrets.py` against the candidate rewritten
   history.
4. Coordinate the approved force-push window with the founder/operator.
5. Re-run remote CI and update the external-gate evidence.

## Boundary

Do not claim remote security closure from local-only evidence. Remote branch
divergence, credential rotation, remote CI, and founder approval are still
external blockers.
