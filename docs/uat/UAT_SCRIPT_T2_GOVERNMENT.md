# UAT Script — Tier 2: Ministry Liaison (Government)
**Persona:** MeitY/DST official analyzing national research capacity and funding allocation.
**Access:** Aggregated statistics only — no individual names, no personal data.
**Login:** `gov_user` / `government-pass`
**Duration:** 60 minutes, 10 queries

---

## Pre-Session Checklist

- [ ] API is running: `curl http://localhost:8000/health`
- [ ] Audit chain verified: `python scripts/chain_seal_attestation.py`
- [ ] Logged in as `gov_user`
- [ ] Confirmed dashboard shows only aggregated/anonymized views

**Verification test (Tier separation):**
- Run Query 1 from T1 (researcher name lookup)
- Confirm it returns NO individual researcher names
- If names appear → TIER SEPARATION FAIL — STOP and report

---

## Tier Separation Verification (2 min)

**Run this first:**
```
find robotics researchers in Gujarat
```

**Expected:** Aggregated count like "47 researchers across 12 institutions in Gujarat" — NO individual names.
**If you see a list of names → BLOCKER. Stop session. Report immediately.**

---

## Core Queries (55 min — ~5 min each)

For each query: time it, score quality (1-5), note if anonymized.

---

### Query 1 — State Funding Overview
**Text:**
```
Show state-wise research funding for the last 3 years
```
**Expected:** State names with aggregated funding amounts. Anonymized per-institution within state.
**Verify:** No individual researcher names visible.

---

### Query 2 — State Research Ranking
**Text:**
```
Which states have the most publications in AI?
```
**Expected:** State ranking with publication counts. Anonymized.
**Time target:** < 5s

---

### Query 3 — Sector Distribution
**Text:**
```
What percentage of research is in healthcare vs engineering?
```
**Expected:** Percentage breakdown by domain/sector. Anonymized.
**Time target:** < 5s

---

### Query 4 — Time-Series Growth
**Text:**
```
Show the growth trend of IIT publications over 10 years
```
**Expected:** Year-by-year chart/table of publication counts.
**Time target:** < 8s

---

### Query 5 — Patent Ranking
**Text:**
```
Which institutions have the highest patents filed?
```
**Expected:** Institutional ranking by patent count. Anonymized (institution names OK, individual names not).
**Time target:** < 5s

---

### Query 6 — Public vs Private Split
**Text:**
```
Compare funding allocation between government and private institutions
```
**Expected:** Segmented analysis — government vs private funding.
**Time target:** < 5s

---

### Query 7 — Research ROI
**Text:**
```
What is the research output per crore of funding?
```
**Expected:** Efficiency metric — publications or patents per ₹crore invested.
**Time target:** < 8s

---

### Query 8 — Geographic Heatmap
**Text:**
```
Show the geographic distribution of renewable energy research
```
**Expected:** State-level distribution. Geographic visualization.
**Time target:** < 8s

---

### Query 9 — Fastest Growing Areas
**Text:**
```
Which research areas have grown the fastest in 5 years?
```
**Expected:** Domain ranking with growth rates. Anonymized.
**Time target:** < 5s

---

### Query 10 — National Summary
**Text:**
```
Generate a summary report of national research capacity
```
**Expected:** Multi-section report covering publications, patents, funding, collaboration.
**Time target:** < 15s

---

## Scoring Matrix

| Query | Time (s) | Quality (1-5) | Anonymized? | Notes |
|-------|----------|--------------|-------------|-------|
| 1 | | | ☐ | |
| 2 | | | ☐ | |
| 3 | | | ☐ | |
| 4 | | | ☐ | |
| 5 | | | ☐ | |
| 6 | | | ☐ | |
| 7 | | | ☐ | |
| 8 | | | ☐ | |
| 9 | | | ☐ | |
| 10 | | | ☐ | |
| **Average** | | | | |

---

## Sign-Off

| | |
|---|---|
| **Ministry Liaison Name** | |
| **Date** | |
| **Queries Passed** | /10 |
| **Avg Response Time** | s |
| **Avg Quality** | /5 |
| **Anonymization Verified** | ☐ Yes ☐ No |
| **Signature** | ☐ Approved ☐ Conditional ☐ Rejected |
