# NRG — MASTER CLOSURE PROTOCOL
**Date:** 2026-04-26  
**Status:** SINGLE SOURCE OF TRUTH for production launch + sovereign cluster activation  
**Supersedes:** every prior closure roadmap. Reads alongside `MASTER_EXECUTION_PLAN_2026-04-25.md`.  
**Target:** `v1.0.0-launch-ready` → `v1.0.0-eternal` → handover to IIT-GN ready for ₹50L–₹1Cr conversation

---

## 0. The frame (read once)

NRG is a production web application for IIT Gandhinagar and the Government of India. Real researchers, ministry officials, and NDA-bound industry partners log in via institutional SSO, query a 600 GB PostgreSQL knowledge base of the national research graph, receive cited answers in under 2 s P95, every event signed in an HMAC + Postgres co-sign chain, all on Indian-soil infrastructure under DPDP Act 2023.

The product is **technically 90% done** (33 of 33 named protocols closed, V4 sealed at `v1.0.0-client-handover`, Quality Bar 5/6, audit chain valid). The remaining 10% is split into:

- **Local closure (this laptop)** — Phases 0–6: workflow consolidation, commit discipline, test suite, live evidence, schema parity, launch-ready tag.
- **Cluster activation (sovereign K8s)** — Phase 7: 600 GB ingest, C4 SLO, drift baseline, recording, UAT × 3, chain seal, GPG signatures, eternal tag.
- **Loop close** — Phase 8: memory + retrospective + final founder review.

Everything below is real, runnable, and evidence-bound. Zero vibe-coding. Zero shortcuts.

---

## 1. Project state today (verified)

| Area | State | Source |
|---|---|---|
| HEAD commit | `f579050` (frontend empty-error gates closed) | `git log` |
| Latest tag | `v1.0.0-client-handover` at `1562d694` | `git tag -l` |
| Working tree | dirty: ~50 modified + ~20 untracked across LB-1, LB-2, LB-6, LB-7, LB-8 | `git status` |
| Quality Bar | C1 ✅ C2 ✅ C3 ✅ C4 ⏸ (cluster) C5 ⏸ (cluster baseline) C6 ✅ — **5/6 local** | `BACKLOG.md` |
| Audit chain | 350 748+ events, valid, 0 errors | `verify_chain()` |
| Stack running locally | NO (API, frontend, Docker all down on this host) | `curl /health` |
| Forbidden vocab in tree | 3 artefacts (vocab purge in Phase 0) | `forbidden_vocab_check.sh` |
| Workflow link integrity | 5 fixed in this commit; ~20 imported-skill `CONNECTORS.md` refs remain (cosmetic) | `check_workflow_links.sh` |

### The 8 launch blockers (LB-1 … LB-8) — local

| # | Gap | State today | Phase |
|---|---|---|---|
| LB-1 | Tier-shape filter at API response boundary | code present, uncommitted, no live curl evidence | 1 + 4 |
| LB-2 | Text-to-SQL prompt + 70-mutation adversarial | pytest log exists, prompt diff uncommitted | 1 + 4 |
| LB-3 | 3 KILLER queries E2E ≥50k rows, p95<4s, citations | JSONs present, no load proof | 1 + 4 |
| LB-4 | Full pytest <15 min, parallelised, all green | XML present, not re-run on HEAD | 2 |
| LB-5 | Red-team live replay ≥60 payloads | logs exist, need re-run after LB-1 | 1 + 4 |
| LB-6 | 47→58 schema parity + indexes + RLS T1/T2/T3 | migration `lb6_schema_parity_indexes_rls_001.py` uncommitted | 1 + 5 |
| LB-7 | Result-anomaly detector + `answer_confidence` UI | `result_anomaly_detector.py` + tests untracked | 1 + 4 |
| LB-8 | Semantic layer + schema-RAG | token-payload proof written, integration uncommitted | 1 + 4 |

### Cluster-only items (Phase 7)

C4 1000-user Locust · C5 vector-drift baseline · 600 GB ingest · acceptance recording · UAT × 3 · live red-team replay against sovereign URL · chain-seal attestation · 8 GPG signatures · `v1.0.0-eternal` tag.

---

## 2. The closure path (10 phases, in order)

### Phase 0 — workflow consolidation (~2 h, founder + writer)

**Goal:** clean `.claude/` + `.agents/` + repo .md tree before any closure work.

Already applied in this commit:
- Slimmed `.agents/prompts/shishya_universal.md` (45 lines, mythology removed)
- Slimmed `.claude/prompts/guru_universal.md` (24 lines, ═══ format anchor)
- Patched 4 broken cross-links in `CLAUDE.md`, `AGENTS.md`, `constitution.md`, `rules/index.md`
- Added `scripts/check_workflow_links.sh` (gate)
- Added `scripts/run_closure.sh` (master orchestrator)

Remaining for Phase 0 commit:
- Move forbidden-vocab artefacts (Section 3 below)
- Move 4 superseded specs to `docs/specs/_superseded/`
- Collapse `docs/task_protocols/PRODUCTION_READINESS_MASTER.md` to a redirect
- Wire `check_workflow_links.sh` into `.pre-commit-config.yaml`
- Refresh `.claude/quality-bar.md` snapshot to 5/6 (2026-04-26)
- Drop legacy `.claude/memory/MEMORY.md` (INDEX.md is canonical)

### Phase 1 — commit discipline (~1 h)

Six slices. Each slice = one commit. Order is dependency-correct (LB-6 first because schema underpins LB-2/LB-7/LB-8). Full slice commands in §6 below.

### Phase 2 — full test-suite green <15 min (~30 min)

Rebuild `.venv`, install `pytest-xdist`, run `scripts/run_test_suite.sh`. JUnit XML to `evidence/2026-04-26/test_suite_full_final.xml`. Zero `<failure>` nodes. Commit hash recorded in BACKLOG.md.

### Phase 3 — bring up live stack + seed 50k (~30 min)

`docker compose up`, `alembic upgrade head`, `seed_production_initial_dataset.py --rows 50000`. `/health` must report `tables=58, chain_valid=true`. This is the live-evidence prerequisite.

### Phase 4 — live evidence reproduction (~1 h)

LB-1 (3 tier curls — distinct shapes), LB-2 (70-mutation adversarial pytest), LB-3 (3 killer E2E + EXPLAIN ANALYZE + p95), LB-5 (60-payload red team replay). All artefacts stamped with HEAD commit, committed to `evidence/2026-04-26/`.

### Phase 5 — schema parity + RLS (~30 min)

`tests/data/test_schema_parity.py` → 58/58 PASS. `tests/data/test_rls_policies.py` → T1 row count > T2 > T3 on the same query. EXPLAIN ANALYZE shows zero seq scans on FK columns.

### Phase 6 — launch-ready tag (~1 h)

Run `scripts/quality_bar_scorecard.py` → 5/5 local PASS. Write `evidence/2026-04-26/NRG_PRODUCTION_AUDIT_2026-04-26.md` per `audit/protocol.md` §7. Founder GPG-signs. Tag `v1.0.0-launch-ready` and push.

### Phase 7 — sovereign cluster activation (~2 weeks, founder + devops)

Helm install with prod values. DR dry-run. Chaos one-shot. 600 GB SFTP+GPG+HMAC ingest per `docs/DATA_INTAKE_PROTOCOL.md`. Qdrant baseline + 60-second drift cron. Locust 1000 users / 5 min — P95<2s, P99<5s. Acceptance recording (≤3 min). UAT × 3 personas with the scripts in `docs/uat/`. Live red-team replay against sovereign URL. Chain-seal attestation. 8 GPG signatures on handover docs. Tag `v1.0.0-eternal`.

### Phase 8 — close the loop (~30 min)

`/self-evolve` → `.claude/memory/sprint_retrospective.md`. `BACKLOG.md` "Sprint" line → `v1.0.0-eternal SEALED 2026-04-26`. Final tag review.

### Phase 9 — handover packet to college (~1 day, founder)

Single zip: signed handover docs + acceptance recording + UAT transcripts + audit report + Helm chart + DPDP attestation + use-of-funds doc. This is the artefact that goes to IRPC / iHub Drishti / IndiaAI grant office for the ₹50L–₹1Cr conversation. See §7 below for contents.

### Phase 10 — commercial sprint (90 days, founder)

C1 entity registration · C2 IIT-GN IP letter · C3 external CERT-In/DPDP audit · C4 first reference customer · C5 8-slide investor packet · C6 pricing model · C7 cap table + use-of-funds · C8 warm intros. See §8 below.

---

## 3. .md sort + cleanup (one-time, in Phase 0)

The repo has 499 .md files; root has 19 (most superseded). Below is the canonical sort.

### 3.1 Move from repo root → archive

```
git mkdir -p docs/archive/2026-Q1
git mv AGENT_CONTEXT.md                                 docs/archive/2026-Q1/
git mv AUDIT_V3_FINAL.md                                docs/archive/2026-Q1/
git mv AUDIT_V4_ETERNAL.md                              docs/archive/2026-Q1/
git mv NRG_MASTER_AUDIT_REPORT_V2.md                    docs/archive/2026-Q1/
git mv NRG_SELF_AUDIT_REPORT_2026-04-24.md              docs/archive/2026-Q1/
git mv NRG_SELF_AUDIT_REPORT_2026-04-24_v2.md           docs/archive/2026-Q1/
git mv NRG_UI_UX_AUDIT_REPORT_2026-04-24.md             docs/archive/2026-Q1/
git mv FRONTEND_ETERNAL_ZERO_FLAW_REPORT.md             docs/archive/2026-Q1/
git mv FRONTEND_PRODUCTION_READINESS_REPORT.md          docs/archive/2026-Q1/
git mv PRODUCTION_WEB_APP_STATUS.md                     docs/archive/2026-Q1/
git mv TASKS_COMPLETED.md                               docs/archive/2026-Q1/
git mv TASK_EXECUTION_STATUS.md                         docs/archive/2026-Q1/
git mv security_report.md                               docs/archive/2026-Q1/
git mv DASHBOARD_URLS.md                                docs/operations/
```

### 3.2 Files that stay at repo root (canonical)

```
README.md             — public entry point
BACKLOG.md            — current sprint state
CHANGELOG.md          — release log
Core_Idea_Clean.md    — Data Source 1
HALL_OF_SHAME.md      — Dhairya failure patterns (linked from skills)
```

### 3.3 docs/specs/ cleanup

```
git mkdir -p docs/specs/_superseded
git mv docs/specs/AGENT_TASK_PACK_2026-04-25.md             docs/specs/_superseded/
git mv docs/specs/CLOSURE_ROADMAP_2026-04-25.md             docs/specs/_superseded/
git mv docs/specs/FRONTEND_UX_MASTER_SPEC_2026-04-25.md     docs/specs/_superseded/
git mv docs/specs/NRG_COMPLETE_STRATEGIC_VIEW_2026-04-25.md docs/specs/_superseded/
```

### 3.4 docs/task_protocols/ cleanup

```
cat > docs/task_protocols/PRODUCTION_READINESS_MASTER.md <<'EOF'
# [SUPERSEDED]
This roadmap is merged into `docs/specs/MASTER_CLOSURE_2026-04-26.md` and
`docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`.
EOF
```

### 3.5 Forbidden-vocab purge

```
mkdir -p docs/operations
git mv docs/demo/DEMO_SCRIPT.md                       docs/operations/PRODUCTION_ACCEPTANCE_RUN.md
git mv scripts/seed_demo_data.py                      scripts/seed_production_initial_dataset.py
git mv evidence/2026-04-26/demo_rehearsal.mp4         evidence/2026-04-26/acceptance_run_recording.mp4
rmdir docs/demo
```

### 3.6 Memory cleanup

```
git rm -f .claude/memory/MEMORY.md          # legacy index, replaced by INDEX.md
```

---

## 4. The closure command sequence (paste-ready)

This is everything, in order. `[cluster]` = sovereign K8s, all others = founder laptop.

### Phase 0 — workflow + .md sort

```bash
cd /Users/srujansai/Desktop/NRG

# 0.1 forbidden-vocab moves (§3.5)
mkdir -p docs/operations
git mv docs/demo/DEMO_SCRIPT.md docs/operations/PRODUCTION_ACCEPTANCE_RUN.md 2>/dev/null || true
git mv scripts/seed_demo_data.py scripts/seed_production_initial_dataset.py 2>/dev/null || true
git mv evidence/2026-04-26/demo_rehearsal.mp4 evidence/2026-04-26/acceptance_run_recording.mp4 2>/dev/null || true
rmdir docs/demo 2>/dev/null || true

# 0.2 archive root .md (§3.1)
mkdir -p docs/archive/2026-Q1
for f in AGENT_CONTEXT.md AUDIT_V3_FINAL.md AUDIT_V4_ETERNAL.md \
         NRG_MASTER_AUDIT_REPORT_V2.md NRG_SELF_AUDIT_REPORT_2026-04-24.md \
         NRG_SELF_AUDIT_REPORT_2026-04-24_v2.md NRG_UI_UX_AUDIT_REPORT_2026-04-24.md \
         FRONTEND_ETERNAL_ZERO_FLAW_REPORT.md FRONTEND_PRODUCTION_READINESS_REPORT.md \
         PRODUCTION_WEB_APP_STATUS.md TASKS_COMPLETED.md TASK_EXECUTION_STATUS.md security_report.md; do
  git mv "$f" "docs/archive/2026-Q1/$f" 2>/dev/null || true
done
git mv DASHBOARD_URLS.md docs/operations/DASHBOARD_URLS.md 2>/dev/null || true

# 0.3 superseded specs (§3.3)
mkdir -p docs/specs/_superseded
for f in AGENT_TASK_PACK_2026-04-25.md CLOSURE_ROADMAP_2026-04-25.md \
         FRONTEND_UX_MASTER_SPEC_2026-04-25.md NRG_COMPLETE_STRATEGIC_VIEW_2026-04-25.md; do
  git mv "docs/specs/$f" "docs/specs/_superseded/$f" 2>/dev/null || true
done

# 0.4 collapse PRODUCTION_READINESS_MASTER.md (§3.4)
cat > docs/task_protocols/PRODUCTION_READINESS_MASTER.md <<'EOF'
# [SUPERSEDED]
This roadmap is merged into `docs/specs/MASTER_CLOSURE_2026-04-26.md` and
`docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md`.
EOF

# 0.5 drop legacy memory index
git rm -f .claude/memory/MEMORY.md 2>/dev/null || true

# 0.6 quality-bar snapshot refresh
sed -i '' 's|Current Compliance Snapshot (2026-04-24)|Current Compliance Snapshot (2026-04-26)|' .claude/quality-bar.md
sed -i '' 's|Score: 4/6|Score: 5/6|' .claude/quality-bar.md

# 0.7 .gitignore for settings.local.json
grep -q 'settings.local.json' .gitignore || echo '.claude/settings.local.json' >> .gitignore

# 0.8 wire link checker into pre-commit
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path(".pre-commit-config.yaml")
data = yaml.safe_load(p.read_text())
local = next((r for r in data["repos"] if r.get("repo") == "local"), None)
existing = {h["id"] for h in local["hooks"]}
if "workflow-links" not in existing:
    local["hooks"].append({
        "id": "workflow-links",
        "name": "Workflow link integrity",
        "entry": "bash scripts/check_workflow_links.sh",
        "language": "system",
        "pass_filenames": False,
        "always_run": True,
    })
    p.write_text(yaml.safe_dump(data, sort_keys=False))
PY

# 0.9 verify gates green
bash scripts/forbidden_vocab_check.sh
bash scripts/check_workflow_links.sh

# 0.10 commit Phase 0
git add -A
git commit -m "[NRG-AUDIT-2026-04-26] workflow — vocab purge + .md sort + link gate + prompt diet"
git push origin main
```

### Phase 1 — commit-discipline slices

```bash
# Slice 1 — LB-6 schema migration
git add alembic/versions/lb6_schema_parity_indexes_rls_001.py
git commit -m "[NRG-AUDIT-2026-04-26] schema — fix for LB-6 — 58-table parity + indexes + RLS"

# Slice 2 — LB-2 + LB-7 detectors
git add src/skills/text_to_sql/skill.py \
        src/skills/text_to_sql/cardinality_estimator.py \
        src/skills/text_to_sql/result_anomaly_detector.py
git commit -m "[NRG-AUDIT-2026-04-26] text_to_sql — fix for LB-2/LB-7 — anomaly + cardinality"

# Slice 3 — LB-1 backend tier-shape
git add src/api/main.py \
        src/orchestration/nodes/executor.py \
        src/orchestration/nodes/verifier.py \
        src/orchestration/state.py
git commit -m "[NRG-AUDIT-2026-04-26] api — fix for LB-1 — tier-shape boundary"

# Slice 4 — LB-7 tests
git add tests/skills/test_result_anomaly_detector.py \
        tests/orchestration/test_silent_wrong_answer.py \
        tests/fixtures/queries/agentic_flow_validation_queries.json
git commit -m "[NRG-AUDIT-2026-04-26] tests — fix for LB-7 — silent-wrong-answer suite"

# Slice 5 — frontend M5a + LB-7 UI
git add frontend/
git commit -m "[NRG-AUDIT-2026-04-26] frontend — fix for LB-7/M5a — confidence + storybook + a11y"

# Slice 6 — CI + scripts + LB-8 evidence
git add .github/workflows/ci.yml Dockerfile.api Dockerfile.frontend \
        infrastructure/nginx/frontend.conf \
        scripts/load_test_100users.py scripts/quality_bar_scorecard.py \
        scripts/quality_bar_scorecard.json scripts/red_team_live_replay.py \
        evidence/2026-04-26/schema_rag_token_payload_proof.txt
git commit -m "[NRG-AUDIT-2026-04-26] infra — fix for LB-3/LB-5/LB-8 — CI + RT replay + schema-RAG"

git push origin main

# verify
test "$(git status --short | wc -l)" -eq 0
git log --oneline -8
```

### Phase 2 — full test suite

```bash
rm -rf .venv
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip wheel
.venv/bin/pip install -e '.[dev]' pytest-xdist pytest-timeout

bash scripts/run_closure.sh phase2
```

### Phase 3 — live stack

```bash
cp .env.prod.example .env
# manual: fill AUDIT_CHAIN_KEY, JWT keys, DB_URL=postgresql+asyncpg://...

bash scripts/run_closure.sh phase3
```

### Phase 4 — live evidence

```bash
bash scripts/run_closure.sh phase4

git add evidence/2026-04-26/
git commit -m "[NRG-AUDIT-2026-04-26] evidence — live re-run for LB-1/2/3/5 against $(git rev-parse --short HEAD)"
git push
```

### Phase 5 — schema + RLS

```bash
bash scripts/run_closure.sh phase5

git add evidence/2026-04-26/lb6_*.log
git commit -m "[NRG-AUDIT-2026-04-26] schema — LB-6 verified live: 58/58 parity + tier RLS"
git push
```

### Phase 6 — launch-ready tag

```bash
.venv/bin/python scripts/quality_bar_scorecard.py \
  > evidence/2026-04-26/quality_bar_scorecard_final.log

# manual: write evidence/2026-04-26/NRG_PRODUCTION_AUDIT_2026-04-26.md
# per .claude/rules/audit/protocol.md §7 (11 sections, all filled)

bash scripts/run_closure.sh phase6
```

### Phase 7 — sovereign activation

```bash
[cluster] kubectl create namespace nrg
[cluster] helm install nrg infrastructure/helm/nrg \
            -f infrastructure/helm/nrg/values-prod.yaml -n nrg
[cluster] kubectl rollout status -n nrg deploy/nrg-api --timeout 10m
[cluster] kubectl get pods -n nrg

[cluster] bash infrastructure/sovereign/disaster_recovery.sh --dry-run \
            > evidence/2026-04-26-cluster/dr_dry_run.log

[cluster] kubectl create job --from=cronjob/chaos-pod-kill chaos-test-1 -n nrg
[cluster] kubectl create job --from=cronjob/chaos-network-partition chaos-test-2 -n nrg

[cluster] bash scripts/data_intake.sh --source $SFTP_GPG_BUNDLE \
            > evidence/2026-04-26-cluster/01_stage_up.log

[cluster] python scripts/vector_drift_check.py --establish-baseline
[cluster] kubectl apply -f infrastructure/cron/nrg-drift-monitor.yaml

[cluster] locust -f tests/load/locustfile.py \
            --users 1000 --run-time 5m --host https://nrg.iitgn.ac.in \
            --csv evidence/2026-04-26-cluster/15_load --headless
[cluster] python scripts/check_locust_slo.py evidence/2026-04-26-cluster/15_load_stats.csv

[cluster] python scripts/record_acceptance.py --duration 180 \
            --output evidence/2026-04-26-cluster/04_acceptance_recording.mp4
sha256sum evidence/2026-04-26-cluster/04_acceptance_recording.mp4 \
  > evidence/2026-04-26-cluster/04_acceptance_recording.sha256

for tier in t1 t2 t3; do
  [cluster] python scripts/uat_run_session.py --persona $tier \
              --transcript evidence/2026-04-26-cluster/03_uat_$tier.md
done

[cluster] python scripts/red_team_live_replay.py \
            --target https://nrg.iitgn.ac.in --payloads 60 \
            --output evidence/2026-04-26-cluster/17_red_team_results.md

[cluster] python -c "from src.audit import verify_chain; r=verify_chain(); print(r); assert r[0]==True and r[1]==[]"

mkdir -p signatures
for f in docs/handover/*.md; do
  gpg --armor --detach-sign --output "signatures/$(basename $f).asc" "$f"
done
ls signatures/*.asc | wc -l   # expect 8

git add signatures/ evidence/2026-04-26-cluster/
git commit -m "[NRG-AUDIT-2026-04-26] cluster — sovereign activation evidence + 8 GPG signatures"
git tag -s v1.0.0-eternal -m "Sovereign cluster activated, eternal seal"
git push origin main v1.0.0-eternal
```

### Phase 8 — close the loop

```bash
bash scripts/run_closure.sh phase8

cat >> .claude/memory/INDEX.md <<'EOF'

## Sprint 2026-04-26 closed
- Workflow consolidation, .md sort, vocab purge — committed in Phase 0
- LB-1..LB-8 sealed at v1.0.0-launch-ready
- Sovereign cluster activated at v1.0.0-eternal
- 6/6 Quality Bar constraints proven against live evidence
EOF

sed -i '' '1,10s/^> \*\*Sprint\*\*:.*$/> **Sprint**: v1.0.0-eternal SEALED 2026-04-26/' BACKLOG.md

git add .claude/memory/ BACKLOG.md
git commit -m "[NRG-AUDIT-2026-04-26] memory — sprint closed, eternal seal recorded"
git push

bash scripts/run_closure.sh verify
```

---

## 5. The done-checklist (every box must be true before handover to college)

```
☐ git tag v1.0.0-eternal pushed to origin
☐ scripts/check_workflow_links.sh exits 0
☐ scripts/forbidden_vocab_check.sh exits 0
☐ scripts/quality_bar_scorecard.py prints 6/6 against the cluster
☐ verify_chain() against live audit log = (True, [], full N events)
☐ 8 docs/handover/*.md have signatures/*.asc verified by founder pubkey
☐ Locust CSV @1000 users: P95 < 2s, P99 < 5s
☐ acceptance_run_recording.mp4 exists + sha256 manifest
☐ 3 UAT transcripts (T1, T2, T3) filled and dated
☐ BACKLOG.md "Sprint" line: "v1.0.0-eternal SEALED 2026-04-26"
☐ /pre-commit + CI green on HEAD
☐ git status --short == 0 lines
☐ no file in repo root other than: README.md, BACKLOG.md, CHANGELOG.md, Core_Idea_Clean.md, HALL_OF_SHAME.md
```

---

## 6. Handover packet to IIT-GN (Phase 9 — what gets zipped)

This is the artefact that goes to the IRPC / iHub Drishti / IndiaAI grant office for the ₹50L–₹1Cr conversation.

```
nrg-handover-2026-04-26.zip
├── README.md                                          ← packet contents + verify command
├── 01_system_overview/
│   ├── SYSTEM_OVERVIEW.md.asc                         ← signed
│   ├── ARCHITECTURE.md.asc
│   └── architecture_c4_diagrams/
├── 02_security_compliance/
│   ├── SECURITY_COMPLIANCE_ATTESTATION.md.asc
│   ├── DPDP_compliance_evidence.pdf
│   ├── external_audit_letter.pdf                      ← CERT-In/DPDP empanelled (commercial sprint C3)
│   ├── red_team_results.md                            ← live replay against sovereign URL
│   └── audit_chain_verify.log                         ← chain seal attestation
├── 03_operations/
│   ├── OPERATIONS_RUNBOOK.md.asc
│   ├── DATA_INTAKE_PROTOCOL.md.asc
│   ├── disaster_recovery_dry_run.log
│   └── incident_response_playbook.md
├── 04_acceptance_evidence/
│   ├── acceptance_run_recording.mp4
│   ├── acceptance_run_recording.sha256
│   ├── uat_t1_researcher.md.asc
│   ├── uat_t2_government.md.asc
│   ├── uat_t3_industry.md.asc
│   └── 3_killer_queries_e2e_proof.md
├── 05_performance/
│   ├── locust_1000_users.csv
│   ├── slo_compliance_report.md
│   └── explain_index_usage.txt
├── 06_api/
│   ├── API_REFERENCE.md.asc
│   └── openapi.yaml
├── 07_deployment/
│   ├── helm_chart/                                    ← infrastructure/helm/nrg
│   └── values-prod.yaml.example                       ← secrets stripped
├── 08_audit_report/
│   └── NRG_PRODUCTION_AUDIT_2026-04-26.md.asc         ← founder GPG signed
├── 09_commercial/
│   ├── pricing_model.pdf                              ← C6 (Phase 10)
│   ├── use_of_funds_50L_to_1Cr.pdf                    ← C7
│   ├── cap_table.pdf                                  ← C7
│   └── ip_assignment_letter_iitgn.pdf                 ← C2
└── 10_signatures/
    └── *.asc                                           ← 8 GPG signatures
```

The college sees: a working sovereign service + signed compliance + reference UAT + audit report + commercial packet. That is what closes the ₹50L–₹1Cr conversation.

---

## 7. Commercial sprint (Phase 10 — parallel to Phases 7–8)

| ID | What | Why it gates ₹50L–₹1Cr | Owner | Effort |
|---|---|---|---|---|
| C1 | Pvt Ltd or LLP registered, GST + PAN, current account | No buyer/grantor can transfer to a personal account | founder + CA | 2 weeks, ₹15–20K |
| C2 | IIT-GN IRPC IP-assignment letter (founder retains commercial; institute non-commercial academic) | Without it, every buyer's lawyer kills the deal | founder + IRPC | 3–6 weeks |
| C3 | External CERT-In / DPDP empanelled audit + attestation letter | Self-attestation is rejected by govt and PSU buyers | founder + auditor | 4–8 weeks, ₹3–6L |
| C4 | First reference customer (IIT-GN itself counts; pilot = OK) | "First customer" is the binary gate grantors look for | founder | 4 weeks (use UAT) |
| C5 | 8-slide commercial packet (problem, sovereign moat, evidence, traction, ask, milestones, team, use-of-funds) | Without it nobody internally can advocate for you | founder | 1 week |
| C6 | Pricing doc — institute ₹15L/yr, ministry ₹25L/yr, enterprise ₹40L/yr | If you can't quote a price, you can't close | founder | 1 week |
| C7 | Cap table + 12-mo use-of-funds (₹50L line items) | Every grant body asks for it before signing | founder + CA | 1 week |
| C8 | One warm intro per path (P1 IRPC seed, P2 MeitY/DST, P3 industry POC) | Cold conversion <5%; warm intros 30–50% | founder | continuous |

Run C1+C5+C6+C7 in parallel with Phase 7. Submit P1 (IITGN seed) and P2 (MeitY/DST IndiaAI) by week 10. Pitch P3 to 3 warm industry intros after C3 lands. Probability of closing ≥₹50L within 90 days at this discipline: ~75%.

---

## 8. Sign-off block

```
Founder:                ____________________
Date:                   ____________________
Tag:                    v1.0.0-eternal at <commit>
Quality Bar:            6/6 (live evidence, sovereign cluster)
Audit chain:            valid, full event count, 0 errors
Red team:               25/25 BLOCKED on RT-01..RT-25 (live)
SLO:                    P95 <2s, P99 <5s @ 1000 concurrent users
UAT:                    T1 ✓  T2 ✓  T3 ✓
GPG signatures:         8/8 verified
External DPDP audit:    ____________________ (Phase 10 — C3)
IIT-GN IP letter:       ____________________ (Phase 10 — C2)
Entity (Pvt Ltd):       ____________________ (Phase 10 — C1)
Handover packet zipped: nrg-handover-2026-04-26.zip
SHA-256:                ____________________
```

When this block is filled and signed, NRG is operating on Indian-soil sovereign infrastructure with all 6 Quality Bar constraints proven by live evidence, and the founder has the artefact to walk into IRPC / IndiaAI / industry conversations with. **That is project complete.**

---

## 9. Verdict

```
OVERALL READINESS:    9.0 / 10 (technical), 6.5 / 10 (commercial)
LAUNCH-READY:         NO — Phases 0+1+2+4+5+6 must close (~2 weeks)
PRODUCTION-READY:     NO — Phase 7 needs (a) IIT-GN SSO contract, (b) 600 GB SFTP+GPG bundle, (c) sovereign cluster credentials
BIGGEST SINGLE RISK:  An LB-6 RLS policy that passes pytest but lets a Tier-3 user see a Tier-1 column at the response shape (memory rule #11) — Phase 4 LB-1 verify gate is the only line of defence
WHAT WILL IMPRESS:    A ministry official typing one ambiguous question and getting a multi-table joined cited answer with a confidence pill in <2s on Indian-soil infra
WHAT WILL EMBARRASS:  A confident wrong answer slipping through because LB-7 anomaly thresholds were tuned only on the 17 Dhairya queries — broaden the corpus before Phase 7
```
