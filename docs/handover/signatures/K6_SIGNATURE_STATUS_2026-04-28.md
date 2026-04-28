# K-6 GPG Signature Status

**Protocol:** FOUNDER-SPRINT-2026-04-28
**Status:** BLOCKED on founder private key
**Reason:** GnuPG is installed, but `gpg --list-secret-keys --keyid-format LONG`
returns no configured private signing keys for this user.

## Local Tool Check

```text
gpg (GnuPG) 2.5.19
Home: /Users/srujansai/.gnupg
Secret keys: none listed
```

## Required Documents

| # | Document | Expected signature file |
|---|---|---|
| 1 | `docs/handover/README.md` | `README.md.asc` |
| 2 | `docs/handover/SYSTEM_OVERVIEW.md` | `SYSTEM_OVERVIEW.md.asc` |
| 3 | `docs/handover/ARCHITECTURE.md` | `ARCHITECTURE.md.asc` |
| 4 | `docs/handover/API_REFERENCE.md` | `API_REFERENCE.md.asc` |
| 5 | `docs/handover/OPERATIONS_RUNBOOK.md` | `OPERATIONS_RUNBOOK.md.asc` |
| 6 | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` | `SECURITY_COMPLIANCE_ATTESTATION.md.asc` |
| 7 | `docs/handover/DATA_INTAKE_PROTOCOL.md` | `DATA_INTAKE_PROTOCOL.md.asc` |
| 8 | `docs/handover/UAT_RESULTS.md` | `UAT_RESULTS.md.asc` |

## Command To Run On Founder Machine

```bash
cd docs/handover/signatures/
for doc in ../README.md ../SYSTEM_OVERVIEW.md ../ARCHITECTURE.md \
           ../API_REFERENCE.md ../OPERATIONS_RUNBOOK.md \
           ../SECURITY_COMPLIANCE_ATTESTATION.md ../DATA_INTAKE_PROTOCOL.md \
           ../UAT_RESULTS.md; do
  gpg --armor --detach-sign --output "$(basename "$doc").asc" "$doc"
done
ls *.asc | wc -l
```

Expected count: `8`.

If the founder key has not been generated or imported on this machine, configure
it first:

```bash
gpg --full-generate-key
# or
gpg --import founder-private-key.asc
```

## Verification

```bash
cd docs/handover/signatures/
for sig in *.asc; do
  doc="../${sig%.asc}"
  gpg --verify "$sig" "$doc"
done
```
