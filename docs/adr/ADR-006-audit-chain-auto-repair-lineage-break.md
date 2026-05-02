# ADR-006: Audit Chain Lineage Repair And Genesis Pinning

Date: 2026-05-03

## Status

Accepted and locally implemented.

## Context

The audit chain can be repaired when a local file corruption creates a line-1
hash mismatch, but that repair changes the active chain lineage. Operators need
two separate facts:

- whether the current chain verifies cryptographically;
- whether the current chain still shares the same first-event anchor as the
  prior accepted lineage.

Without a pinned first-event hash, a repair can produce a valid chain while
hiding that the active genesis changed.

## Decision

The first appended audit event now creates `.audit/genesis_hash.pin` as the
local lineage anchor. The application and rebuild tooling treat the pin as
write-once:

- create it with exclusive file creation;
- fsync the content before close;
- harden file permissions to `0444`;
- never replace an existing pin during normal append or rebuild flows;
- report a critical lineage status when the active first-event hash differs
  from the pinned hash.

`scripts/audit_rebuild.py --rebuild --preserve-lineage` refuses to rewrite a
chain whose active first-event hash does not match the pinned hash unless an
operator passes `--force`.

## Consequences

The local runtime can no longer silently rotate the genesis anchor as a mutable
cursor. An operator with filesystem ownership can still override local file
permissions, so sovereign deployment must place the audit directory or exported
pin evidence on approved immutable storage or object-lock storage for external
attestation.

## Verification

- `tests/audit/test_chain_integrity.py::TestAuditChainIntegrity::test_genesis_pin_is_created_once_and_hardened_read_only`
- `tests/audit/test_chain_integrity.py::TestAuditChainRebuildScript::test_rebuild_script_ensure_genesis_pin_hardens_existing_anchor`
- `tests/audit/test_chain_integrity.py::TestAuditChainRebuildScript::test_rebuild_script_preserve_lineage_requires_force_on_pin_mismatch`
