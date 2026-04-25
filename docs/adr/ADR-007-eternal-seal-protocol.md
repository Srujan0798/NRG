# ADR-007: Eternal Seal Protocol — Zero-Knowledge Attestation for Sovereign Deployment

**Date:** 2026-04-25
**Status:** Proposed
**Author:** Session 92 Agent

## Context

The NRG platform must provide **cryptographic proof** that:
1. The audit chain has not been tampered with (chain seal)
2. All data processing respects consent boundaries (C1)
3. PII is not exfiltrated (C2)
4. Per-user audit binding is enforced (C6)

This "eternal seal" must be verifiable by external auditors without giving them access to the sovereign cluster. The current approach uses GPG signing of the chain hash, but this requires the Founder's private key to be present on the cluster — a security risk.

## Decision

We adopt a **TPM-backed local attestation + remote verification** architecture using the following design:

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ SOVEREIGN CLUSTER (air-gapped)                                   │
│                                                                  │
│  Chain Seal Step:                                                │
│  1. osSEEK() → TPM quote of chain.jsonl digest                   │
│  2. sign(quote, SRK) → TPM signature                             │
│  3. output: { quote, TPM_signature, chain_length, last_hash }    │
│                                                                  │
│  Evidence Bundle:                                                │
│  - /evidence/05_chain_seal.json                                  │
│  - .audit/chain.jsonl (not exported — stays on cluster)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ evidence bundle (no raw data)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXTERNAL AUDITOR (off-cluster)                                   │
│                                                                  │
│  Verification:                                                   │
│  1. Load TPM root public (from Manufacturer EK cert)              │
│  2. Verify TPM quote signature                                    │
│  3. Compare chain_length + last_hash against previous bundle    │
│  4. Replay verify_chain() on exported chain.jsonl               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. What gets signed: `{chain_length, last_hash, timestamp, policy_hash}`

We sign a **commitment** (digest of chain state), not the full chain. The commitment is:
- `chain_length`: number of events (detects insertions/deletions)
- `last_hash`: final hash in chain (detects modifications to any event)
- `timestamp`: monotonic clock reading (detects replay)
- `policy_hash`: SHA-256 of active policy config (C1+C2+C6 settings)

**Why not sign the full chain?**
- Chain is 100+ MB — expensive to sign every event
- Chain never leaves the sovereign cluster
- Commitment scheme is standard (Hash-and-Sign with collision-resistant hash)

#### 2. TPM vs. Software HSM

| | TPM 2.0 | Software HSM |
|--|---------|--------------|
| Physical | Discrete chip on motherboard | Softwar simulation |
| Tamper evidence | Yes — hardware binding | No |
| Cost | Pre-installed on most servers | Free |
| Sovereign | Yes — no external dependency | Yes |
| Key extraction | Prevented by hardware | Possible if host compromised |

**Decision:** Require TPM 2.0 on sovereign nodes; software simulation acceptable only for local dev.

#### 3. Policy Hash — What Config Gets Bound

The `policy_hash` commits to:
- `C1_ALLOWLIST`: egress whitelist (source IPs, domains)
- `C2_PII_COLUMNS`: columns flagged as PII
- `C6_ACCESS_TIERS`: tier boundary definitions
- `AUDIT_BINDING_ENABLED`: per-user key enforcement flag

Any change to these policies after sealing invalidates the attestation — preventing "policy drift."

## Options Considered

### Option A: GPG Signing (Current approach)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Key security | Private key must be on cluster |
| Sovereign | Partial — key material on machine |
| Non-repudiation | Strong |

**Cons:** Key on cluster violates sovereign principle; if cluster is compromised, key is compromised.

### Option B: HSM-as-a-Service (AWS CloudHSM, Azure Key Vault)
**Pros:** FIPS 140-2, managed, audited
**Cons:** Not sovereign — data leaves cluster for key operations; vendor lock-in; costly.

### Option C: TSS2 (TPM Software Stack) + remote attestation
**Pros:** Standards-based, sovereign, hardware-backed
**Cons:** Complex setup; requires TPM 2.0 provisioning

## Consequences

### Positive
- Auditor can verify chain integrity without ever touching raw data
- Policy changes are detectable via policy_hash mismatch
- TPM provides hardware-level tamper evidence
- No private key material leaves the sovereign cluster
-符合印度国家安全要求 (sovereign air-gap compatible)

### Negative
- Requires TPM 2.0 provisioning on sovereign nodes (added deployment complexity)
- TPM quote verification requires auditor to have TPM manufacturer root cert
- Policy_hash requires version control + hash computation on every seal step
- Chain export for replay verification requires separate secure channel (audit chain file itself never moves)

## Action Items

- [ ] Implement `TPMSealer` class using `tpm2-tss` or `pytss` library
- [ ] Define `PolicyCommitment` schema: `PolicyCommitment = {c1_hash, c2_hash, c6_hash, version}`
- [ ] Compute `policy_hash = SHA256(policy_commitment_json)` at seal time
- [ ] Add TPM quote generation to `scripts/chain_seal_attestation.py`
- [ ] Create auditor verification script in `scripts/verify_eternal_seal.py`
- [ ] Document TPM provisioning steps in `docs/architecture/OPERATIONS_RUNBOOK.md`
- [ ] Add `policy_hash` to evidence bundle output
- [ ] Write integration test: change C1 allowlist → verify policy_hash mismatch detected

## Evidence Bundle Schema

```json
{
  "eternal_seal_version": "1.0",
  "chain_seal": {
    "tpm_quote": "base64encoded TPM quote",
    "tpm_signature": "base64encoded TPM signature",
    "pcr_bank": "SHA256",
    "chain_length": 378779,
    "last_hash": "abc123...",
    "timestamp": "2026-04-25T12:00:00Z",
    "policy_hash": "sha256:xyz789..."
  },
  "c1_result": { "passed": true, "events_verified": 12847 },
  "c2_result": { "passed": true, "pii_columns_scanned": 23 },
  "c6_result": { "passed": true, "user_keys_verified": 3421 },
  "seal_timestamp": "2026-04-25T12:00:05Z",
  "next_seal_due": "2026-04-26T12:00:05Z"
}
```

**Reviewed by:** Session 92 Agent
**Next Review:** 2026-06-25
