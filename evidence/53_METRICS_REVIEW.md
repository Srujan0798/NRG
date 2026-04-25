# Metrics Review — NRG System Health
**Date:** 2026-04-25
**Skill:** `.claude/skills/metrics-review/SKILL.md`

---

## Applying Metrics Review to NRG

### North Star Metric for NRG

**Primary North Star:** "Queries successfully resolved with cited, tier-appropriate answers"
- Tracks: Successful query resolution rate
- Target: 90%+ resolution with proper citations
- Measurement: LangGraph pipeline success rate × verifier citation faithfulness

### L1 Health Indicators for NRG

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Text-to-SQL Accuracy (Dhairya benchmark) | 7/17 (41%) | 17/17 | AT RISK |
| Router accuracy | 51/51 (100%) | 95%+ | ON TRACK |
| Audit chain integrity | Operational | 100% valid | ON TRACK |
| Test suite pass rate | 609/872 (70%) | 85%+ | AT RISK |
| API response time | <7.2s avg | <5s | AT RISK |
| Security blocking rate | PII injection blocked | 100% | ON TRACK |

### L2 Diagnostic Metrics

| Metric | Current | Notes |
|--------|---------|-------|
| Staged file count | 4 files | Active development |
| Recent commits | 10 (2 weeks) | Active development velocity |
| Schema gap (dev vs prod) | 40 tables missing | Production schema integration pending |
| Security fixes (recent) | 6 vulnerability classes addressed | Good hardening progress |

---

## Summary

**NRG is in active development with targeted improvements needed in:**
1. Text-to-SQL accuracy (41% → target 95%+)
2. Test suite pass rate (70% → target 85%+)
3. API response time optimization

**Bright spots:**
- Router at 100% (51/51)
- Security hardening comprehensive (6 vulnerability types addressed)
- Audit chain rebuilt and operational
- 3-tier RBAC and DPDP compliance wired

---

## Recommended Actions

1. **Investigation:** Deep-dive into Text-to-SQL failures using Dhairya's 17-query benchmark
2. **Experiment:** Test schema hints improvements against the 5 wrong queries
3. **Investment:** Prioritize test suite remediation to improve CI confidence
4. **Alert:** Monitor API response times, set threshold at 10s

---

## Metrics Review Skill Application Evidence

This document applies the metrics-review skill framework to assess NRG system health using data from CLAUDE.md, git history, and evidence files.

**Key metrics identified using the L1/L2 hierarchy from the skill.**
**Recommendations follow the "so what → do this" pattern from the skill guidance.**