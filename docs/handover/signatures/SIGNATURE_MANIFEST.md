# NRG Handover Signature Manifest

**Protocol:** FOUNDER-SPRINT-2026-04-28
**Status:** BLOCKED - no local founder private signing key is configured
**Last checked:** 2026-04-29

## Required Signatures

| # | Document | Expected signature file | Status |
|---|---|---|---|
| 1 | `docs/handover/README.md` | `docs/handover/signatures/README.md.asc` | Pending |
| 2 | `docs/handover/SYSTEM_OVERVIEW.md` | `docs/handover/signatures/SYSTEM_OVERVIEW.md.asc` | Pending |
| 3 | `docs/handover/ARCHITECTURE.md` | `docs/handover/signatures/ARCHITECTURE.md.asc` | Pending |
| 4 | `docs/handover/API_REFERENCE.md` | `docs/handover/signatures/API_REFERENCE.md.asc` | Pending |
| 5 | `docs/handover/OPERATIONS_RUNBOOK.md` | `docs/handover/signatures/OPERATIONS_RUNBOOK.md.asc` | Pending |
| 6 | `docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md` | `docs/handover/signatures/SECURITY_COMPLIANCE_ATTESTATION.md.asc` | Pending |
| 7 | `docs/handover/DATA_INTAKE_PROTOCOL.md` | `docs/handover/signatures/DATA_INTAKE_PROTOCOL.md.asc` | Pending |
| 8 | `docs/handover/UAT_RESULTS.md` | `docs/handover/signatures/UAT_RESULTS.md.asc` | Pending |

## Local Key Check

`gpg --list-secret-keys --keyid-format LONG` completed successfully after keyring access approval, but returned no secret keys.

Result: signatures cannot be generated on this machine until the founder key is generated or imported.

## Signing Command

Run on the founder-controlled machine with the founder private key available:

```bash
cd /Users/srujansai/Desktop/NRG/docs/handover/signatures
for doc in ../README.md ../SYSTEM_OVERVIEW.md ../ARCHITECTURE.md \
           ../API_REFERENCE.md ../OPERATIONS_RUNBOOK.md \
           ../SECURITY_COMPLIANCE_ATTESTATION.md ../DATA_INTAKE_PROTOCOL.md \
           ../UAT_RESULTS.md; do
  gpg --armor --detach-sign --output "$(basename "$doc").asc" "$doc"
done
find . -maxdepth 1 -name "*.asc" | wc -l
```

Expected count: `8`.

## Verification Command

```bash
cd /Users/srujansai/Desktop/NRG/docs/handover/signatures
for sig in *.asc; do
  doc="../${sig%.asc}"
  gpg --verify "$sig" "$doc"
done
```

## Terminal Step

Do not create or move the final `v1.0.0-eternal` tag until:

- all eight signatures above are present and verified;
- K-2/C4 evidence is passing on the target stack;
- live UAT sessions are attached;
- founder approves the final tag ceremony.
