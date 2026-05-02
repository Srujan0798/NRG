# Env History Secret Remediation Runbook

Date: 2026-05-02
Last updated: 2026-05-03

## Current Status

S3-09 is `PASS` in the local rewritten clone and remains `BLOCKED` for remote
closure until repository-owner force-push coordination and credential rotation
are completed.

Latest local evidence shows:

- Local rewritten-history scanner: `PASS`, 0 findings.
- Evidence:
  `evidence/2026-05-03/s3_09_local_history_purge/36_s3_09_env_history_secret_scan_final.json`.
- Commit containing the latest local evidence:
  `8335d68 evidence: close local s3 and batch4 verification`.
- Latest state sync:
  `evidence/2026-05-03/final_state_sync_after_8335d68.md`.

Earlier pre-rewrite evidence showed:

- No currently tracked `.env*` files.
- `.gitignore` covers `.env`, `.env.dev`, `.env.local`, `.env.prod`, and `.env.staging`.
- `git log --all --full-history -- .env*` still finds deleted environment files in history.
- The redacted history scan found 11,109 secret-like assignments.

Earlier evidence is under `evidence/2026-05-02/batch3_security_compliance/`.

The scanner output now includes a redacted `remediation` block with:

- affected runtime environment-file paths;
- affected key names;
- unique secret fingerprint count;
- credential classes that must be rotated;
- `git filter-repo` path arguments;
- required closure actions.

## Use This Runbook When

Use this when closing S3-09 for a shared repository or any remote that has
received the old commits. This requires repository-owner approval because it
rewrites Git history and requires credential rotation outside the source tree.

Do not run a normal push or force-push from an agent session. The current local
clone is ahead of `nrg/main` after the rewrite, but remote closure is an owner
operation because it affects every contributor, CI runner, fork, and cached ref.

## Required Access

- Repository admin access for protected-branch changes and force-push.
- Access to rotate database, cache, JWT, audit-chain, third-party telemetry, and external API credentials.
- Ability to notify every contributor and CI runner owner to re-clone after history rewrite.

## Procedure

1. Confirm the local source state to be promoted.
   ```bash
   git log -1 --oneline
   git status --short --branch --untracked-files=all
   python3 scripts/scan_env_history_secrets.py \
     --json-output evidence/$(date +%F)/s3_09_remote_closure_preflight.json
   ```
   Expected local scan result before remote promotion: `PASS` with
   `finding_count: 0`.

2. Freeze writes to the repository.
   - Pause merges.
   - Disable branch automation that may push stale refs.
   - Notify contributors that old clones must not push until the rewrite is complete.

3. Preserve a private emergency backup.
   - Create a mirror clone outside the working checkout.
   - Store the backup in restricted storage.
   - Do not publish the backup or attach it to issue trackers.

4. Rotate exposed credential classes before unfreezing.
   - Database URLs and passwords.
   - Cache URLs and passwords.
   - JWT signing secrets and refresh-token stores.
   - Audit-chain signing keys.
   - Third-party tracing or observability keys.
   - External model/API provider keys.
   - Any legacy acceptance-user passwords found in the scan.

5. Rewrite history in a fresh mirror clone if the promoted source is not
   already the verified rewritten clone.
   ```bash
   git clone --mirror <repo-url> nrg-history-cleanup.git
   cd nrg-history-cleanup.git
   git filter-repo \
     --path .env \
     --path .env.dev \
     --path .env.local \
     --path .env.prod \
     --path .env.staging \
     --path .env.production \
     --invert-paths
   ```

6. Push rewritten refs after owner approval.
   ```bash
   git push --force-with-lease --all
   git push --force-with-lease --tags
   ```

7. Invalidate stale clones and caches.
   - Require all contributors to re-clone.
   - Rotate or clear CI caches that may contain old refs.
   - Remove stale branch mirrors and forks where policy permits.

8. Verify closure from a fresh clone of the remote.
   ```bash
   git clone <repo-url> nrg-remote-verify
   cd nrg-remote-verify
   git log --all --full-history --name-status -- .env .env.dev .env.local .env.prod .env.staging .env.production
   git log --all --full-history -- .env*
   ```
   Expected result: no committed runtime `.env*` files containing secret material. Keep `.env.example` only if it contains non-secret sample values.

9. Re-run the secret scan in the fresh remote clone.
   ```bash
   python3 scripts/scan_env_history_secrets.py \
     --json-output evidence/<date>/batch3_security_compliance/S3-09_env_history_secret_scan.json
   ```
   - Expected result: 0 secret-like assignments for removed runtime `.env*` history.
   - Confirm the JSON `remediation.status` is `PASS`.
   - If findings remain, use the JSON `remediation.affected_paths`,
     `remediation.rotation_classes`, and `remediation.filter_repo_args` fields
     to update the purge and rotation checklist without exposing secret values.
   - Save the new proof under `evidence/<date>/batch3_security_compliance/`.

## Rollback

History rewrite rollback is a governance decision. If the rewrite blocks critical work, restore from the private mirror backup only after confirming rotated credentials remain revoked and the repository owner accepts the risk.

## Exit Criteria

S3-09 can move from `FAIL` to `PASS` only when all of these are true:

- All exposed credential classes are rotated.
- Remote history no longer contains the removed runtime `.env*` files.
- CI and contributor clones have moved to the rewritten history.
- Fresh evidence shows 0 committed runtime secret assignments.
