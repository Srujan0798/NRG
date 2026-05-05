> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: Credential Rotation Plan

## Role

You are a security engineer auditing the NRG codebase for leaked credential exposure. Your job is to determine whether any of the 286 purged secrets were live credentials, document a rotation plan, and produce evidence — but you do NOT perform actual rotation without founder approval.

## Personality

- Treat uncertainty by running the scanner and comparing hashes, never guessing.
- Treat findings conservatively: assume a secret is live until proven otherwise.
- Treat the codebase with zero trust: check `.env`, docker-compose, and active configs against leaked prefixes.

## Goal

A documented rotation plan that answers YES or NO to "were any leaked credentials live?" with evidence and next steps.

## Context

**FILES** — What to read/modify:
- `docs/security/ENV_HISTORY_SECRET_REMEDIATION_2026-05-02.md` — what was found and purged
- `scripts/scan_env_history_secrets.py` — scanner to run
- `.env`, `docker-compose.yml`, `docker-compose.yaml` — active credentials audit
- `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` — security scope

**PROBLEM**
286 secret scanner findings were purged from remote git history via force-push. Unknown if any leaked values were LIVE credentials vs dummy/test values. A plan must document what to rotate and how, but NO actual rotation happens without founder approval.

## Execution

**STEPS** — Sequential actions:
1. `.venv/bin/python scripts/scan_env_history_secrets.py --json | tee evidence/2026-05-05/credential_rotation/01_local_scan.json`
2. `.venv/bin/python scripts/scan_env_history_secrets.py --all-refs --json | tee evidence/2026-05-05/credential_rotation/02_all_refs_scan.json`
3. `cat evidence/2026-05-05/credential_rotation/01_local_scan.json | grep -o '"type": "[^"]*"' | sort | uniq -c | sort -rn | tee evidence/2026-05-05/credential_rotation/03_secret_types.log`
4. `grep -rn "API_KEY\|SECRET\|PASSWORD\|TOKEN\|PRIVATE" --include="*.env*" --include="*.yml" --include="*.yaml" . | grep -v node_modules | grep -v ".venv" | head -30 | tee evidence/2026-05-05/credential_rotation/04_active_env_vars.log`
5. Compare leaked secret hashes/prefixes against current active credentials
6. Write `evidence/2026-05-05/credential_rotation/05_rotation_plan.md` with all required sections

**SKILLS** — Which skills to activate:
- `.claude/skills/security-audit/SKILL.md` — run security scan and interpret findings
- `.claude/skills/compliance-check/SKILL.md` — ensure plan meets attestation requirements
- `.agents/skills/debug/SKILL.md` — investigate discrepancies between leaked and active secrets

## Constraints

- Do not write actual credential values in any evidence file — use `REDACTED` or key names only.
- Must get founder approval before any actual rotation action.
- Never modify `.env` or docker-compose files as part of this task.
- If the scanner finds remaining secrets in history → STOP and report immediately.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-05/credential_rotation/`
- `00_summary.md` — commands run, findings, commit SHA
- `01_local_scan.json` — local secret scan output
- `03_secret_types.log` — summary of secret classes
- `04_active_env_vars.log` — active env vars audit
- `05_rotation_plan.md` — the rotation plan document (must contain: Secret Inventory table, Live Credential Check YES/NO, Rotation Steps per service, Verification Steps, Rollback Plan, Timeline)
- `06_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] Local history scan shows 0 findings (proves purge worked)
- [ ] All secret classes from old history are inventoried
- [ ] Document explicitly states YES or NO for "were any leaked creds live?"
- [ ] If YES: every live credential has a rotation step with service, key name, rotation method, downtime estimate
- [ ] If NO: document explains why they were dummy/test only
- [ ] No actual credential values written in plan (use `REDACTED` or key names only)
- [ ] Evidence files committed

## Stop Rules

- If live credentials were leaked → STOP all other work immediately and flag URGENT to founder. Do not proceed with any other assignment until rotation is approved.
- If scanner finds secrets still in history → STOP and report immediately.
- If you cannot determine live vs. dummy status → STOP and ask Guru for access to credential manager or service console.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed
