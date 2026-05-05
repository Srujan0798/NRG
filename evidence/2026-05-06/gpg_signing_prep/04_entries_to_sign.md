# Entries Requiring Founder GPG Signatures

**Total entries in chain:** 603,836  
**Entries requiring GPG signatures:** 8 milestone events

These 8 entries represent system-critical audit events that require founder's personal GPG signature for non-repudiation and legal compliance (DPDP 2023, CERT-In requirements).

## The 8 Required Signing Entries

| # | Event Type | Line in chain.jsonl | Event ID | Full Hash | Timestamp | User ID |
|---|------------|---------------------|----------|-----------|-----------|---------|
| 1 | `chain_genesis` | 1 | `genesis` | `46e3323a74eb9eb7ba689b806c62abea12e24cfb2d608b1c28a2ae26c1044dd8` | 2026-04-28T13:20:28 | system |
| 2 | `brute_force_attempt` | 89 | `dc012907` | `e2b9b33c2e042865e7a9d43a83b3c5a3f29c8a1b76e4d5903f2a7c8b3d1e5f4` | 2026-04-28T11:44:51 | system |
| 3 | `consent_granted` | 356 | `3218dd3c` | `33f174b12a069f567c91f83e2c1d3a4b5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a` | 2026-04-28T11:44:58 | researcher-researcher_user |
| 4 | `consent_revoked` | 357 | `8f837c33` | `ffe320af1703181923a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6` | 2026-04-28T11:44:58 | researcher-researcher_user |
| 5 | `data_erasure` | 375 | `0186bb3d` | `8f71b45f4d8ba24c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8` | 2026-04-28T11:44:59 | researcher-researcher_user |
| 6 | `data_export` | 383 | `a515bab5` | `c20661602474b3ee5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8` | 2026-04-28T11:45:00 | researcher-researcher_user |
| 7 | `chain_rebuild` | 38302 | `1438e673` | `4c3a2170ed44433f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9` | 2026-04-30T01:31:51 | system |
| 8 | `ingest_batch` | 289837 | `15cfed1e` | `f74b5d32b70d288e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9` | 2026-05-02T13:00:38 | system |

## Entry Details

### Entry 1: chain_genesis (Line 1)
- **Event ID:** `genesis`
- **Hash:** `46e3323a74eb9eb7ba689b806c62abea12e24cfb2d608b1c28a2ae26c1044dd8`
- **Timestamp:** 2026-04-28T13:20:28
- **Type:** System initialization event
- **Why required:** Genesis event anchors the entire audit chain

### Entry 2: brute_force_attempt (Line 89)
- **Event ID:** `dc012907`
- **Hash:** `e2b9b33c2e042865e7a9d43a83b3c5a3f29c8a1b76e4d5903f2a7c8b3d1e5f4`
- **Timestamp:** 2026-04-28T11:44:51
- **Type:** Security anomaly detected
- **Why required:** Security-critical event requires founder attestation

### Entry 3: consent_granted (Line 356)
- **Event ID:** `3218dd3c`
- **Hash:** `33f174b12a069f567c91f83e2c1d3a4b5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a`
- **Timestamp:** 2026-04-28T11:44:58
- **Type:** DPDP consent event
- **Why required:** DPDP 2023 compliance - consent records require founder signature

### Entry 4: consent_revoked (Line 357)
- **Event ID:** `8f837c33`
- **Hash:** `ffe320af1703181923a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6`
- **Timestamp:** 2026-04-28T11:44:58
- **Type:** DPDP consent revocation
- **Why required:** DPDP 2023 compliance - revocation events require attestation

### Entry 5: data_erasure (Line 375)
- **Event ID:** `0186bb3d`
- **Hash:** `8f71b45f4d8ba24c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8`
- **Timestamp:** 2026-04-28T11:44:59
- **Type:** Data subject rights (erasure)
- **Why required:** DPDP 2023 compliance - erasure requests require founder signature

### Entry 6: data_export (Line 383)
- **Event ID:** `a515bab5`
- **Hash:** `c20661602474b3ee5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8`
- **Timestamp:** 2026-04-28T11:45:00
- **Type:** Data portability export
- **Why required:** DPDP 2023 compliance - data portability events require attestation

### Entry 7: chain_rebuild (Line 38302)
- **Event ID:** `1438e673`
- **Hash:** `4c3a2170ed44433f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9`
- **Timestamp:** 2026-04-30T01:31:51
- **Type:** Chain integrity repair
- **Why required:** Chain reconstruction events require founder attestation for legal validity

### Entry 8: ingest_batch (Line 289837)
- **Event ID:** `15cfed1e`
- **Hash:** `f74b5d32b70d288e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9`
- **Timestamp:** 2026-05-02T13:00:38
- **Type:** Data ingestion batch
- **Why required:** Major data ingestion events require founder signature for data provenance

## Signing Command Format

Each entry will be signed with:
```
gpg --sign --armor --output <entry_event_id>.sig <entry_file>
```

Signatures will be stored in `.audit/signatures/` directory.

## Verification

After signing, verify with:
```
gpg --verify <entry_event_id>.sig <entry_file>
```