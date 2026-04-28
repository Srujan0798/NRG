#!/bin/bash
# run_closure.sh — master orchestrator for NRG production closure
# from f579050 (today) to v1.0.0-eternal.
#
# Usage:
#   bash scripts/run_closure.sh phase0     # workflow consolidation
#   bash scripts/run_closure.sh phase1     # commit discipline (manual review per slice)
#   bash scripts/run_closure.sh phase2     # full test-suite green
#   bash scripts/run_closure.sh phase3     # bring up live stack + seed 50k
#   bash scripts/run_closure.sh phase4     # live evidence reproduction (LB-1/2/3/5)
#   bash scripts/run_closure.sh phase5     # schema parity + RLS proof (LB-6)
#   bash scripts/run_closure.sh phase6     # launch-ready tag
#   bash scripts/run_closure.sh phase7     # [cluster] sovereign activation (manual on K8s)
#   bash scripts/run_closure.sh phase8     # close the loop (memory + retrospective)
#   bash scripts/run_closure.sh verify     # done-checklist verification
#
# Each phase aborts on the first failure. Read MASTER_CLOSURE_2026-04-26.md.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE=$(date +%Y-%m-%d)
cd "$REPO"

phase0() {
  echo "=== PHASE 0 — workflow consolidation ==="
  bash scripts/forbidden_vocab_check.sh
  bash scripts/check_workflow_links.sh
  test "$(wc -l < .agents/prompts/shishya_universal.md)" -le 50
  test "$(wc -l < .claude/prompts/guru_universal.md)" -le 40
  if ! git diff --cached --quiet || ! git diff --quiet; then
    git add -A
    git commit -m "[NRG-AUDIT-${DATE}] workflow — links + vocab + prompt diet sealed" || true
  fi
  echo "PHASE 0 PASS"
}

phase2() {
  echo "=== PHASE 2 — full test-suite green ==="
  if [ ! -d .venv ]; then
    python3.11 -m venv .venv
    .venv/bin/pip install --upgrade pip wheel
    .venv/bin/pip install -e '.[dev]' pytest-xdist pytest-timeout
  fi
  time bash scripts/run_test_suite.sh
  mkdir -p evidence/${DATE}
  cp .test_artifacts/junit.xml evidence/${DATE}/test_suite_full_final.xml 2>/dev/null || true
  cp .test_artifacts/run.log   evidence/${DATE}/test_suite_full_final.log 2>/dev/null || true
  if grep -q '<failure' evidence/${DATE}/test_suite_full_final.xml; then
    echo "FAIL: test suite has failures"; exit 1
  fi
  echo "PHASE 2 PASS"
}

phase3() {
  echo "=== PHASE 3 — bring up live stack + seed 50k ==="
  test -f .env || { echo "FAIL: .env missing — copy from .env.prod.example and fill secrets"; exit 1; }
  docker compose -f docker-compose.prod.yml up -d
  .venv/bin/alembic upgrade head
  .venv/bin/python scripts/seed_production_initial_dataset.py --rows 50000 || \
    .venv/bin/python scripts/seed_production_tables.py --rows 50000
  curl -fsS http://localhost:8000/health | jq -e \
    '.status=="healthy" and .database.tables==58 and .audit.chain_valid==true'
  echo "PHASE 3 PASS"
}

phase4() {
  echo "=== PHASE 4 — live evidence reproduction (LB-1/2/3/5) ==="
  COMMIT=$(git rev-parse --short HEAD)
  mkdir -p evidence/${DATE}

  for tier in researcher_user gov_user industry_user; do
    TOKEN=$(.venv/bin/python scripts/issue_test_jwt.py --user $tier 2>/dev/null || echo "")
    [ -z "$TOKEN" ] && { echo "WARN: issue_test_jwt failed for $tier"; continue; }
    curl -sS -X POST http://localhost:8000/query \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"question":"Top 5 funding agencies by total grant amount"}' \
      > evidence/${DATE}/live_${tier}.json
  done

  .venv/bin/python -c "
import json, sys
shapes=[]
for t in ['researcher_user','gov_user','industry_user']:
    p=f'evidence/${DATE}/live_{t}.json'
    try:
        d=json.load(open(p))
        rows=d.get('sql_results') or [{}]
        shapes.append(frozenset(rows[0].keys()) if rows else frozenset())
    except Exception as e:
        print(f'WARN: {t}: {e}')
        sys.exit(1)
assert len(set(shapes))==3, f'Tier shapes are not distinct: {shapes}'
print('LB-1 PASS: 3 distinct tier shapes')
"

  .venv/bin/pytest tests/benchmarks/test_dhairya_adversarial.py -v \
    --junitxml=evidence/${DATE}/lb2_adversarial.xml \
    | tee evidence/${DATE}/lb2_adversarial.log

  .venv/bin/pytest tests/e2e/test_three_killer_queries.py -v \
    | tee evidence/${DATE}/lb3_killer_e2e.log

  .venv/bin/python scripts/red_team_live_replay.py \
    --target http://localhost:8000 --payloads 60 \
    --output evidence/${DATE}/lb5_red_team_live.md

  echo "PHASE 4 PASS"
}

phase5() {
  echo "=== PHASE 5 — schema parity + RLS (LB-6) ==="
  .venv/bin/pytest tests/data/test_schema_parity.py -v \
    | tee evidence/${DATE}/lb6_schema_parity.log
  .venv/bin/pytest tests/data/test_rls_policies.py -v \
    | tee evidence/${DATE}/lb6_rls_policies.log
  echo "PHASE 5 PASS"
}

phase6() {
  echo "=== PHASE 6 — launch-ready tag ==="
  .venv/bin/python scripts/quality_bar_scorecard.py \
    > evidence/${DATE}/quality_bar_scorecard_final.log
  test -f evidence/${DATE}/NRG_PRODUCTION_AUDIT_${DATE}.md \
    || { echo "WRITE evidence/${DATE}/NRG_PRODUCTION_AUDIT_${DATE}.md per audit_protocol.md §7 first"; exit 1; }
  gpg --armor --detach-sign evidence/${DATE}/NRG_PRODUCTION_AUDIT_${DATE}.md
  git add evidence/${DATE}/
  git commit -m "[NRG-AUDIT-${DATE}] audit — production audit sealed + GPG-signed"
  git tag -s v1.0.0-launch-ready -m "Launch-ready, sovereign cluster pending"
  git push origin main v1.0.0-launch-ready
  echo "PHASE 6 PASS"
}

phase8() {
  echo "=== PHASE 8 — close the loop ==="
  test -f scripts/run_self_evolve.py && \
    .venv/bin/python scripts/run_self_evolve.py --output .claude/memory/sprint_retrospective.md \
    || echo "self-evolve script absent; manually update .claude/memory/sprint_retrospective.md"
  git tag -l "v1.0.0*"
  echo "PHASE 8 PASS"
}

verify() {
  echo "=== VERIFY — done-checklist ==="
  bash scripts/check_workflow_links.sh
  bash scripts/forbidden_vocab_check.sh
  test "$(git status --short | wc -l)" -eq 0 && echo "[ok] working tree clean"
  git tag -l "v1.0.0-eternal" | grep -q . && echo "[ok] eternal tag present" || echo "[--] eternal tag missing"
  echo "VERIFY DONE"
}

case "${1:-}" in
  phase0) phase0 ;;
  phase2) phase2 ;;
  phase3) phase3 ;;
  phase4) phase4 ;;
  phase5) phase5 ;;
  phase6) phase6 ;;
  phase8) phase8 ;;
  verify) verify ;;
  *) echo "usage: $0 {phase0|phase2|phase3|phase4|phase5|phase6|phase8|verify}"; exit 2 ;;
esac
