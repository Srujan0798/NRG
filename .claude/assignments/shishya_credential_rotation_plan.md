# SHISHYA ASSIGNMENT: Credential Rotation Plan

> Copy this entire block and paste to your Shishya agent. Do not paraphrase.

---

## Goal
Produce a concrete credential rotation plan. Remote-history cleanup evidence now
shows 0 findings after stale-branch cleanup, but if any previously exposed
values were LIVE credentials instead of dummy/test values, they must still be
rotated. This assignment does NOT rotate credentials; it produces the plan for
the founder to approve and execute.

## Must Read (in order)
1. `docs/security/ENV_HISTORY_SECRET_REMEDIATION_2026-05-02.md` — what was found and purged
2. `scripts/scan_env_history_secrets.py` — run this to see what classes of secrets were detected
3. `.claude/CURRENT_STATE.md` — check current blocker status
4. `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` — security scope

## Exact Commands to Run

```bash
# 1. Scan local history (should show 0 findings post-purge)
cd "$(git rev-parse --show-toplevel)"
mkdir -p evidence/2026-05-05/credential_rotation
.venv/bin/python scripts/scan_env_history_secrets.py --json 2>&1 | tee evidence/2026-05-05/credential_rotation/01_local_scan.json

# 2. Scan ALL refs including remote (may still show stale remote refs if any exist)
.venv/bin/python scripts/scan_env_history_secrets.py --all-refs --json 2>&1 | tee evidence/2026-05-05/credential_rotation/02_all_refs_scan.json

# 3. Identify which secret classes were in the old commits
cat evidence/2026-05-05/credential_rotation/01_local_scan.json | grep -o '"type": "[^"]*"' | sort | uniq -c | sort -rn | tee evidence/2026-05-05/credential_rotation/03_secret_types.log

# 4. Check current .env files and Docker compose for active creds
grep -rn "API_KEY\|SECRET\|PASSWORD\|TOKEN\|PRIVATE" --include="*.env*" --include="*.yml" --include="*.yaml" . 2>/dev/null | grep -v node_modules | grep -v ".venv" | head -30 | tee evidence/2026-05-05/credential_rotation/04_active_env_vars.log

# 5. Check if any leaked creds match current active creds (CRITICAL)
#    Compare hashes or prefixes of old leaked values vs current values.
#    If they match, those credentials ARE LIVE and MUST be rotated.
```

## Deliverable: Rotation Plan Document

Create: `evidence/2026-05-05/credential_rotation/05_rotation_plan.md`

Must contain these sections:

### 1. Secret Inventory
| Secret Class | Count Found | Live or Dummy? | Rotation Required? |
|-------------|-------------|----------------|-------------------|
| (fill in)   |             |                |                   |

### 2. Live Credential Check
- Did any leaked secret match a CURRENT active credential? YES / NO
- If YES: list exact keys and services affected

### 3. Rotation Steps (for each live credential)
| Service | Key Name | How to Rotate | Downtime? | Owner |
|---------|----------|---------------|-----------|-------|
|         |          |               |           |       |

### 4. Verification Steps
- How to confirm old credential no longer works
- How to confirm new credential works

### 5. Rollback Plan
- What to do if rotation breaks staging/production

### 6. Timeline
- Proposed rotation date
- Verification date
- Sign-off required from: _____________

## Acceptance Criteria

- [ ] Local history scan shows 0 findings (proves purge worked)
- [ ] All secret classes from old history are inventoried
- [ ] Document explicitly states YES/NO for "were any leaked creds live?"
- [ ] If YES: every live credential has a rotation step
- [ ] Plan is reviewed by founder before any rotation happens
- [ ] No actual credentials are written in the plan (use `REDACTED` or key names only)

## Evidence Output Path

Save all evidence to: `evidence/2026-05-05/credential_rotation/`

Required artifacts:
- `00_summary.md` — what you did, commands run, commit SHA
- `01_local_scan.json` — local secret scan output
- `03_secret_types.log` — summary of secret classes
- `04_active_env_vars.log` — active env vars audit
- `05_rotation_plan.md` — the rotation plan document
- `06_blockers.md` — what remains blocked

## If Blocked

Stop immediately and report BLOCKED with:
1. What command failed
2. Whether the scan script exists and works
3. What permission or input you need

## Halt Rule

If you find LIVE credentials that were leaked, STOP all other work and flag URGENT to founder. Do not proceed with any other assignment until rotation is approved.
