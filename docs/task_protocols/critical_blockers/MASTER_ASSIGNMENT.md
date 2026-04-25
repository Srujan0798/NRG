# CRITICAL BLOCKERS — Master Assignment

**Date:** 2026-04-25  
**Status:** P0 — Demo cannot proceed until both are resolved  
**Discovered By:** Guru system check

---

## The Two Blockers

| # | Blocker | Impact | Fix Time | Protocol |
|---|---------|--------|----------|----------|
| B1 | Qdrant is DOWN | RAG retrieval fails, Step 9 of demo script fails | 15–30 min | `TP-B1_fix_qdrant.md` |
| B2 | Login accounts locked/wrong passwords | Cannot login, entire demo script blocked | 15–30 min | `TP-B2_fix_login_lockouts.md` |

---

## Execution Order

```
PARALLEL (both can run simultaneously):
├── TP-B1  Restart Qdrant + verify vectors     [DEVOPS/BACKEND]
└── TP-B2  Reset lockouts + verify all logins   [BACKEND/SECURITY]

THEN (sequential verification):
└── BOTH must report PASS before any demo work resumes
```

---

## Correct Credentials (Verified from Code)

| Persona | Username | Password |
|---------|----------|----------|
| Researcher | `researcher_user` | `researcher-pass` |
| Government | `gov_user` | `government-pass` |
| Industry | `industry_user` | `industry-pass` |

**If frontend `Login.tsx` shows different passwords, update it to match.**

---

## Verification Command (After Both Fixes)

```bash
# 1. Qdrant health
curl -s http://localhost:6333 && echo "✓ Qdrant up"

# 2. Backend health
curl -s http://localhost:8000/health | grep -q "qdrant_reachable.*true" && echo "✓ Backend sees Qdrant"

# 3. All 3 logins
for user in researcher_user gov_user industry_user; do
  case $user in
    researcher_user) pass="researcher-pass" ;;
    gov_user) pass="government-pass" ;;
    industry_user) pass="industry-pass" ;;
  esac
  curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$user\",\"password\":\"$pass\"}" | grep -q "access_token" && echo "✓ $user login OK" || echo "✗ $user login FAILED"
done
```

All checks must pass before any demo sprint work resumes.

---

## Evidence Folder

```
evidence/2026-04-25/critical_blockers/
├── B1_qdrant_fix.log
└── B2_login_verification.log
```
