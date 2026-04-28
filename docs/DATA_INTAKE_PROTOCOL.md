# DATA_INTAKE_PROTOCOL.md — 600GB National Research Database Intake

> **Scope**: Documenting the process for ingesting 600GB of government research data into NRG.
> **Authority**: NRG Architecture Document (Core_Idea_Clean.md) + Protocol #21
> **Last Updated**: 2026-04-24

---

## 1. Overview

### 1.1 What This Document Covers

This document describes the end-to-end process for receiving, validating, transforming, and loading 600GB of national research data into the NRG PostgreSQL database. It covers data arrival formats, validation checks, transformation rules, loading procedures, and post-load verification.

### 1.1.1 Phase 7 Trigger Gate

P7-B is blocked until the sovereign cluster and SFTP intake bundle are both
ready. Before assigning or executing ingest work, run:

```bash
python3 scripts/phase7_preflight.py \
  --require P7-B \
  --intake-bundle-dir /data/intake/2026-05-xx
```

If the command exits non-zero, do not load data and do not claim ingest evidence.

### 1.2 Data Sources

The 600GB dataset consists of:
- **Researcher records**: Personal and professional data for ~500,000 researchers
- **Institution data**: ~2,400 institutions across India
- **Publication records**: ~5M publications with citations and metadata
- **Funding data**: Government and private funding records
- **Patent records**: Filed and granted patents from Indian patent offices
- **Lab infrastructure**: Research lab details and capabilities
- **Collaboration networks**: Inter-institutional collaboration records

### 1.3 Data Sovereignty Requirements

> **CRITICAL**: The 600GB repository resides exclusively on Indian servers. The system is architecturally incapable of uploading data to the internet.

- All data transfer must use secure, encrypted channels
- Data must never transit non-Indian infrastructure
- Audit logs must track every byte of data movement
- Access controls must be applied at file-system and database level

---

## 2. Pre-Arrival Preparation

### 2.1 Infrastructure Readiness

| Component | Specification | Status |
|-----------|--------------|--------|
| PostgreSQL Storage | 2TB allocated (600GB data + growth + indexes) | Required |
| Memory | 64GB RAM minimum | Required |
| CPU | 16 cores for parallel loading | Required |
| Network | 10Gbps internal (no internet egress) | Required |
| Backup Storage | 1TB for encrypted backups | Required |

### 2.2 Schema Verification

Before data arrival, verify the PostgreSQL schema matches `db_struct.sql`:

```bash
python scripts/schema_sync.py check --db postgresql://user:pass@host/nrg
```

Expected output: `SCHEMA IN SYNC ✓`

### 2.3 Receiving Server Preparation

1. Create dedicated intake user account with limited permissions
2. Configure audit logging for all file operations
3. Verify antivirus scanning is active
4. Test network connectivity to source system
5. Confirm VPN or private link is operational

---

## 3. Data Arrival Process

### 3.1 Arrival Formats

The 600GB dataset may arrive in the following formats:

| Format | Volume Estimate | Loading Strategy |
|--------|-----------------|------------------|
| CSV files (zipped) | ~450GB compressed | Parallel COPY |
| PostgreSQL dump | ~300GB | pg_restore with parallelism |
| JSON/JSONL | ~500GB | COPY with transformed values |
| XML | ~400GB | Pre-process then COPY |
| Parquet | ~200GB | COPY with Arrow reader |

### 3.2 Arrival Checklist

```
□ Source system credentials verified
□ VPN/private link tested
□ Receiving directory created: /data/intake/YYYY-MM-DD/
□ Manifest received: manifest.json
□ GPG detached signatures received for every file (.asc or .sig)
□ Row HMAC shared through DATA_INTAKE_HMAC_SECRET
□ Checksums received (SHA-256)
□ File count matches manifest
□ Total bytes match manifest
□ Audit logging active
```

### 3.3 Chain of Custody

Every data transfer must be logged:

```python
audit_entry = {
    "event": "DATA_ARRIVAL",
    "source": "MHRD/NIC",
    "timestamp": "2026-04-24T10:30:00Z",
    "file_count": 150,
    "total_bytes": 644245094400,
    "sha256_checksum": "abc123...",
    "receiving_user": "intake_service",
    "transport_method": "secure_file_transfer"
}
```

---

## 4. Validation Phase

### 4.1 Pre-Load Validation

Before loading into PostgreSQL, validate:

| Check | Pass Criteria | Fail Action |
|-------|--------------|-------------|
| File completeness | All files present per manifest | Halt, notify source |
| GPG signature | Every file verifies against source public key | Halt, notify source |
| Checksum verification | SHA-256 matches provided | Halt, re-download |
| Row HMAC | Every CSV row has valid `row_hmac` | Quarantine file, do not load |
| Format validation | CSV/JSON/XML parses correctly | Log, skip malformed |
| Schema mapping | All required fields present | Halt, clarify with source |
| PII scan | No Aadhaar/PAN in public fields | Quarantine, review |

### 4.1.1 Bundle Verification Command

Before any `COPY` or `pg_restore`, run the intake verifier:

```bash
export DATA_INTAKE_HMAC_SECRET="$(vault kv get -field=row_hmac secret/nrg/intake)"

python scripts/verify_intake_bundle.py \
  --bundle-dir /data/intake/2026-05-xx \
  --manifest /data/intake/2026-05-xx/manifest.json
```

For local dry runs without source signatures only:

```bash
python scripts/verify_intake_bundle.py \
  --bundle-dir ./fixtures/intake \
  --manifest ./fixtures/intake/manifest.json \
  --skip-gpg
```

Expected result before load: `"status": "pass"`, `files_verified` equals manifest file count, and `hmac.invalid_rows` is `0`.

### 4.2 PII Detection

Per NRG's security model, the following must never appear in raw data:
- Aadhaar numbers (12-digit + biometrics)
- PAN numbers (AABCB1234C format)
- Unencrypted email addresses (allowed after masking)
- Phone numbers (allowed after masking)

Any PII detected triggers immediate quarantine and review.

### 4.3 Sample Validation Script

```python
import re

PII_PATTERNS = {
    "aadhaar": r"\b[2-9]{1}[0-9]{11}\b",
    "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
    "phone": r"\b[6-9]{1}[0-9]{9}\b",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
}

def scan_file_for_pii(filepath: str) -> list:
    """Scan file and return PII matches."""
    matches = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            for pii_type, pattern in PII_PATTERNS.items():
                found = re.findall(pattern, line)
                if found:
                    matches.append({
                        "file": filepath,
                        "line": i + 1,
                        "type": pii_type,
                        "matches": found
                    })
    return matches
```

---

## 5. Transformation Phase

### 5.1 Data Type Mapping

Raw source data → PostgreSQL type:

| Source Type | PostgreSQL Type | Notes |
|-------------|-----------------|-------|
| VARCHAR | TEXT | Flexible for research data |
| INTEGER | BIGINT | Large researcher IDs |
| DECIMAL | DECIMAL(15,2) | Funding amounts |
| DATE | DATE | Academic dates |
| TIMESTAMP | TIMESTAMPTZ | UTC normalized |
| BOOLEAN | BOOLEAN | Status fields |

### 5.2 Normalization Rules

**Researcher Names**:
- Extract components: first_name, middle_name, last_name
- Normalize Unicode: NFD → NFC
- Handle titles: remove "Dr.", "Prof.", "Mr.", "Mrs." prefix

**Institution Names**:
- Map to canonical names in `tb_institute_mstr`
- Standardize abbreviations: IIT → Indian Institute of Technology

**Research Areas**:
- Map to controlled vocabulary in `master_expertise`
- Handle synonyms: "ML" = "Machine Learning" = "Artificial Intelligence (Narrow)"

**Funding Amounts**:
- Normalize to INR (crores)
- Handle "Lakhs", "Crores", "Millions" conversion
- Flag zero or negative values as invalid

### 5.3 Missing Data Handling

| Field Type | Missing Strategy |
|-----------|-------------------|
| Optional text | NULL |
| Required text | "Unknown" or derived value |
| Required FK | Quarantine row for manual review |
| Numeric | NULL (allowed for optional) |
| Date | NULL (allowed for optional) |

---

## 6. Loading Phase

### 6.1 Loading Strategy

For 600GB data, use parallel loading with the following approach:

```bash
# Parallel COPY for CSV files
psql -c "COPY researchers FROM 'researchers_part_*.csv' WITH (FORMAT csv, PARALLEL TRUE)"

# For PostgreSQL dump
pg_restore -j 16 -d nrg prod_dump.dump
```

### 6.2 Loading Order (Dependency Aware)

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

### 6.3 Progress Tracking

Track loading progress with audit entries:

```python
load_progress = {
    "table": "researchers",
    "rows_loaded": 150000,
    "rows_total": 500000,
    "bytes_processed": 300GB,
    "errors": 0,
    "warnings": 12,
    "elapsed_seconds": 3600
}
```

### 6.4 Error Handling

| Error Type | Recovery Action |
|------------|-----------------|
| FK violation | Log row, skip, continue |
| Constraint violation | Log row, skip, continue |
| Connection loss | Retry 3 times, then halt |
| Disk full | Halt, notify ops |
| Duplicate key | Update existing, log |

---

## 7. Post-Load Verification

### 7.1 Row Count Verification

After loading, verify expected row counts:

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

### 7.2 Sample Query Verification

Run sample queries against loaded data:

```sql
-- Verify researcher data
SELECT COUNT(DISTINCT institution_id) FROM researchers;

-- Verify funding data
SELECT SUM(grant_received) FROM innovation_grant_from_govt;

-- Verify publication linkage
SELECT COUNT(*) FROM researcher_publications rp
JOIN researchers r ON rp.researcher_id = r.researcher_id;
```

### 7.3 Schema Parity Check

After loading, run schema parity verification:

```bash
python scripts/schema_sync.py check --db postgresql://...
```

Expected: `SCHEMA IN SYNC ✓`

### 7.4 Performance Verification

Check query performance on sample:

```sql
EXPLAIN ANALYZE
SELECT r.name, r.research_area, COUNT(p.publication_id) as pub_count
FROM researchers r
LEFT JOIN researcher_publications rp ON r.researcher_id = rp.researcher_id
LEFT JOIN publications p ON rp.publication_id = p.publication_id
WHERE r.institution_id = 1
GROUP BY r.researcher_id, r.name, r.research_area;
```

Expected: Execution time < 5 seconds for typical queries.

---

## 8. Post-Load Steps

### 8.1 Index Creation

After data load, create indexes for performance:

```sql
-- Researchers
CREATE INDEX idx_researchers_institution ON researchers(institution_id);
CREATE INDEX idx_researchers_research_area ON researchers(research_area);

-- Publications
CREATE INDEX idx_publications_year ON publications(year);
CREATE INDEX idx_publications_research_area ON publications(research_area);

-- Funding
CREATE INDEX idx_innovation_grant_institute ON innovation_grant_from_govt(institute);
CREATE INDEX idx_innovation_grant_year ON innovation_grant_from_govt(year_of_receiving);
```

### 8.2 Vacuum and Analyze

Run PostgreSQL maintenance:

```bash
psql -c "VACUUM ANALYZE;"
psql -c "SELECT pg_stat_reset();"
```

### 8.3 Backup

Create encrypted backup after successful load:

```bash
pg_basebackup -Ft -Db nrg -U postgres -Pw -D /backup/pre-prod-$(date +%Y%m%d)/
gpg --encrypt --recipient gov@example.com /backup/pre-prod-*.tar
```

### 8.4 Notification

Send completion notification:

```
DATA_INTAKE_COMPLETE:
  Source: MHRD/NIC
  Total rows: 6,234,567
  Duration: 48 hours
  Status: SUCCESS
  Next: Dhairya benchmark validation
```

---

## 9. Dhairya Benchmark Validation

After data load, run the Dhairya SQL benchmark to verify data fitness:

```bash
python scripts/benchmark_dhairya_queries.py --url postgresql://...
```

Expected: All 17 queries should execute without errors.

Current SQL accuracy: 41% (improved by proper data loading)

Target: ≥ 85% accuracy after full data load and query fixes.

---

## 10. Rollback Procedures

### 10.1 If Loading Fails Mid-Way

```bash
# Stop all loading
pkill -f "COPY researchers"

# Verify current state
SELECT COUNT(*) FROM researchers;

# If partial, restore from pre-load backup
pg_restore -d nrg pre_load_backup.dump

# Or drop all tables and restart
psql -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### 10.2 If Data Quality Issues Found After Load

```bash
# Quarantine affected rows
UPDATE researchers SET quarantine = true WHERE invalid_condition = true;

# Generate quarantine report
SELECT * FROM researchers WHERE quarantine = true;

# Manual review before cleanup
```

---

## 11. Security Controls

### 11.1 Access Control

- Only `nrg_intake` service account can write to intake directory
- Database loading uses `nrg_load` role with INSERT-only permissions
- Production read access requires `nrg_reader` role with audit logging

### 11.2 Audit Trail

Every data operation logged:

```python
{
    "event": "DATA_LOAD",
    "table": "researchers",
    "rows": 500000,
    "user": "nrg_load",
    "timestamp": "2026-04-24T14:30:00Z",
    "ip_address": "10.0.1.50",
    "session_id": "sess_abc123"
}
```

### 11.3 Data Residency Confirmation

Confirm data never left Indian infrastructure:

```python
def verify_data_residency():
    """Verify all data operations within Indian region."""
    # Log all network operations
    # Verify no egress to foreign IPs
    # Confirm all storage in Indian DCs
    pass
```

---

## 12. Contacts and Escalation

| Role | Contact | Escalation |
|------|---------|------------|
| Data Intake Lead | ops@nrg.in | guru@nrg.in |
| Database Admin | dba@nrg.in | guru@nrg.in |
| Security Officer | security@nrg.in | guru@nrg.in |

---

*End of DATA_INTAKE_PROTOCOL.md*
