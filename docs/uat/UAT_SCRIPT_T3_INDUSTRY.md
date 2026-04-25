# UAT Script — Tier 3: Industry Partner
**Persona:** R&D director scouting research partnerships and technology experts.
**Access:** Institution names + research areas only — no personal data, no detailed statistics.
**Login:** `industry_user` / `industry-pass`
**Duration:** 60 minutes, 10 queries

---

## Pre-Session Checklist

- [ ] API is running: `curl http://localhost:8000/health`
- [ ] Audit chain verified: `python scripts/chain_seal_attestation.py`
- [ ] Logged in as `industry_user`
- [ ] Confirmed no personal contact info visible

**Tier Separation Verification (Tier 3 is most restricted):**
- Run Query 1 from T1
- Confirm NO personal data: no email, phone, individual researcher names
- If you see individual names or contact info → BLOCKER

---

## Tier Separation Verification (2 min)

**Run this first:**
```
find robotics researchers in Gujarat
```

**Expected:** Institution names + research areas only. NO: individual names, email, phone, h-index, ORCID.
**If personal data appears → BLOCKER. Stop. Report immediately.**

---

## Core Queries (55 min — ~5 min each)

---

### Query 1 — EV Battery Expertise
**Text:**
```
Who works on electric vehicle battery technology?
```
**Expected:** Institution names + research area focus. No individual names.
**Time target:** < 5s

---

### Query 2 — Semiconductor Capability
**Text:**
```
Find institutions with semiconductor research capability
```
**Expected:** List of institutions (IITs, NITs, etc.) with semiconductor programs.
**Verify:** No individual faculty names.

---

### Query 3 — ML Experts (Anonymized)
**Text:**
```
Who are the top experts in machine learning?
```
**Expected:** Research area focus, possibly institution-level groupings. NOT individual names.
**Time target:** < 5s

---

### Query 4 — Quantum Research Groups
**Text:**
```
Show research groups working on quantum computing
```
**Expected:** Group/institution names. Anonymized.
**Time target:** < 5s

---

### Query 5 — Collaboration Network
**Text:**
```
Which institutions collaborate on robotics research?
```
**Expected:** Collaboration patterns between institutions. NO individual names.
**Time target:** < 8s

---

### Query 6 — Emerging Materials
**Text:**
```
Find researchers in graphene-related technologies
```
**Expected:** Institution + research area matches. No individual names.
**Time target:** < 5s

---

### Query 7 — Chip Design Expertise
**Text:**
```
Who has expertise in chip design and verification?
```
**Expected:** Anonymized area + institution listing.
**Time target:** < 5s

---

### Query 8 — Institutional Ranking
**Text:**
```
Show the top 10 research institutions in India by area
```
**Expected:** Anonymized ranking. Area breakdowns by institution.
**Time target:** < 5s

---

### Query 9 — Communications Research
**Text:**
```
Which researchers publish on 5G and next-gen communications?
```
**Expected:** Area + institution focus. No personal data.
**Time target:** < 5s

---

### Query 10 — Industry-Academia Collaboration
**Text:**
```
Find industry-academia collaboration examples in AI
```
**Expected:** Collaboration patterns. Institution names OK. Individual names NOT OK.
**Time target:** < 8s

---

## Scoring Matrix

| Query | Time (s) | Quality (1-5) | Tier Compliant? | Notes |
|-------|----------|--------------|-----------------|-------|
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
| **Industry Partner Name** | |
| **Date** | |
| **Queries Passed** | /10 |
| **Avg Response Time** | s |
| **Avg Quality** | /5 |
| **Tier Compliance** | ☐ Verified |
| **Signature** | ☐ Approved ☐ Conditional ☐ Rejected |
