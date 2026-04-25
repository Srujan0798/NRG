# UAT Scripts — GAP-G Evidence

**Date**: 2026-04-25
**Gap**: GAP-G — UAT sessions with 3 personas (researcher, government, industry)

UAT cannot be conducted without real participants. However, the **UAT scripts and materials** are fully prepared and ready for immediate use when participants are available.

---

## Persona 1: Researcher (Tier 1)

**Profile**: Academic researcher at IIT Bombay. Access to publications, researcher profiles, projects with `access_tier >= 1`. Full individual records visible.

### UAT Script

```bash
# === PRE-REQUISITES ===
# 1. Start API: uvicorn src.api.main:app --host 127.0.0.1 --port 8000
# 2. JWT token for researcher persona
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "researcher_user", "password": "researcher-pass", "grant_type": "password"}'

# === TEST 1: Query publication counts ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many publications are in the database?", "user_context": {"role": "researcher"}}'
# Expected: sql_results with count, audit_event_id returned

# === TEST 2: List publications by research area ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me publications in AI/ML from 2020 onwards", "user_context": {"role": "researcher"}}'
# Expected: Table of publications, authors, venues, citations

# === TEST 3: Researcher profile lookup ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the h-index of IIT Bombay researchers in Machine Learning?", "user_context": {"role": "researcher"}}'
# Expected: Aggregated stats, researcher names and institutions

# === TEST 4: Funding opportunity query ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What government funding opportunities are available for quantum computing research?", "user_context": {"role": "researcher"}}'
# Expected: List of projects, funding agencies, sanctioned amounts

# === TEST 5: Verify audit trail ===
curl http://localhost:8000/audit/self \
  -H "Authorization: Bearer <TOKEN>"
# Expected: List of user's own audit events

# === SUCCESS CRITERIA ===
# - All 5 queries return 200 with valid sql_results
# - audit_event_id present in all responses
# - No PII exposed (verified by running PII scan on outputs)
# - Chain integrity maintained: verify_chain() = True
```

---

## Persona 2: Government (Tier 2)

**Profile**: Ministry official. Access to aggregated statistics and sample records with masked PII. Requires IP allowlist for tier-2 access.

> **Note**: Government tier requires IP to be in allowlist. Test from whitelisted IP or use TESTING=true bypass.

### UAT Script

```bash
# === PRE-REQUISITES ===
# IP allowlist entry for test machine in src/api/middleware/security.py
# Or run with: TESTING=true uvicorn src.api.main:app --host 127.0.0.1 --port 8000

# === TEST 1: National R&D statistics (aggregated) ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <GOV_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the total funding allocated to AI research across all IITs?", "user_context": {"role": "government"}}'
# Expected: Aggregated figures, no individual researcher records

# === TEST 2: Institution-level comparison ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <GOV_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare publication counts across IITs for the last 5 years", "user_context": {"role": "government"}}'
# Expected: Comparative table with masked/minimal PII

# === TEST 3: High-value project listing ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <GOV_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all projects above INR 50 Crores funding", "user_context": {"role": "government"}}'
# Expected: Project titles, agencies, amounts (PII masked)

# === TEST 4: Researcher collaboration networks ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <GOV_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show collaboration patterns between institutions in semiconductor research", "user_context": {"role": "government"}}'
# Expected: Aggregated network data, no individual emails/phones

# === TEST 5: Policy recommendation query ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <GOV_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Identify research gaps in climate science based on publication analysis", "user_context": {"role": "government"}}'
# Expected: Synthesized recommendation with supporting data

# === SUCCESS CRITERIA ===
# - All 5 queries return 200
# - No individual PII (emails, phones, ORCIDs) in outputs
# - Aggregated/summary data only for individual-level metrics
# - IP allowlist verified in logs
```

---

## Persona 3: Industry (Tier 3)

**Profile**: Corporate R&D team. Access to anonymized summaries only. No individual researcher or institution records.

### UAT Script

```bash
# === PRE-REQUISITES ===
# Industry user token from auth endpoint

# === TEST 1: Market landscape summary ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <INDUSTRY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the emerging research trends in quantum computing?", "user_context": {"role": "industry"}}'
# Expected: Anonymized trend summary, no researcher names

# === TEST 2: Technology capability assessment ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <INDUSTRY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize Indian research output in semiconductor technology", "user_context": {"role": "industry"}}'
# Expected: Aggregated counts, anonymized institution categories

# === TEST 3: Funding landscape ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <INDUSTRY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the total government funding in AI/ML research?", "user_context": {"role": "industry"}}'
# Expected: Aggregate funding figures only

# === TEST 4: Collaboration opportunity identification ===
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <INDUSTRY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Identify potential research collaboration areas between industry and academia", "user_context": {"role": "industry"}}'
# Expected: Anonymized areas of mutual interest

# === TEST 5: Verify no PII leakage ===
# Run PII scan on all outputs from above queries
# Expected: 0 PII detections

# === SUCCESS CRITERIA ===
# - All queries return 200 with anonymized outputs
# - No individual researcher names, emails, phone numbers
# - No specific institution names (only categories like "IIT", "NIT", "Institute")
# - PII compliance test: 0/5 queries contain PII
```

---

## UAT Execution Checklist

- [ ] All 3 persona types tested
- [ ] Researcher: 5/5 queries return valid structured data
- [ ] Government: 5/5 queries with no PII, proper aggregation
- [ ] Industry: 5/5 queries anonymized, no individual records
- [ ] PII scan run on all 15 query outputs — 0 detections
- [ ] Audit events logged for all 15 queries
- [ ] Chain integrity verified post-UAT: `verify_chain() = True`
- [ ] Rate limit behavior confirmed (429 after 10 req/min per persona)

## GAP-G Status: MATERIALS READY

UAT scripts and success criteria are fully prepared. The actual UAT sessions require:
1. Scheduling with professor + ministry + industry contacts
2. Sovereign cluster access for production environment testing
3. Real participant consent (DPDP compliance)

**Code is ready. Materials are ready. Scheduling is the remaining ops task.**
