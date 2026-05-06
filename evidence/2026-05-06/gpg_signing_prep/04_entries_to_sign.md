# Entries Requiring Founder GPG Signatures

**Date:** 2026-05-06
**Chain file:** `.audit/chain.jsonl`
**Total chain entries:** 609,810
**Required signatures:** 8

The assignment states that 8 audit-chain entries require founder GPG signatures. The audit protocol file does not define a separate 8-entry manifest, so this package uses the 8 milestone events named by the assignment context and existing prior evidence. If Guru requires a different manifest, update this file and the script before the founder signs.

## Signing Manifest

| # | Line | Event Type | Event ID | Hash | Timestamp | User ID |
|---|---:|---|---|---|---|---|
| 1 | 1 | `chain_genesis` | `genesis` | `46e3323a74eb9eb7ba689b806c62abea12e24cfb2d608b1c28a2ae26c1044dd8` | 2026-04-28T13:20:28.052747+00:00 | `system` |
| 2 | 89 | `brute_force_attempt` | `dc012907` | `e2b9b33c2e04286514b98dc4176982de6852662961e05e608eb9c178dba94b68` | 2026-04-28T11:44:51.336562+00:00 | `bruteforce_test_user` |
| 3 | 356 | `consent_granted` | `3218dd3c` | `33f174b12a069f5622b9d2f7431f38d9d76424fdf286deaeab0a83d9b456acfb` | 2026-04-28T11:44:58.802205+00:00 | `user1` |
| 4 | 357 | `consent_revoked` | `8f837c33` | `ffe320af170318192f3810258155ff119e897fae09507483bff85e90bb3b1010` | 2026-04-28T11:44:58.896196+00:00 | `user1` |
| 5 | 375 | `data_erasure` | `0186bb3d` | `8f71b45f4d8ba24cfaeff26ea423303541ba1dcff26c4802a36e91061c89aea9` | 2026-04-28T11:44:59.869139+00:00 | `user1` |
| 6 | 383 | `data_export` | `a515bab5` | `c20661602474b3ee401be3f9560fd363e97559b497d28deb0959d8e0cc1f8106` | 2026-04-28T11:45:00.326920+00:00 | `user_exp` |
| 7 | 38302 | `chain_rebuild` | `1438e673` | `4c3a2170ed44433f674e85bae92a156a3c1de20e6f59a0bd3ad1a03eaec2d6c6` | 2026-04-30T01:31:51.066574+00:00 | `system` |
| 8 | 289837 | `ingest_batch` | `15cfed1e` | `f74b5d32b70d288e18e29fa7d4f4e8bd8bcf4e98016b09a573b31b330a1b6b8f` | 2026-05-02T13:00:38.920311+00:00 | `system` |

## Signature Output

The signing script writes one canonical extracted JSON line and one detached signature per entry under:

```text
.audit/signatures/
```

Expected detached signature filenames:

```text
entry_001_chain_genesis.json.asc
entry_002_brute_force_attempt.json.asc
entry_003_consent_granted.json.asc
entry_004_consent_revoked.json.asc
entry_005_data_erasure.json.asc
entry_006_data_export.json.asc
entry_007_chain_rebuild.json.asc
entry_008_ingest_batch.json.asc
```
