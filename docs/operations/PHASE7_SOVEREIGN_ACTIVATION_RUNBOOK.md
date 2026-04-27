# Phase 7 Sovereign Activation Runbook

**Date:** 2026-04-27  
**Scope:** P7-A through P7-H execution on the sovereign IIT-GN cluster.  
**Status:** Repo-ready, live execution blocked until Kubernetes context, DNS/TLS, secrets, and official data bundles are available.

## Prerequisites

- `kubectl config current-context` points to the sovereign cluster.
- Helm 3 is installed on the operator machine.
- DNS points `api.nrg.iitgn.ac.in` to the Kong ingress.
- Vault or Kubernetes secrets contain DB, JWT, HMAC, GPG, and service-token material.
- Official intake bundle is present under `/data/intake/2026-05-xx/` with `manifest.json`, `.asc` or `.sig` sidecars, and `row_hmac` columns for CSV rows.

## P7-A Cluster Provision

```bash
python infrastructure/helm/nrg/scripts/validate_chart.py --skip-helm
helm lint infrastructure/helm/nrg
kubectl create namespace nrg-production --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install nrg infrastructure/helm/nrg \
  -n nrg-production \
  -f infrastructure/helm/nrg/values.prod.yaml \
  --wait --atomic --timeout 15m
curl -fsS https://api.nrg.iitgn.ac.in/health
```

Acceptance: `/health` returns HTTP 200, `database.table_count >= 75`, and all critical pods are Ready.

## P7-B 600 GB Data Ingest

```bash
export DATA_INTAKE_HMAC_SECRET="$(vault kv get -field=row_hmac secret/nrg/intake)"
python scripts/verify_intake_bundle.py \
  --bundle-dir /data/intake/2026-05-xx \
  --manifest /data/intake/2026-05-xx/manifest.json
python scripts/seed_from_csvs.py --rebuild --csv-dir /data/intake/2026-05-xx/csv
python scripts/build_qdrant_index.py
```

Acceptance: manifest file count, SHA-256, GPG signatures, and row HMACs pass; all 75 target tables are populated; `/health.database.table_count` and table row counts match the ingestion manifest.

## P7-C Vector Baseline And Drift Cron

```bash
python scripts/vector_drift_check.py --establish-baseline --json
kubectl -n nrg-production get cronjob nrg-vector-drift-lightweight nrg-vector-drift-deep
curl -fsS https://api.nrg.iitgn.ac.in/health | jq '.vector_drift'
```

Acceptance: `vector_drift.status == "healthy"`. The Helm chart now includes:

- `nrg-vector-drift-lightweight`: every 5 minutes, `--check-only --json`
- `nrg-vector-drift-deep`: nightly at 02:30, `--json`

## P7-D C4 1000-User Locust Run

```bash
mkdir -p evidence/2026-05-xx/C4_1000_user_locust
uv run locust -f tests/performance/locustfile_c4.py \
  --headless \
  --users 1000 \
  --spawn-rate 3.33 \
  --run-time 15m \
  --host https://api.nrg.iitgn.ac.in \
  --html evidence/2026-05-xx/C4_1000_user_locust/report.html \
  --csv evidence/2026-05-xx/C4_1000_user_locust/stats
```

Acceptance: p50 < 500 ms, p99 < 3 s, error rate < 1%, throughput >= 100 RPS, and request count > 0.

## P7-E UAT x 3 Personas

Use `docs/uat/UAT_SCRIPT_T1_RESEARCHER.md`, `docs/uat/UAT_SCRIPT_T2_GOVERNMENT.md`, and `docs/uat/UAT_SCRIPT_T3_INDUSTRY.md`.

Evidence paths:

- `evidence/2026-05-xx/uat_transcript_researcher.md`
- `evidence/2026-05-xx/uat_transcript_government.md`
- `evidence/2026-05-xx/uat_transcript_industry.md`

Acceptance: all three testers sign off; Tier 2 sees aggregates without PII; Tier 3 sees anonymized results capped at 100.

## P7-F Live Red Team

```bash
API_URL=https://api.nrg.iitgn.ac.in \
python scripts/red_team_live_replay.py --api-url https://api.nrg.iitgn.ac.in
```

Acceptance: at least 121 payload attempts, all blocked or downgraded; attach `evidence/2026-05-xx/lb5_red_team_sovereign.md`.

## P7-G DR Dry Run And Chaos

```bash
bash infrastructure/sovereign/disaster_recovery.sh assess "phase7-dr-drill"
kubectl -n nrg-production delete pod -l app=nrg-api
kubectl -n nrg-production rollout status deploy/nrg-api --timeout=60s
python scripts/audit_rebuild.py --verify
```

Acceptance: API replacement pod is Ready in under 60 seconds, PostgreSQL failover is verified by the operator, and audit rebuild returns a valid chain.

## P7-H Chain Seal And GPG Signatures

```bash
python scripts/audit_rebuild.py --verify
python scripts/pre_tag_checklist.py
gpg --detach-sign docs/handover/evidence/01_stage_up.json
gpg --detach-sign docs/handover/evidence/02_load_report.md
gpg --detach-sign docs/handover/evidence/03_uat_t1.md
gpg --detach-sign docs/handover/evidence/03_uat_t2.md
gpg --detach-sign docs/handover/evidence/03_uat_t3.md
gpg --detach-sign docs/handover/evidence/04_demo.sha256
gpg --detach-sign docs/handover/SECURITY_COMPLIANCE_ATTESTATION.md
gpg --detach-sign docs/handover/UAT_RESULTS.md
git tag -s v1.0.0-eternal -m "NRG sovereign eternal seal"
git push nrg v1.0.0-eternal
```

Current blocker: `v1.0.0-eternal` already exists as an unsigned lightweight tag on an older commit. Do not retag it until P7-A through P7-G evidence is present and the founder approves replacing or superseding it.
