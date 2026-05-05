# D4-06 / D4-08 Partition and Index Report

## Time-Series Tables

| Table | Exists | Partitioned | Child partitions |
|---|---|---|---:|
| `audit_events` | True | True | 3 |
| `query_logs` | False | False | 0 |

## Hot-Path Timings

| Query | Status | Elapsed ms | Result |
|---|---|---:|---:|
| `researchers_state` | PASS | 2.317 | 0 |
| `researchers_area` | PASS | 56.092 | 0 |
| `publications_year` | PASS | 4.687 | 10000 |
| `audit_events_recent` | PASS | 6.021 | 807 |

## Index Counts

| Table | Index count |
|---|---:|
| `researchers` | 11 |
| `publications` | 8 |
| `funding_records` | 5 |
| `labs` | 3 |
| `projects` | 6 |
| `patents` | 4 |
| `collaborations` | 6 |
| `research_documents` | 4 |
| `audit_events` | 4 |

## Partition Pruning

- Status: PASS
- Relations in plan: audit_events_2026
