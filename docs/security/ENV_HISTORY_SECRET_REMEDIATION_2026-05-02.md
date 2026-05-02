# Env History Secret Remediation Runbook

Date: 2026-05-02

## Current Status

S3-09 is `FAIL` for repository history, not for the current checkout.

Local evidence shows:

- No currently tracked `.env*` files.
- `.gitignore` covers `.env`, `.env.dev`, `.env.local`, `.env.prod`, and `.env.staging`.
- `git log --all --full-history -- .env*` still finds deleted environment files in history.
- The redacted history scan found 11,109 secret-like assignments.

Evidence is under `evidence/2026-05-02/batch3_security_compliance/`.

The scanner output now includes a redacted `remediation` block with:

- affected runtime environment-file paths;
- affected key names;
- unique secret fingerprint count;
- credential classes that must be rotated;
- `git filter-repo` path arguments;
- required closure actions.

## Use This Runbook When

Use this when closing S3-09 for a shared repository or any remote that has received the old commits. This requires repository-owner approval because it rewrites Git history and requires credential rotation outside the source tree.

## Required Access

- Repository admin access for protected-branch changes and force-push.
- Access to rotate database, cache, JWT, audit-chain, third-party telemetry, and external API credentials.
- Ability to notify every contributor and CI runner owner to re-clone after history rewrite.

## Procedure

1. Freeze writes to the repository.
   - Pause merges.
   - Disable branch automation that may push stale refs.
   - Notify contributors that old clones must not push until the rewrite is complete.

2. Preserve a private emergency backup.
   - Create a mirror clone outside the working checkout.
   - Store the backup in restricted storage.
   - Do not publish the backup or attach it to issue trackers.

3. Rotate exposed credential classes before unfreezing.
   - Database URLs and passwords.
   - Cache URLs and passwords.
   - JWT signing secrets and refresh-token stores.
   - Audit-chain signing keys.
   - Third-party tracing or observability keys.
   - External model/API provider keys.
   - Any legacy acceptance-user passwords found in the scan.

4. Rewrite history in a fresh mirror clone.
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

5. Push rewritten refs after owner approval.
   ```bash
   git push --force-with-lease --all
   git push --force-with-lease --tags
   ```

6. Invalidate stale clones and caches.
   - Require all contributors to re-clone.
   - Rotate or clear CI caches that may contain old refs.
   - Remove stale branch mirrors and forks where policy permits.

7. Verify closure.
   ```bash
   git log --all --full-history --name-status -- .env .env.dev .env.local .env.prod .env.staging .env.production
   git log --all --full-history -- .env*
   ```
   Expected result: no committed runtime `.env*` files containing secret material. Keep `.env.example` only if it contains non-secret sample values.

8. Re-run the secret scan.
   ```bash
   uv run python scripts/scan_env_history_secrets.py \
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
