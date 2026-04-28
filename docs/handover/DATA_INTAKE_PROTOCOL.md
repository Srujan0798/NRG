# NRG Data Intake Protocol

## SFTP + GPG + HMAC Manifest Handshake — Staging → Validation → Promotion Flow

**Version:** 1.0  
**Date:** 2026-04-24  
**Classification:** Internal — Data Operations  
**Cross-Reference:** `docs/DATA_INTAKE_PROTOCOL.md` (full protocol)  

---

## 1. Overview

This document describes how to intake 600GB of national research data into NRG. The full protocol with technical details is in `docs/DATA_INTAKE_PROTOCOL.md`.

### 1.1 Data Sources

The 600GB dataset consists of:
- **Researcher records**: ~500,000 researchers
- **Institution data**: ~2,400 institutions
- **Publication records**: ~5M publications
- **Funding data**: Government and private funding
- **Patent records**: Filed and granted patents
- **Lab infrastructure**: Research lab details
- **Collaboration networks**: Inter-institutional records

### 1.2 Data Sovereignty Requirement

> **CRITICAL**: The 600GB repository resides exclusively on Indian servers. The system is architecturally incapable of uploading data to the internet.

---

## 2. Intake Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SOURCE: MHRD/NIC                                  │
│                           (Government Systems)                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ SFTP + GPG Encrypted Transfer
                                  │ SHA-256 Manifest
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGING ZONE (Isolated Network)                          │
│                                                                              │
│  /data/intake/YYYY-MM-DD/                                                   │
│  ├── manifest.json          (HMAC-signed manifest)                          │
│  ├── researchers/           (encrypted CSVs)                                │
│  ├── institutions/                                                         │
│  ├── publications/                                                         │
│  ├── funding/                                                              │
│  ├── patents/                                                              │
│  └── labs/                                                                 │
│                                                                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ HMAC Verification + Decryption
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VALIDATION ZONE                                         │
│                                                                              │
│  1. Manifest HMAC verification                                              │
│  2. File checksum validation (SHA-256)                                       │
│  3. PII scan (Aadhaar, PAN, phone, email)                                   │
│  4. Schema mapping verification                                            │
│  5. Format validation (CSV/JSON/XML)                                        │
│                                                                              │
│  PASS → Promote to loading                                                  │
│  FAIL → Quarantine and notify source                                        │
│                                                                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ Approved for loading
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LOADING ZONE (NRG PostgreSQL)                          │
│                                                                              │
│  Tables loaded in dependency order:                                          │
│  1. tb_institute_mstr (no deps)                                             │
│  2. tb_goi_ministries_mstr (no deps)                                        │
│  3. tb_academic_year_mstr (no deps)                                         │
│  4. [other master tables]                                                   │
│  5. researchers (requires institution_id)                                  │
│  6. institutions                                                             │
│  7. labs (requires institution_id)                                          │
│  8. publications (requires researcher_id, institution_id)                  │
│  9. patents (requires institution_id)                                        │
│  10. funding_records (requires researcher_id, institution_id)                │
│  11. [junction tables]                                                      │
│                                                                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  │ Post-load verification
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PRODUCTION ZONE (NRG Live)                             │
│                                                                              │
│  • Row count verification                                                    │
│  • Sample query verification                                                │
│  • Schema parity check                                                      │
│  • Dhairya benchmark validation (17 queries ≥85% accuracy)                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SFTP + GPG + HMAC Handshake Protocol

### 3.1 Pre-Arrival Checklist

```
□ Source system credentials verified
□ VPN/private link tested
□ Receiving directory created: /data/intake/YYYY-MM-DD/
□ GPG key pair generated and distributed
□ HMAC secret key securely shared
□ Checksums (SHA-256) received for all files
□ File count matches manifest
□ Total bytes match manifest
□ Audit logging active
```

### 3.2 SFTP Transfer

```bash
# Connect to source (MHRD/NIC)
sftp data_source@mhrd.nic.in

# Transfer files (encrypted at rest)
cd /data/intake/2026-04-24
put researchers_2026.tar.gz.gpg
put institutions_2026.tar.gz.gpg
put publications_2026.tar.gz.gpg
put funding_2026.tar.gz.gpg
put patents_2026.tar.gz.gpg
put labs_2026.tar.gz.gpg
put manifest.json.hmac

# Verify transfer completeness
ls -la
```

### 3.3 Manifest Structure

```json
{
  "manifest_id": "MAN-2026-04-24-001",
  "created_at": "2026-04-24T10:00:00Z",
  "source": "MHRD/NIC",
  "total_bytes": 644245094400,
  "total_files": 150,
  "sha256_checksum": "abc123def456...",
  "hmac_signature": "sig_xyz789...",
  "files": [
    {
      "filename": "researchers_2026.tar.gz.gpg",
      "bytes": 150000000000,
      "sha256": "file1_hash...",
      "record_count": 500000
    },
    {
      "filename": "publications_2026.tar.gz.gpg",
      "bytes": 200000000000,
      "sha256": "file2_hash...",
      "record_count": 5000000
    }
  ]
}
```

### 3.4 HMAC Manifest Verification

```bash
# Verify intake bundle manifest, checksums, optional sidecar signatures, and row HMACs
python scripts/verify_intake_bundle.py \
  --bundle-dir /data/intake/2026-04-24/ \
  --manifest /data/intake/2026-04-24/manifest.json \
  --hmac-secret-env DATA_INTAKE_HMAC_SECRET

# Expected output
# HMAC VERIFIED ✓
# File count: 150/150
# Total bytes: 644245094400/644245094400 ✓
```

### 3.5 GPG Decryption

```bash
# Decrypt files using government GPG key
gpg --decrypt researchers_2026.tar.gz.gpg | tar -xz -C /data/intake/2026-04-24/
gpg --decrypt publications_2026.tar.gz.gpg | tar -xz -C /data/intake/2026-04-24/
# ... repeat for all files

# Verify decrypted checksums
sha256sum /data/intake/2026-04-24/researchers/*.csv
# Must match manifest
```

---

## 4. Validation Phase

### 4.1 PII Scan (Critical Security Step)

> **IMPORTANT**: Any PII detected triggers immediate quarantine and review.

```python
PII_PATTERNS = {
    "aadhaar": r"\b[2-9]{1}[0-9]{11}\b",
    "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "phone": r"\b[6-9]{1}[0-9]{9}\b",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
}
```

```bash
# Run the seven-pillar scorecard before import, including PII leakage checks
python scripts/data_quality_scorecard.py \
  --database-url "$DATABASE_URL" \
  --json-output /data/intake/2026-04-24/pii_scan_report.json \
  --markdown-output /data/intake/2026-04-24/data_quality_report.md \
  --fail-on-p0

# If PII found:
# 1. Quarantine affected files
# 2. Notify source system
# 3. Do NOT proceed until resolved
```

### 4.2 Validation Checks

| Check | Pass Criteria | Fail Action |
|-------|--------------|-------------|
| File completeness | All files present per manifest | HALT, notify source |
| Checksum verification | SHA-256 matches provided | HALT, re-download |
| Format validation | CSV/JSON/XML parses correctly | Log, skip malformed |
| Schema mapping | All required fields present | HALT, clarify with source |
| PII scan | No Aadhaar/PAN in public fields | QUARANTINE, review |

---

## 5. Loading Phase

### 5.1 Loading Order (Dependency Aware)

Tables must be loaded in this order due to foreign key dependencies:

```
1. tb_institute_mstr         (no dependencies)
2. tb_goi_ministries_mstr    (no dependencies)
3. tb_academic_year_mstr    (no dependencies)
4. tb_course_program_types  (no dependencies)

5. researchers               (requires institution_id)
6. institutions              (no dependencies)
7. labs                      (requires institution_id)

8. publications              (requires researcher_id, institution_id)
9. patents                  (requires institution_id)
10. funding_records          (requires researcher_id, institution_id)

11. researcher_publications (requires researcher_id, publication_id)
12. researcher_labs          (requires researcher_id, lab_id)
13. collaborations          (requires institution_id)

14. innovation_grant_from_govt       (requires institution_id)
15. patents_details                    (requires institution_id)
16. incubation_details                (requires institution_id)
```

### 5.2 Loading Commands

**PostgreSQL:**
```bash
# Parallel loading
pg_restore -j 16 -d nrg prod_dump.dump

# Or for CSV
psql -c "COPY researchers FROM 'researchers_part_*.csv' WITH (FORMAT csv, PARALLEL TRUE)"
```

### 5.3 Progress Tracking

Every table load is audit-logged:

```python
load_progress = {
    "event": "DATA_LOAD",
    "table": "researchers",
    "rows_loaded": 150000,
    "rows_total": 500000,
    "bytes_processed": "300GB",
    "errors": 0,
    "warnings": 12,
    "elapsed_seconds": 3600
}
```

### 5.4 Error Handling

| Error Type | Recovery Action |
|------------|-----------------|
| FK violation | Log row, skip, continue |
| Constraint violation | Log row, skip, continue |
| Connection loss | Retry 3 times, then halt |
| Disk full | Halt, notify ops |
| Duplicate key | Update existing, log |

---

## 6. Post-Load Verification

### 6.1 Row Count Verification

```sql
SELECT
    'researchers' as table_name,
    COUNT(*) as expected,
    (SELECT COUNT(*) FROM researchers) as actual
UNION ALL
SELECT 'institutions', 2400, (SELECT COUNT(*) FROM institutions)
UNION ALL
SELECT 'publications', 5000000, (SELECT COUNT(*) FROM publications);
```

### 6.2 Dhairya Benchmark Validation

After data load, run the Dhairya SQL benchmark to verify data fitness:

```bash
python scripts/benchmark_dhairya_queries.py --url postgresql://...

# Target: All 17 queries execute without errors
# Current SQL accuracy: 41% (pre-data-load)
# Target after full load: ≥85% accuracy
```

### 6.3 Performance Verification

```sql
EXPLAIN ANALYZE
SELECT r.name, r.research_area, COUNT(p.publication_id) as pub_count
FROM researchers r
LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
LEFT JOIN publications p ON rp.publication_id = p.publication_id
WHERE r.institution_id = 1
GROUP BY r.researcher_id, r.name, r.research_area;

-- Expected: Execution time < 5 seconds
```

---

## 7. Rollback Procedures

### 7.1 If Loading Fails Mid-Way

```bash
# Stop all loading
pkill -f "COPY researchers"

# Verify current state
SELECT COUNT(*) FROM researchers;

# Restore from pre-load backup
pg_restore -d nrg pre_load_backup.dump
```

### 7.2 If Data Quality Issues Found After Load

```bash
# Quarantine affected rows
UPDATE researchers SET quarantine = true WHERE invalid_condition = true;

# Generate quarantine report
SELECT * FROM researchers WHERE quarantine = true;

# Manual review before cleanup
```

---

## 8. Contacts and Escalation

| Role | Contact | Escalation |
|------|---------|------------|
| Data Intake Lead | ops@nrg.iitgn.ac.in | guru@nrg.in |
| Database Admin | dba@nrg.iitgn.ac.in | guru@nrg.in |
| Security Officer | security@nrg.iitgn.ac.in | guru@nrg.in |

---

*Document version: 1.0*  
*Last updated: 2026-04-24*  
*Full protocol: `docs/DATA_INTAKE_PROTOCOL.md`*  
*For questions: ops@nrg.iitgn.ac.in*
