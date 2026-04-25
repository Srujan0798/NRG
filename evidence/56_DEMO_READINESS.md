# Demo Readiness Check
**Date:** 2026-04-25
**Skill:** `.claude/skills/demo-readiness/SKILL.md`

---

## Applying Demo Readiness to NRG

### The Professor Principle

> "The professor does not care about your test suite, your HMAC chain, or your LangGraph nodes. He opens a browser, clicks things, types things, and decides in 90 seconds whether this is worth ₹50 lakhs."

### Quick Checklist (5 Minutes)

The skill defines a 10-step demo script. Applying to NRG's current state:

| Step | Check | Status | Notes |
|------|-------|--------|-------|
| 1 | Chrome DevTools Console empty | UNKNOWN | Requires browser execution |
| 2 | Network tab — 0 failed requests | UNKNOWN | Requires browser execution |
| 3 | Lighthouse ≥ 70 performance/accessibility | UNKNOWN | Requires browser execution |
| 4 | Tier 1 login → Dashboard with real numbers | UNKNOWN | Requires running API |
| 5 | Tier 3 login → VISIBLY different UI | UNKNOWN | Requires browser + auth |
| 6 | Query → Loading → Readable prose result | UNKNOWN | Requires running system |
| 7 | PII query → Clean blocked message | PARTIAL | Security pipeline exists |
| 8 | Every nav link → No 404s | UNKNOWN | Requires browser |
| 9 | 375px resize → Readable, no horizontal scroll | UNKNOWN | Requires browser |
| 10 | Browser tab titles → Meaningful | PARTIAL | Route titles configured |

### Red Flags Assessment

| Red Flag | Current State |
|----------|---------------|
| Console shows red errors | Unknown — needs browser check |
| "undefined"/"null"/"NaN" visible | Unknown — needs browser check |
| Raw JSON shown to user | Synthesizer produces prose — likely OK |
| Spinner never stops | Unknown — needs timeout handling verification |
| No visual feedback on click | Unknown — needs UI review |
| Page title is "React App" | Likely fixed — React apps typically set titles |
| Horizontal scroll on desktop | Unknown — needs browser check |
| Tier 1 and Tier 3 look identical | Unknown — needs UI comparison |
| `alert()` in code | Unknown — needs grep |
| Placeholder text | Unknown — needs grep |

### Pre-Demo Requirements

Before demo, the following must be verified in a running browser:

**Minimum viable demo check:**
1. API server running: `.venv/bin/python -m uvicorn src.api.main:app --reload --port 8000`
2. Frontend running: `cd frontend && npm run dev`
3. Login flow works for Tier 1
4. Query returns readable prose (not JSON)
5. Security blocking works for PII injection attempt

**Evidence required for demo-readiness:**
- Screen recording of 10-step demo script
- Lighthouse report screenshot (Performance + Accessibility ≥ 70)
- Console screenshot (0 errors)
- Network screenshot (0 failed requests)
- UI/UX Audit Report filled

---

## NRG Demo Readiness Assessment

### Current State: NOT FULLY VERIFIED

**What's confirmed working:**
- Router: 51/51 tests passing
- Audit chain: Operational
- Security pipeline: Hardened (6 vulnerability types addressed)
- LangGraph pipeline: All 6 nodes implemented

**What's unverified (needs running system):**
- Frontend UI rendering
- Login flow end-to-end
- Query → response flow in browser
- Lighthouse scores
- Console cleanliness

### Recommendation

Before any demo with the professor:
1. Start the full stack: `/deploy-local`
2. Run the 10-step demo script
3. Capture all 5 evidence items
4. Fill UI/UX Audit Report template

**If any step fails → Fix before demo.**

---

## Skill Application Evidence

This document applies the demo-readiness skill to assess NRG's readiness for a ₹50L demo.

**Key finding:** The system has strong backend foundations (router, audit, security) but frontend demo-readiness cannot be verified without a running browser session.

**Required action:** Run `/deploy-local` and execute the 10-step demo script to complete the demo-readiness verification.