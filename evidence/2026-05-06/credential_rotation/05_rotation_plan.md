# Credential Rotation Plan

**Date:** 2026-05-06
**Scope:** planning only; no credentials were rotated by the agent.

## Secret Inventory

| Class | Active key names observed | Service | Exposure status | Rotate before remote/funding? |
|---|---|---|---|---|
| Database credentials | `DATABASE_URL`, `POSTGRES_PASSWORD` | PostgreSQL | Unknown; treat as live | YES |
| Redis/cache credentials | `REDIS_URL`, `REDIS_PASSWORD` | Redis | Unknown; treat as live | YES |
| JWT signing material | `JWT_SECRET`, `JWT_SECRET_KEY`, `JWT_PRIVATE_KEY_PATH` | API auth | Unknown; treat as live | YES |
| LLM provider keys | `MINIMAX_API_KEY`, `NVIDIA_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AZURE_OPENAI_API_KEY` | External model providers | Unknown; treat as live | YES |
| Observability keys | `LANGFUSE_SECRET_KEY` | Langfuse/telemetry | Unknown; treat as live | YES |
| Seeded user passwords | `RESEARCHER_PASSWORD`, `GOV_PASSWORD`, `INDUSTRY_PASSWORD`, legacy industry password key | Local/staging auth users | Unknown; treat as live | YES |
| Backup/Vault/Kong secret refs | Helm/Kong/Vault template secret refs | Deployment infra | Template references only in this audit | Verify in cluster secret store |

## Live Credential Check

**YES for rotation requirement. UNKNOWN for exact leaked-value match.**

The current rewritten local history scanner reports `0` findings, so this clone cannot compare old secret fingerprints against active secret values. The old history had runtime `.env*` secret-like assignments, and active config includes live credential classes. The conservative security decision is to rotate every active class before declaring the remote safe.

## Rotation Steps Per Service

| Service | Keys | Method | Downtime estimate | Verification |
|---|---|---|---|---|
| PostgreSQL | `DATABASE_URL`, `POSTGRES_PASSWORD` | Create new role/password, update secret manager/env, restart API workers, revoke old role/password | 5-15 min local/staging; production should use rolling restart | `/health/db` green, old password rejected |
| Redis | `REDIS_URL`, `REDIS_PASSWORD` | Set new Redis password/ACL, update API/env, restart Redis clients, revoke old password | 5-10 min | `/health/all` Redis green, old password rejected |
| JWT | `JWT_SECRET`, `JWT_SECRET_KEY`, `JWT_PRIVATE_KEY_PATH` | Generate new RS256 keypair or HMAC secret, update key id, force session/token invalidation | Users must re-login | New login succeeds, old token rejected |
| MiniMax/NVIDIA/Gemini/OpenAI/Anthropic/Azure | provider API keys | Create new provider key in console, update env/secret manager, revoke old key | No downtime if dual-loaded; otherwise API restart | Provider health call succeeds, old key disabled |
| Langfuse/telemetry | `LANGFUSE_SECRET_KEY` | Generate new project secret, update env, restart telemetry client, revoke old secret | No user-facing downtime | New events accepted, old secret rejected |
| Seeded users | `RESEARCHER_PASSWORD`, `GOV_PASSWORD`, `INDUSTRY_PASSWORD`, legacy variants | Generate new high-entropy passwords, update seed/secret manager, invalidate old sessions | Users must re-login | Login succeeds with new passwords only |
| Deployment secrets | Helm/Vault/Kong secret refs | Rotate in cluster secret store, redeploy workloads consuming affected secrets | Rolling restart | `kubectl rollout status`, smoke tests green |

## Verification Steps

1. Fresh clone from remote after owner force-push.
2. Run `python3 scripts/scan_env_history_secrets.py --json-output evidence/<date>/credential_rotation/fresh_clone_scan.json`.
3. Confirm `finding_count: 0`.
4. Confirm active secret values are stored only in approved secret manager or local untracked env files.
5. Confirm old database/Redis/provider/JWT credentials fail authentication.
6. Run `/health`, `/health/db`, `/health/all`, auth login, and one query smoke test.
7. Record rotated key ids or secret versions, not secret values.

## Rollback Plan

1. Keep old credentials disabled but recoverable for a short founder-approved emergency window where provider policy allows.
2. If new credentials fail, restore service from the secret-manager previous version only after confirming old exposed credentials are not re-enabled publicly.
3. Re-run smoke tests after rollback.
4. File a security incident note explaining the rollback and re-rotation schedule.

## Timeline

| Window | Action |
|---|---|
| T-0 | Founder freezes repository writes and approves rotation |
| T+0-2h | Rotate provider, telemetry, seeded-user, JWT material |
| T+2-4h | Rotate PostgreSQL and Redis; restart local/staging services |
| T+4-6h | Force-push clean remote and require fresh clones |
| T+6-8h | Run fresh-clone scan and service smoke verification |
| T+24h | Confirm old credentials remain revoked and CI caches/stale clones are cleared |
