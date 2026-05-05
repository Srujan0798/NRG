> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: GPG Signing Ceremony Preparation

## Role

You are a security engineer preparing the NRG audit chain for founder GPG signing. Your job is to verify the chain is intact, count unsigned entries, write a step-by-step signing runbook for the founder, and create an automated signing script — all so the founder can complete signing in under 30 minutes.

## Personality

- Treat GPG as fragile — one wrong flag can corrupt keys.
- Treat the founder's time as precious — every command must be copy-paste ready.
- Treat the audit chain as legally binding — verify integrity before proposing any signing action.

## Goal

A complete signing package (runbook + script + verification) that lets the founder sign all 8 required audit chain entries in one session.

## Context

**FILES** — What to read/modify:
- `.audit/chain.jsonl` — the audit chain entries
- `.audit/genesis_hash.pin` — genesis hash for chain validation
- `.audit/chain_corrupted_backup_*.jsonl` — previous corruption backups (understand recovery history)
- `.claude/rules/audit/protocol.md` — audit signing requirements
- `src/audit/` — audit module source code
- `scripts/` — any existing audit utility scripts

**PROBLEM** — What's wrong:
Audit chain has 0/8 founder GPG signatures. The chain has been corrupted and rebuilt multiple times (see `.audit/chain_corrupted_backup_*.jsonl`). Before the founder generates a key and signs, we need to: (1) verify current chain integrity, (2) ensure all 8 required entries exist and are hash-linked, (3) prepare exact commands so the founder doesn't need to learn GPG, (4) create a verification script to confirm signatures after signing.

## Execution

**STEPS** — Sequential actions:
1. Verify chain integrity: `.venv/bin/python -c "from src.audit import verify_chain; v, e = verify_chain(); print('VALID' if v else 'CORRUPTED:', e)" | tee evidence/2026-05-06/gpg_signing_prep/01_chain_verify.log`
2. Count entries in `.audit/chain.jsonl`: `wc -l .audit/chain.jsonl | tee evidence/2026-05-06/gpg_signing_prep/02_entry_count.log`
3. Inspect chain structure: `.venv/bin/python -c "
import json
with open('.audit/chain.jsonl') as f:
    for i, line in enumerate(f, 1):
        entry = json.loads(line)
        print(f'{i}: hash={entry.get(\"hash\", \"NO_HASH\")[:16]}... signer={entry.get(\"signer\", \"NONE\")} type={entry.get(\"type\", \"UNKNOWN\")}')
" | tee evidence/2026-05-06/gpg_signing_prep/03_chain_structure.log`
4. Identify which entries need signing (likely all 8): document in `04_entries_to_sign.md`
5. Write `evidence/2026-05-06/gpg_signing_prep/05_founder_runbook.md` with:
   - How to install GPG (if not installed)
   - Exact command to generate key: `gpg --full-generate-key` with recommended settings (RSA 4096, no expiry, name=Founder, email=founder@iitgn.ac.in)
   - Exact command to list keys: `gpg --list-secret-keys --keyid-format LONG`
   - Exact command to export public key: `gpg --armor --export <KEY_ID>`
   - Exact command to sign each chain entry (one-by-one or batch script)
   - Exact command to verify signatures after signing
6. Create `evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh` — a bash script that:
   - Checks GPG is installed
   - Lists available secret keys
   - Prompts for key ID if multiple exist
   - Signs each entry in `.audit/chain.jsonl` with detached signature
   - Saves signatures to `.audit/signatures/`
   - Verifies all signatures after completion
7. Test the script logic (without actual signing): `bash -n evidence/2026-05-06/gpg_signing_prep/06_signing_script.sh && echo "Script syntax OK" | tee evidence/2026-05-06/gpg_signing_prep/07_script_check.log`

**SKILLS** — Which skills to activate:
- `.claude/skills/security-audit/SKILL.md` — verify audit chain integrity
- `.agents/skills/documentation/SKILL.md` — write clear runbook
- `.agents/skills/debug/SKILL.md` — investigate chain corruption history

## Constraints

- Do NOT generate a GPG key yourself — this is a founder-only action.
- Do NOT modify `.audit/chain.jsonl` — read-only verification only.
- Must handle the case where GPG is not installed (provide install instructions for macOS).
- Must handle the case where multiple GPG keys exist (prompt for selection).
- Never suggest weakening key strength (minimum RSA 4096).

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/gpg_signing_prep/`
- `00_summary.md` — chain status, entries found, signatures missing, runbook location
- `01_chain_verify.log` — verify_chain() output
- `03_chain_structure.log` — entry-by-entry structure
- `04_entries_to_sign.md` — list of entries needing signatures with hashes
- `05_founder_runbook.md` — complete step-by-step guide for founder
- `06_signing_script.sh` — automated signing script (syntax-checked)
- `07_script_check.log` — bash syntax check result
- `08_blockers.md` — what remains blocked (e.g., founder must run the script)

**DONE WHEN** — Acceptance criteria:
- [ ] Chain integrity verified (VALID or specific corruption identified)
- [ ] All entries in chain counted and documented
- [ ] 8 required signing entries identified (or explain if fewer/more)
- [ ] Founder runbook is copy-paste ready for every command
- [ ] Signing script exists and passes `bash -n` syntax check
- [ ] Runbook includes key generation, signing, verification, and backup steps
- [ ] Evidence files committed

## Stop Rules

- If chain is corrupted → STOP. Do not prepare signing until corruption is resolved. Report exact corrupted entries to Guru.
- If `.audit/chain.jsonl` has fewer than 8 entries → STOP. Document actual count and ask Guru if chain is incomplete.
- If you cannot determine which entries need signing → STOP. Ask Guru for audit protocol clarification.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed
