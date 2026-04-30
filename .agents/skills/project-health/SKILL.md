---
name: project-health
description: "One-command health check that audits EVERYTHING — build, tests, security, audit chain, quality bar, forbidden vocab, schema parity, data quality, frontend lint, docker config. Produces a single health score (0-100) with pass/fail per dimension. The 'is my project broken?' button."
user-invocable: true
---

# Project Health Check

## Purpose

One command. One score. Is NRG healthy or not? No guessing, no partial checks, no "I think it works." Run this and know exactly where you stand.

## When to Use

- Start of every session
- Before any external session or showing
- After major changes (MVP merge, schema change, pipeline update)
- When Founder says "what's the state?"
- Weekly automated health check
- Before tagging a release

---

## The Health Protocol

### Run ALL checks in this order:

```
DIMENSION                    WEIGHT    COMMAND / CHECK
──────────────────────────────────────────────────────────
1. Git Status                 5%       git status, git stash list
2. Python Backend Build       10%      pip install check, import test
3. Frontend Build             10%      npm run build
4. Python Tests               15%      pytest (with timeout)
5. Frontend Tests             10%      npm run test
6. Frontend Lint              5%       npm run lint
7. Security Scan              10%      pip-audit, npm audit
8. Forbidden Vocabulary       5%       forbidden_vocab_check.sh
9. Quality Bar Scorecard      15%      quality_bar_scorecard.py
10. Audit Chain               5%       audit_investigate.py
11. Docker Config             5%       docker compose config
12. Data Quality              5%       data_quality_scorecard.py
──────────────────────────────────────────────────────────
TOTAL                        100%
```

### Check Details

#### 1. Git Status (5%)
```bash
git status --short
git stash list
git log --oneline -3
```
- Clean tree = 5/5
- Uncommitted changes = 3/5
- Dirty tree with untracked = 1/5

#### 2. Python Backend Build (10%)
```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/python -c "from src.api.main import app; print('API importable')"
.venv/bin/python -c "from src.orchestration.graph import NRGWorkflow; print('Orchestration importable')"
.venv/bin/python -c "from src.audit import AuditLogger; print('Audit importable')"
.venv/bin/python -c "from src.security.pii import detect_pii; print('PII importable')"
```
- All 4 imports work = 10/10
- Per import failure = -2.5

#### 3. Frontend Build (10%)
```bash
cd frontend && npm run build 2>&1
```
- Clean build = 10/10
- Build with warnings = 7/10
- Build fails = 0/10

#### 4. Python Tests (15%)
```bash
cd /Users/srujansai/Desktop/NRG
PYTEST_CURRENT_TEST=1 .venv/bin/python -m pytest tests/ -q --ignore=tests/scripts --timeout=120 -x 2>&1
```
- All pass = 15/15
- >95% pass = 12/15
- >80% pass = 8/15
- <80% pass = 3/15
- Can't run = 0/15

#### 5. Frontend Tests (10%)
```bash
cd frontend && npm run test -- --run 2>&1
```
- All pass = 10/10
- >90% pass = 7/10
- <90% = 3/10
- Can't run = 0/10

#### 6. Frontend Lint (5%)
```bash
cd frontend && npm run lint 2>&1
```
- Clean = 5/5
- Warnings only = 3/5
- Errors = 0/5

#### 7. Security Scan (10%)
```bash
cd /Users/srujansai/Desktop/NRG
.venv/bin/pip-audit --strict 2>&1 | tail -5
cd frontend && npm audit --audit-level=critical 2>&1 | tail -5
grep -rn "sk-\|password.*=.*['\"].*[a-zA-Z]" src/ --include="*.py" | grep -v test | grep -v ".pyc" | head -5
```
- Zero critical/high + no leaked keys = 10/10
- Medium vulns only = 7/10
- Critical/high vulns = 3/10
- Leaked credentials found = 0/10

#### 8. Forbidden Vocabulary (5%)
```bash
bash scripts/forbidden_vocab_check.sh 2>&1
```
- Clean = 5/5
- Violations found = 0/5

#### 9. Quality Bar Scorecard (15%)
```bash
.venv/bin/python scripts/quality_bar_scorecard.py 2>&1
```
- 6/6 pass = 15/15
- 5/6 pass = 10/15
- 4/6 pass = 6/15
- <4/6 = 2/15

#### 10. Audit Chain (5%)
```bash
.venv/bin/python scripts/audit_investigate.py 2>&1
```
- ok=true, zero breaks = 5/5
- ok=true with warnings = 3/5
- ok=false = 0/5

#### 11. Docker Config (5%)
```bash
docker compose config --quiet 2>&1
```
- Valid config = 5/5
- Config errors = 0/5
- Docker not available = 2/5 (acceptable locally)

#### 12. Data Quality (5%)
```bash
.venv/bin/python scripts/data_quality_scorecard.py --database-url sqlite:///nrg_research.db 2>&1
```
- All 7 pillars pass = 5/5
- P1 issues only = 3/5
- P0 issues = 0/5

---

### Scoring

```
SCORE    GRADE    MEANING
─────────────────────────────────────
90-100   A+       Production-ready. Ship it.
80-89    A        Strong. Minor issues only.
70-79    B        Acceptable. Fix P1s before showing.
60-69    C        Fragile. Several things broken.
50-59    D        Risky. Major fixes needed.
<50      F        Broken. Do not show to anyone.
```

---

### Output Format

```markdown
## NRG Project Health Report — [Date] [Time]

### Overall: [SCORE]/100 — Grade [A+/A/B/C/D/F]

### Dimension Breakdown
| # | Dimension | Score | Max | Status | Details |
|---|-----------|-------|-----|--------|---------|
| 1 | Git Status | X | 5 | ✅/⚠️/❌ | [clean/dirty/...] |
| 2 | Backend Build | X | 10 | ✅/❌ | [all imports/failures] |
| 3 | Frontend Build | X | 10 | ✅/❌ | [clean/warnings/fail] |
| 4 | Python Tests | X | 15 | ✅/⚠️/❌ | [X passed, Y failed, Z skipped] |
| 5 | Frontend Tests | X | 10 | ✅/⚠️/❌ | [X passed, Y failed] |
| 6 | Frontend Lint | X | 5 | ✅/⚠️/❌ | [clean/warnings/errors] |
| 7 | Security | X | 10 | ✅/⚠️/❌ | [clean/vulns found/keys leaked] |
| 8 | Forbidden Vocab | X | 5 | ✅/❌ | [clean/X violations] |
| 9 | Quality Bar | X | 15 | ✅/⚠️/❌ | [X/6 constraints pass] |
| 10 | Audit Chain | X | 5 | ✅/❌ | [ok/broken, X events] |
| 11 | Docker Config | X | 5 | ✅/⚠️/❌ | [valid/errors/unavailable] |
| 12 | Data Quality | X | 5 | ✅/⚠️/❌ | [X/7 pillars pass] |

### Critical Issues (fix NOW)
- [list any 0-score dimensions]

### Warnings (fix before showing)
- [list any partial-score dimensions]

### Healthy
- [list any full-score dimensions]

### Comparison vs Last Check
| Dimension | Last | Now | Change |
|-----------|------|-----|--------|
| ... | ... | ... | ↑/↓/→ |

### Quick Commands to Fix Issues
[For each failing dimension, the exact command to fix it]
```

### Evidence

```
evidence/<date>/project_health/
├── health_report.md
├── health_report.json     # machine-readable
├── raw_outputs/
│   ├── git_status.txt
│   ├── backend_build.txt
│   ├── frontend_build.txt
│   ├── pytest_output.txt
│   ├── frontend_test.txt
│   ├── lint_output.txt
│   ├── security_scan.txt
│   ├── vocab_check.txt
│   ├── quality_bar.txt
│   ├── audit_chain.txt
│   ├── docker_config.txt
│   └── data_quality.txt
└── health_history.json    # append-only, tracks score over time
```

---

## Agent Assignment Template

```
═══ PROJECT HEALTH CHECK ═══

Read .claude/skills/project-health/SKILL.md
Run ALL 12 checks in order.
Produce health report with score.
Save to evidence/<date>/project_health/

Skills: project-health, test-suite, security-audit, audit-check
Report the score first, then details.
```
