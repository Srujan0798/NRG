# Credential Rotation Plan

**Date:** 2026-05-05
**Task:** Assignment 4 — Shishya Credential Rotation Plan
**Status:** INCOMPLETE — BLOCKED (requires founder approval + external verification)

---

## 1. Secret Inventory

| Credential Class | Key Names Found | Location | Status |
|-----------------|-----------------|----------|--------|
| Model API Keys | MINIMAX_API_KEY, NVIDIA_API_KEY, GEMINI_API_KEY | `.env` (disk only) | LIVE (likely real keys) |
| Database Passwords | POSTGRES_PASSWORD | `.env.dev`, `.env.local` | DEV/TEST only |
| JWT Secrets | JWT_SECRET, JWT_SECRET_KEY | `.env`, `.env.dev`, `.env.staging` | DEV/TEST only |
| Acceptance User Passwords | RESEARCHER_PASSWORD, GOV_PASSWORD, INDUSTRY_PASSWORD | `.env` | DEV/TEST only |
| Redis Passwords | REDIS_PASSWORD | `.env.staging`, `.env.prod` | Placeholder only |
| Audit Chain Key | AUDIT_CHAIN_KEY | `.env.example` | DEV only |

---

## 2. Live Credential Check

**QUESTION: Were any of the 286 leaked credentials LIVE (production-capable)?**

**ANSWER: CANNOT DETERMINE FROM LOCAL SCAN ALONE**

### Evidence:
- Local git history scan: **0 findings** → history purge verified working
- On-disk `.env` contains MINIMAX_API_KEY and NVIDIA_API_KEY with real-looking key prefixes (sk-cp-*, nvapi-*)
- These on-disk files are NOT tracked in git (excluded via `.gitignore`)
- Scanner cannot compare on-disk keys against the 286 purged hashes (no access to the original 286 findings or their SHA fingerprints)

### Limitation:
The original 286-secret remediation report (`ENV_HISTORY_SECRET_REMEDIATION_2026-05-02.md`) references SHA256 fingerprint data but does not expose the actual secret values. Without the original fingerprint list, we cannot confirm whether the current on-disk keys match the leaked ones.

### External Verification Required:
To definitively answer YES or NO, one of the following is needed:
1. Access to the original 286-finding fingerprint list (SHA256 prefixes from the previous scan)
2. Direct verification with the API key providers (Minimax, NVIDIA) that the keys have not been used
3. Founder confirmation of whether these specific keys were ever in git commits

---

## 3. Rotation Steps

**NOTE: No rotation performed without founder approval. Steps below are documentation only.**

### If LIVE credentials confirmed (ANSWER = YES):

| Service | Key | Rotation Method | Downtime | Priority |
|---------|-----|----------------|----------|----------|
| Minimax | MINIMAX_API_KEY | Generate new key from Minimax console; update `.env` and any CI secrets | ~5 min | P0 |
| NVIDIA | NVIDIA_API_KEY | Generate new key from NVIDIA NGC console; update `.env` and any CI secrets | ~5 min | P0 |
| PostgreSQL | POSTGRES_PASSWORD | `ALTER USER nrg WITH PASSWORD 'new_secure_password'` + update all `.env` files and compose | ~10 min | P1 |
| JWT | JWT_SECRET | Run `openssl rand -base64 32` to generate new; update all env files; invalidate existing tokens | ~15 min | P1 |
| Acceptance Users | RESEARCHER_PASSWORD, GOV_PASSWORD, INDUSTRY_PASSWORD | Update passwords in auth DB; update `.env` files | ~10 min | P2 |

### If LIVE credentials NOT confirmed (ANSWER = NO):

| Service | Key | Status | Action |
|---------|-----|--------|--------|
| Minimax | MINIMAX_API_KEY | DEV/TEST only | Monitor for unusual usage; no immediate rotation needed |
| NVIDIA | NVIDIA_API_KEY | DEV/TEST only | Monitor for unusual usage; no immediate rotation needed |
| PostgreSQL | dev/local passwords | DEV/TEST only | Replace with stronger dev defaults (optional) |
| JWT | development-secret-key-2026 | DEV/TEST only | Rotate in next dev cycle (optional) |

---

## 4. Verification Steps

1. **History verification**: Run `scripts/scan_env_history_secrets.py` on a fresh clone of the remote → must show 0 findings
2. **API key verification**: Call Minimax/NVIDIA APIs with current keys to confirm they are active and scoped to dev only
3. **Git history check**: `git log --all --full-history -- .env*` must return empty on remote clone
4. **Disk vs git comparison**: Ensure no runtime `.env` files are accidentally committed in future pushes

---

## 5. Rollback Plan

**If rotation is performed and something breaks:**

1. **API keys**: Keep old keys valid for 24h after rotation; revert `.env` if new keys fail
2. **PostgreSQL**: Keep old password in `.env.backup`; document the original `ALTER USER` command to reverse
3. **JWT**: If new tokens fail, revert `.env` and force re-login of all users (last resort)
4. **Audit chain**: If AUDIT_CHAIN_KEY is rotated, all existing audit signatures become invalid — require full audit chain rebuild

---

## 6. Timeline

| Phase | Action | Duration | Depends On |
|-------|--------|----------|-----------|
| 0 | External verification (confirm if MINIMAX/NVIDIA keys are live) | 1-2 days | Founder/API providers |
| 1 | If YES: Emergency rotation of Minimax + NVIDIA keys | 30 min | Founder approval |
| 1 | If NO: Document as TEST/DEV only, no immediate action | 1 hour | - |
| 2 | Update `.env.example` with clearer "DO NOT USE IN PRODUCTION" labels | 1 hour | - |
| 3 | Add pre-commit hook to detect accidental `.env` commits | 2 hours | - |
| 4 | Verify CI/CD pipelines don't expose secrets in logs | 2 hours | - |

---

## 7. BLOCKERS

1. **Cannot confirm if on-disk API keys are the same as the 286 purged secrets** — requires original fingerprint list or external verification
2. **Scanner limitation** — `--all-refs` flag not available; however scanner defaults to `--all` via `git log --all --full-history`
3. **Founder approval required** before any actual credential rotation

---

## 8. Recommendation

**Interim posture:** Treat MINIMAX_API_KEY and NVIDIA_API_KEY as potentially live until proven otherwise.

**Immediate next step:** Founder or authorized personnel should:
1. Log into Minimax console and verify the current `sk-cp-...` key usage
2. Log into NVIDIA NGC and verify the current `nvapi-...` key usage
3. Report back whether these keys are dev-only or have production access

If production access confirmed → **URGENT: Rotate immediately**
If dev-only confirmed → **Document and close with no rotation needed**