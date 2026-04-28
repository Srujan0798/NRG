#!/bin/bash
# run_critical_path_final.sh — final orchestrator for the user-visible path.
# Boots stack, seeds, prewarms, runs Playwright walk, eyeballs 5 golden answers,
# saves video + screenshots + JSON, prints a single PASS/FAIL summary.
#
# Usage:
#   bash scripts/run_critical_path_final.sh           # full run
#   bash scripts/run_critical_path_final.sh --reset   # wipe + fresh boot
#   bash scripts/run_critical_path_final.sh --walk    # just the Playwright walk
#
# Exits non-zero on any RED. Writes evidence/<date>/critical_path/.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE=$(date +%Y-%m-%d)
EVID="$REPO/evidence/$DATE/critical_path"
cd "$REPO"
mkdir -p "$EVID"

step() { echo -e "\n\033[1;34m[$(date +%T)] $*\033[0m"; }
ok()   { echo -e "  \033[32m[ok]\033[0m $*"; }
fail() { echo -e "  \033[31m[FAIL]\033[0m $*"; exit 1; }
warn() { echo -e "  \033[33m[warn]\033[0m $*"; }

############# 0. preflight
step "0/8 preflight — env + venv + docker"
[ -f .env ] || fail ".env missing — copy .env.prod.example and fill secrets"
grep -q '^MINIMAX_API_KEY=' .env || fail "MINIMAX_API_KEY missing in .env"
grep -q '^LLM_PROVIDER=minimax' .env || warn "LLM_PROVIDER is not minimax"
[ -d .venv ] || { python3.11 -m venv .venv && .venv/bin/pip install -e '.[dev]' pytest-xdist pytest-timeout; }
command -v docker >/dev/null || fail "docker not installed"
command -v jq >/dev/null || fail "jq not installed (brew install jq)"
ok "preflight clean"

############# 1. reset (optional)
if [ "${1:-}" = "--reset" ]; then
  step "1/8 reset — wipe docker volumes"
  docker compose -f docker-compose.prod.yml down -v || true
  ok "volumes wiped"
fi

############# 2. boot stack
step "2/8 boot — docker compose up"
docker compose -f docker-compose.prod.yml up -d
for port in 5432 6333 6379 8000; do
  for i in {1..30}; do
    nc -z localhost $port 2>/dev/null && break
    sleep 1
  done
  nc -z localhost $port 2>/dev/null || fail "port $port not reachable"
done
ok "PG, Qdrant, Redis, API up"

############# 3. migrate + seed + prewarm
step "3/8 migrate + seed + prewarm"
.venv/bin/alembic upgrade head | tail -3
.venv/bin/python scripts/seed_acceptance_users.py 2>/dev/null \
  || .venv/bin/python scripts/seed_demo_data.py
.venv/bin/python scripts/seed_acceptance_data.py --rows 50000 2>/dev/null \
  || .venv/bin/python scripts/seed_production_initial_dataset.py --rows 50000 2>/dev/null \
  || warn "seed script not found — skipping (assumes prior seed)"
.venv/bin/python scripts/prewarm_acceptance_cache.py 2>/dev/null \
  || .venv/bin/python scripts/prewarm_demo_cache.py 2>/dev/null \
  || warn "prewarm script not found — skipping"
ok "data + cache ready"

############# 4. /health green
step "4/8 /health green"
HEALTH=$(curl -fsS http://localhost:8000/health)
echo "$HEALTH" | jq . > "$EVID/health.json"
echo "$HEALTH" | jq -e '.status=="healthy"' >/dev/null \
  || fail "/health status != healthy — see $EVID/health.json"
echo "$HEALTH" | jq -e '.audit.chain_valid==true' >/dev/null \
  || warn "audit chain not valid"
ok "/health healthy"

############# 5. login curl × 3 personas
step "5/8 login — 3 personas via curl"
for persona in 'researcher@iitgn.ac.in:Researcher@2026:t1' \
               'ministry@nrg.gov.in:Ministry@2026:t2' \
               'partner@industry.in:Industry@2026:t3'; do
  EMAIL=${persona%%:*}; REST=${persona#*:}
  PASS=${REST%%:*}; TIER=${REST##*:}
  RESP=$(curl -sS -X POST http://localhost:8000/auth/login \
           -H 'Content-Type: application/json' \
           -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
  echo "$RESP" > "$EVID/cp_login_curl_${TIER}.txt"
  echo "$RESP" | jq -e '.access_token' >/dev/null \
    || fail "login failed for $EMAIL — see $EVID/cp_login_curl_${TIER}.txt"
  ok "$TIER login OK"
done

############# 6. golden 5 questions × 3 tiers (eyeball later)
step "6/8 golden answers — 5 questions × 3 tiers"
GOLDEN=("Top 5 funding agencies by total grant amount last 5 years"
        "Compare Gujarat and Karnataka AI research output 5y; show gap"
        "Which IITs collaborate most on hydrogen catalysis?"
        "How many TRL-9 innovations exist in clean energy by state?"
        "Show me institutes that doubled grant size between FY22 and FY24")
> "$EVID/cp0_golden_answers.md"
echo "# Golden Answers — $DATE" >> "$EVID/cp0_golden_answers.md"
for tier in t1 t2 t3; do
  TOKEN=$(jq -r '.access_token' "$EVID/cp_login_curl_${tier}.txt")
  for i in 0 1 2 3 4; do
    Q="${GOLDEN[$i]}"
    START=$(date +%s)
    ANS=$(curl -sS -X POST http://localhost:8000/query \
            -H "Authorization: Bearer $TOKEN" \
            -H 'Content-Type: application/json' \
            --max-time 30 \
            -d "{\"question\":\"$Q\"}" || echo '{}')
    DUR=$(( $(date +%s) - START ))
    echo "" >> "$EVID/cp0_golden_answers.md"
    echo "## $tier · G$((i+1)) · ${DUR}s" >> "$EVID/cp0_golden_answers.md"
    echo "**Q:** $Q" >> "$EVID/cp0_golden_answers.md"
    echo "**Answer:**" >> "$EVID/cp0_golden_answers.md"
    echo "$ANS" | jq -r '.final_answer // .answer // .text // (.|@json)' \
      | head -40 >> "$EVID/cp0_golden_answers.md"
    echo "**SQL:**" >> "$EVID/cp0_golden_answers.md"
    echo '```sql' >> "$EVID/cp0_golden_answers.md"
    echo "$ANS" | jq -r '.sql_query // ""' >> "$EVID/cp0_golden_answers.md"
    echo '```' >> "$EVID/cp0_golden_answers.md"
  done
  ok "$tier × 5 captured"
done
ok "golden answer set saved → $EVID/cp0_golden_answers.md (eyeball ≥13/15)"

############# 7. Playwright walk + recording
step "7/8 Playwright walk — 10 steps + recording"
if [ -d frontend ]; then
  cd frontend
  if ! [ -d node_modules ]; then npm ci --silent; fi
  if ! npx playwright --version >/dev/null 2>&1; then
    npx playwright install --with-deps chromium >/dev/null 2>&1
  fi
  if [ -f tests/e2e/acceptance_walk.spec.ts ]; then
    npx playwright test tests/e2e/acceptance_walk.spec.ts \
      --reporter=line --output="$EVID/playwright" \
      --workers=1 || fail "Playwright walk FAILED — see $EVID/playwright"
    [ -f "$EVID/playwright/walk_recording.mp4" ] || \
      cp "$EVID/playwright/"*.mp4 "$EVID/walk_recording.mp4" 2>/dev/null || \
      warn "no recording captured — run with PWVIDEO=on"
    ok "10-step walk PASS"
  else
    warn "tests/e2e/acceptance_walk.spec.ts missing — write it per CP-9"
  fi
  cd "$REPO"
else
  warn "frontend/ missing — skipping walk"
fi

############# 8. summary
step "8/8 summary"
echo "" | tee -a "$EVID/SUMMARY.md"
echo "# Critical Path Final Run — $DATE" | tee "$EVID/SUMMARY.md"
echo "Commit: $(git rev-parse --short HEAD)" | tee -a "$EVID/SUMMARY.md"
echo "" | tee -a "$EVID/SUMMARY.md"
echo "✅ /health healthy" | tee -a "$EVID/SUMMARY.md"
echo "✅ login × 3 personas (T1/T2/T3)" | tee -a "$EVID/SUMMARY.md"
echo "✅ golden answers × 15 cells captured (eyeball: $EVID/cp0_golden_answers.md)" | tee -a "$EVID/SUMMARY.md"
[ -f "$EVID/walk_recording.mp4" ] && echo "✅ Playwright walk recorded" \
  | tee -a "$EVID/SUMMARY.md" || echo "⏭ Playwright walk: not captured" \
  | tee -a "$EVID/SUMMARY.md"
echo "" | tee -a "$EVID/SUMMARY.md"
echo "Next:" | tee -a "$EVID/SUMMARY.md"
echo "  1) Eyeball $EVID/cp0_golden_answers.md — accept ≥13/15" | tee -a "$EVID/SUMMARY.md"
echo "  2) Open http://localhost:5173 and walk the 10 steps manually" | tee -a "$EVID/SUMMARY.md"
echo "  3) If anything feels wrong → file defect → fix → re-run this script" | tee -a "$EVID/SUMMARY.md"
echo "" | tee -a "$EVID/SUMMARY.md"
echo -e "\n\033[1;32mREADY — http://localhost:5173\033[0m"
echo "T1 researcher@iitgn.ac.in / Researcher@2026"
echo "T2 ministry@nrg.gov.in    / Ministry@2026"
echo "T3 partner@industry.in    / Industry@2026"
