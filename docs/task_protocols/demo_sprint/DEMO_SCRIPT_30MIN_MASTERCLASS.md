# NRG Demo Script — 30-Minute Masterclass

**Audience:** Professor + research group + potential collaborators (5-10 people, mixed technical depth)  
**Duration:** 30 minutes  
**Goal:** Full system demonstration + architecture walkthrough + hands-on participation

---

## SECTION 1: THE VISION (5 minutes)

### Opening Story (3 minutes)

> "In 2019, the DST launched the National Mission on Interdisciplinary Cyber-Physical Systems. ₹3,660 crore. 25 hubs. 1,000+ researchers."

> "In 2023, they wanted to know: what did we get for that money? Which hubs produced patents? Which produced papers? Which produced commercial products?"

> "The answer took 6 months. Teams of people. Excel sheets. Phone calls. Guesswork."

> "NRG answers that question in 6 seconds."

### The Sovereign AI Doctrine (2 minutes)

**[Show `NRG_CONSTITUTION.md` on screen]**

> "We have three non-negotiable principles, written into the codebase itself:"

1. **Data Sovereignty** — Indian research data on Indian infrastructure
2. **Algorithmic Sovereignty** — AI that works without foreign API dependencies
3. **Audit Sovereignty** — Every decision traceable, every action accountable

> "This isn't a feature list. This is `NRG_CONSTITUTION.md`. It lives in the repo. Every commit is checked against it."

---

## SECTION 2: HANDS-ON — RESEARCHER WORKFLOW (7 minutes)

### Login & Onboarding (2 minutes)

**[Project login screen]**

> "Dr. Patel is a new assistant professor at IIT Gandhinagar. She gets credentials from the admin. First login."

**[Login as researcher_user]**

> "Her dashboard shows: her publications, her grants, her citation metrics, and a query box. Nothing else. She cannot see her colleagues' salaries. She cannot see government budget allocations. She sees exactly what she needs."

### Query 1 — Discovery (2 minutes)

**[Type query]**: *"Who is working on perovskite solar cells in Gujarat?"*

**Talking points while processing:**
- "Intent classification: 'perovskite solar cells' = topic, 'Gujarat' = geography, 'who' = researcher list"
- "The router sends this to the text-to-SQL skill"
- "SQL generated: `SELECT r.name, r.institute, COUNT(p.pub_id) FROM researchers r JOIN publications p ON r.researcher_id = p.researcher_id WHERE p.keywords LIKE '%perovskite%' AND r.state = 'Gujarat' GROUP BY r.researcher_id`"
- "But wait — Dr. Patel is Tier 1. The SQL gets wrapped with RBAC filters. She only sees public papers and her own papers."

**[Response arrives]**

> "Three researchers. Dr. Shah at IIT Gandhinagar — 4 public papers. Dr. Mehta at MSU Baroda — 2 public papers. Dr. Patel herself — 1 paper, still under review."

> "Notice: Dr. Patel sees her own under-review paper. She doesn't see Dr. Shah's under-review paper. RBAC at work."

### Query 2 — Collaboration (2 minutes)

**[Type query]**: *"I want to collaborate on battery research. Who has complementary expertise?"*

**Talking points:**
- "This is a complex query. The DAG planner breaks it into subqueries:"
  - "Subquery A: Find battery researchers in Gujarat"
  - "Subquery B: Find researchers with complementary skills (materials characterization, electrochemistry)"
  - "Subquery C: Check which of these have open collaboration slots"
- "Three SQL queries, one merged response"

**[Response arrives]**

> "Dr. Shah has characterization expertise but no electrochemistry. Dr. Banerjee at IISc has electrochemistry but is in Bangalore. Dr. Kumar at IIT Gandhinagar has both and has an open collaboration slot."

### Query 3 — Self-Assessment (1 minute)

**[Type query]**: *"How do my citation metrics compare to peers in my field?"*

**Talking points:**
- "Anonymized aggregation. She sees percentile ranks, not raw names."
- "The system calculates: citations per year, h-index trajectory, field-normalized impact"

**[Response arrives]**

> "75th percentile for career stage. Above average but not exceptional. Suggestion: consider industry collaboration — your field has high commercialization potential."

---

## SECTION 3: HANDS-ON — GOVERNMENT WORKFLOW (7 minutes)

### Login & Context (1 minute)

**[Login as gov_user]**

> "Mr. Rao is a program officer at DST-SERB. He manages ₹50 crore in annual grants. He needs to justify every rupee to the Parliamentary Standing Committee."

### Query 4 — Accountability (2 minutes)

**[Type query]**: *"Show me return on investment for nanotechnology grants in 2023"*

**Talking points:**
- "This query joins four tables: grants, publications, patents, and industry_collaborations"
- "The DAG planner recognizes this as a 'mixed_summary' — needs both SQL aggregation and narrative synthesis"
- "Government tier has access to PII: exact grant amounts, researcher names, institution details"

**[Response arrives]**

> "₹12 crore distributed to 23 projects. 47 publications. 3 patents filed. 2 industry partnerships initiated. ROI metric: 0.39 publications per lakh rupee."

> "Compare to 2022: 0.31 publications per lakh. Improvement of 26%."

### Query 5 — Anomaly Detection (2 minutes)

**[Type query]**: *"Which institutes received high funding but produced zero patents in 5 years?"*

**Talking points:**
- "This is a policy-critical query. The system flags it as 'sensitive' and adds extra audit logging"
- "The response includes a warning: 'This query may affect funding decisions. Please verify with secondary sources.'"

**[Response arrives]**

> "Three institutes identified. [Names redacted in demo for privacy]. Recommendation: schedule review meetings."

### Query 6 — Predictive Intelligence (2 minutes)

**[Type query]**: *"Based on publication trends, which research areas will peak in 2026?"*

**Talking points:**
- "This goes beyond SQL. The system uses time-series analysis on publication counts"
- "It also queries the vector DB for emerging topics not yet in structured tables"
- "RAG + SQL hybrid response"

**[Response arrives]**

> "AI-generated drug discovery: 340% growth in publications. Solid-state batteries: 180% growth. Quantum error correction: 95% growth. Recommendation: increase funding allocation for AI-drug discovery by 25%."

---

## SECTION 4: HANDS-ON — INDUSTRY WORKFLOW (5 minutes)

### Login & Value Proposition (1 minute)

**[Login as industry_user]**

> "Ms. Gupta is the open innovation lead at Reliance New Energy. Her budget: ₹10 crore for academic partnerships. Her problem: finding the right academic partner fast."

### Query 7 — Partner Discovery (2 minutes)

**[Type query]**: *"Find research groups with hydrogen storage expertise and existing industry partnerships"*

**Talking points:**
- "Industry tier sees: technology readiness levels, patent families, collaboration history, contact details"
- "Industry tier does NOT see: government funding amounts, grant rejection history, salary information"
- "Sovereign firewall in action"

**[Response arrives]**

> "IIT Madras — Metal Hydride Group. 5 patents. 2 active industry partnerships. TRL 6. Contact: Dr. Krishnan."

> "IISc Bangalore — Carbon Nanotube Group. 3 patents. 1 active partnership. TRL 4. Open to new partnerships."

### Query 8 — Technology Landscape (2 minutes)

**[Type query]**: *"What is the patent landscape for solid oxide fuel cells in India?"*

**Talking points:**
- "Patent analysis requires structured SQL + unstructured RAG"
- "SQL: count patents by assignee, year, technology subclass"
- "RAG: retrieve recent patent abstracts for context"
- "Merged synthesis"

**[Response arrives]**

> "78 patents filed 2020-2025. Top assignees: CSIR (23), IIT Bombay (12), BHEL (8). Technology trend: moving from planar to tubular designs. White space opportunity: intermediate-temperature SOFCs for distributed generation."

---

## SECTION 5: ARCHITECTURE DEEP DIVE (5 minutes)

### The LangGraph Pipeline (2 minutes)

**[Show diagram or `src/orchestration/` code]**

> "Every query flows through a 6-node LangGraph pipeline:"

1. **Router** — Intent classification + tier checking
2. **Planner** — DAG generation for multi-step queries
3. **Executor** — SQL execution + RAG retrieval (parallel)
4. **Synthesizer** — LLM mesh generates natural language
5. **Verifier** — Citation check + fact verification
6. **Audit** — Event logged to Merkle chain

> "Each node is stateful. If the synthesizer fails, we retry with a different provider. If the verifier finds missing citations, it flags the response. Nothing proceeds without validation."

### The LLM Mesh in Detail (2 minutes)

**[Show `src/config/llm_config.py` — the mesh code]**

> "Six providers. Not six API keys — six independent clients. Each with its own circuit breaker."

> "Health-weighted routing: score = success_rate / average_latency. A provider that fails 3 times in 5 minutes is automatically removed from rotation for 30 seconds. Then it gets a half-open test. If it passes, it's back."

> "Complexity-based racing: simple queries race 2 providers. Complex queries race 3. The first to return wins. The losers are cancelled."

> "Budget: 15 seconds total for cloud. If both providers timeout, local LLM. If local fails, rule-based. Three-tier cascade. Zero downtime."

### The Audit Chain (1 minute)

**[Show `.audit/chain.jsonl` — actual log entries]**

> "Every line is JSON. Every line has: timestamp, user, action, data hash, previous hash."

> "The Merkle root is published every 1000 events. We can verify the entire chain in one hash comparison."

> "Tamper detection: if I change line 5,001, the hash on line 5,002 doesn't match. The verification fails. We know exactly where the corruption happened."

---

## SECTION 6: Q&A (1 minute reserved, extend if needed)

### Deep Technical Questions

**"How do you handle schema evolution?"**
> "Alembic migrations. Version-controlled. Every schema change is a migration file. Rollback tested before deployment."

**"What about GDPR / DPDP compliance for foreign collaborators?"**
> "Foreign collaborators are Tier 1 — researcher level. They see only public data and their own data. No PII. No government data. DPDP Section 12 covers research exemptions."

**"Can researchers opt out?"**
> "Yes. Consent dashboard. One click. Data disappears from all queries within 24 hours. The audit chain records the opt-out event, but not the data itself."

**"What about data quality?"**
> "Three layers: (1) Schema constraints — no nulls where forbidden, foreign keys enforced. (2) Validation rules — email formats, ORCID checksums. (3) Drift detection — if publication counts drop 50% month-over-month, we flag potential ingestion failure."

**"How much does this cost to run?"**
> "Development: MacBook + Docker. Production estimate: ₹2 lakh/month for 500K researchers — single PostgreSQL instance, Qdrant cluster, 2 app servers. Scaling linearly."

---

## CLOSING (30 seconds)

> "NRG is not a product. It's infrastructure. Like UPI for payments, like Aadhaar for identity — NRG is for research intelligence."

> "Built by Indian academics. For Indian academics. On Indian infrastructure."

> "The code is open. The data is sovereign. The future is ours."

**[Pause. Open for questions.]**

---

## DEMO EQUIPMENT CHECKLIST

- [ ] Laptop with server running
- [ ] Second screen or projector
- [ ] Backup laptop with identical setup
- [ ] Printed leave-behinds (pitch deck, architecture diagram)
- [ ] QR code to GitHub repo
- [ ] Water

---

## CONTINGENCY: IF SYSTEM FAILS MID-DEMO

1. **Mesh fails** → Show local LLM fallback → "This is the sovereign cascade working as designed"
2. **Local LLM fails** → Show rule-based fallback → "Zero downtime guarantee"
3. **Database slow** → Show pre-cached responses from text file
4. **Complete crash** → Switch to backup laptop
5. **No backup** → Show screen recordings + architecture slides
