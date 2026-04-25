# UAT Script — Tier 1: Professor (Researcher)
**Persona:** IIT-GN Computer Science professor seeking collaborators and tracking publications.
**Access:** Full researcher data including personal contact info.
**Login:** `researcher_user` / `researcher-pass`
**Duration:** 60 minutes, 10 queries

---

## Pre-Session Checklist

- [ ] API is running: `curl http://localhost:8000/health`
- [ ] Audit chain verified: `python scripts/chain_seal_attestation.py`
- [ ] Test user logged in successfully
- [ ] Notepad open for timing + quality notes

---

## Session Flow

### Part A: Login + Orientation (5 min)

1. Navigate to http://localhost:3000
2. Select **Researcher** persona
3. Login with `researcher_user` / `researcher-pass`
4. Verify dashboard loads with researcher-focused UI
5. Note: Full names, institution details, h-index scores should be visible

### Part B: Core Queries (50 min — 5 min per query)

For each query below:
1. Copy exact query text
2. Paste into NRG search box
3. Start timer when you press Enter
4. Stop timer when answer appears
5. Record: time, quality (1-5), citation accuracy (1-5)
6. Note any unexpected behavior

---

### Query 1 — Simple Researcher Lookup
**Text:**
```
find robotics researchers in Gujarat
```
**Expected:** List of named researchers with robotics focus in Gujarat institutions. Should show names, institutions, possibly h-index.
**Time target:** < 3s

---

### Query 2 — Ranking Query
**Text:**
```
Who has published the most on machine learning in the last 5 years?
```
**Expected:** Ranked list with publication counts. Verify counts are plausible.
**Time target:** < 5s

---

### Query 3 — Domain Expertise
**Text:**
```
Show me researchers working on hydrogen fuel cells
```
**Expected:** Researchers with hydrogen fuel cell expertise. Affiliation + research area visible.
**Time target:** < 5s

---

### Query 4 — Multi-State Comparison (HARD)
**Text:**
```
Compare AI research output between Gujarat and Karnataka over the last 5 years
```
**Expected:** Side-by-side comparison. Two states, 5-year window. Multi-hop planner should decompose this.
**Time target:** < 10s

---

### Query 5 — Personal Data Retrieval
**Text:**
```
Find my profile and show my publications
```
**Expected:** Researcher profile with their publications listed.
**Time target:** < 5s

---

### Query 6 — Institutional Statistics
**Text:**
```
Which institutions have the highest collaboration rate?
```
**Expected:** Aggregated institutional collaboration metrics. Named institutions.
**Time target:** < 5s

---

### Query 7 — Lab Capability Search
**Text:**
```
Show me labs working on quantum computing
```
**Expected:** List of labs with quantum computing research. Lab names + institutions.
**Time target:** < 5s

---

### Query 8 — Funding Trend Analysis
**Text:**
```
What is the funding trend for renewable energy research?
```
**Expected:** Time-series of funding amounts for renewable energy domain.
**Time target:** < 8s

---

### Query 9 — Researcher-Patent Linkage
**Text:**
```
Find researchers who have patents in semiconductor design
```
**Expected:** Researchers with patent records linked to semiconductor work.
**Time target:** < 5s

---

### Query 10 — Knowledge Graph
**Text:**
```
Show the knowledge graph for deep learning
```
**Expected:** Visual graph of deep learning research — papers, authors, institutions connected.
**Time target:** < 8s

---

## Part C: Audit Verification (5 min)

1. Navigate to `/audit/verify`
2. Record: `Chain valid: True/False`
3. Record: Event count
4. Record: Last hash (first 16 chars)

---

## Scoring Matrix

| Query | Time (s) | Quality (1-5) | Citations (1-5) | Notes |
|-------|----------|--------------|-----------------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| **Average** | | | | |

**Pass threshold:** ≥8/10 queries return useful results.

---

## Sign-Off

| | |
|---|---|
| **Professor Name** | |
| **Date** | |
| **Queries Passed** | /10 |
| **Avg Response Time** | s |
| **Avg Quality** | /5 |
| **Signature** | ☐ Approved ☐ Conditional ☐ Rejected |
