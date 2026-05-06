# Blockers — Credential Rotation Plan

**Date:** 2026-05-05

## Immediate Blockers

### 1. Cannot Determine if Leaked Credentials Were LIVE

**Type:** Missing Information
**Block:** Cannot answer YES or NO to "were any leaked credentials live?"
**Reason:** The original 286-secret scan produced SHA256 fingerprint data but the actual fingerprints are not accessible to this scanner. The on-disk `.env` contains real-looking API keys (MINIMAX, NVIDIA) but we cannot compare them against the purged history without the original fingerprint list.
**Resolution:** Either (a) get the original 286 fingerprint list from the previous remediation run, or (b) have founder/API provider verify current keys are dev-only.

### 2. Scanner `--all-refs` Flag Not Available

**Type:** Tool Limitation
**Block:** Step 2 of assignment required `--all-refs` flag which the scanner does not support.
**Workaround:** Scanner defaults to `git log --all --full-history` which covers all branches. The limitation is cosmetic — all refs are still scanned by default.
**Resolution:** None needed — behavior is acceptable.

### 3. Runtime .env Files Not in Git History

**Type:** Configuration Finding
**Block:** The runtime `.env` files exist on disk but are NOT in git history (excluded by `.gitignore`). This means the scanner cannot detect if these on-disk files contain the same secrets that were purged from history.
**Resolution:** Requires external verification with API providers.

---

## Tasks That Can Proceed in Parallel

- [x] Local git history scan → PASS, 0 findings
- [x] Active env vars audit → complete
- [x] Secret inventory → complete
- [x] Rotation plan documentation → complete (pending verification)
- [ ] Pre-commit hook to detect `.env` commits (optional enhancement)
- [ ] CI/CD secret exposure audit (optional enhancement)

---

## Decision Required From Founder

1. **Verify MINIMAX_API_KEY status** - dev-only or production?
2. **Verify NVIDIA_API_KEY status** - dev-only or production?
3. **Approve or skip credential rotation** — based on verification results

---

## Stop Rules Applied

- ✅ Local history scan shows 0 findings → purge worked
- ⚠️ Cannot determine live vs. dummy status → flagged as BLOCKER (Stop Rule 3)
- ✅ No actual credential values written in evidence files → compliant
- ✅ No git history findings → no STOP required per Stop Rule 2
