# NRG Demo Script — 15-Minute Deep Dive

**Audience:** Professor + 2-3 research students (technical but not necessarily engineers)  
**Duration:** 15 minutes  
**Goal:** Show capability + architecture + sovereignty principles

---

## PHASE 1: THE PROBLEM (2 minutes)

> "India produces 1.5 million STEM graduates every year. We have 1,043 universities, 42,000 colleges, and some of the world's best research institutes. But here's the problem:"

**[Pause]**

> "A DST-SERB program officer in Delhi wants to know which materials science labs in Gujarat received funding last year. Right now, they send emails. They wait a week. They get Excel sheets with different formats from every institute. They copy-paste. They make mistakes."

> "A Tata Steel R&D manager wants to find an academic partner for battery research. They search Google Scholar. They find papers from MIT, Stanford, TUM. They don't know that IIT Gandhinagar has a solid-state battery group with 8 patents and 3 industry partnerships."

> "NRG fixes this. One query. One second. Sovereign data."

---

## PHASE 2: THREE TIERS LIVE (5 minutes)

### Tier 1 — Researcher (90 seconds)

**[Login as researcher_user]**

> "Dr. Sharma logs in. She's Tier 1 — researcher. Her JWT token has `scope: own_and_public`. She can see her own grants, her own papers, and anonymized aggregates. She cannot see that DST-SERB gave ₹3 crore to her competitor at IIT Delhi. She cannot see that Tata Steel is funding battery research down the hall."

**[Run Query]**: *"What are the top research areas in materials science?"*

**Talking points while waiting:**
- "The router analyzes her intent — 'materials science', 'top areas', 'aggregation'"
- "It generates a SQL query against our structured database"
- "The LLM mesh synthesizes natural language from the results"

**[Response arrives]**

> "See the citations? Every claim has a `[cite:structured:N]` marker. Click it, you get the raw row. This is reproducible research intelligence."

### Tier 2 — Government (2 minutes)

**[Login as gov_user]**

> "Same database. Completely different view. The government token has `scope: full_tier_access`. The system checks IP whitelisting — this terminal is pre-approved."

**[Run Query]**: *"Show me funding efficiency by institute — grant amount vs publication output"*

**Talking points:**
- "This is the query no Excel sheet can answer. We're joining three tables: `innovation_grant_from_govt`, `publications`, and `researcher_institute_mapping`"
- "The DAG planner breaks this into subqueries, executes them, and merges results"

**[Response arrives]**

> "IIT Gandhinagar: ₹8.2 crore funding, 147 publications. Ratio: 18.3 lakhs per paper. Compare to the national average..."

**[Run Query]**: *"Which researchers have industry patents but no government grants?"*

> "This is policy intelligence. These researchers are innovating without public support. They should be on DST-SERB's radar."

**[Show audit_event_id]**

> "And every query is permanently logged. Event `b1a231eb...` — SHA-256 hash, chained to the previous event. If someone tampered with this log, the hash chain breaks. We can prove it in court."

### Tier 3 — Industry (90 seconds)

**[Login as industry_user]**

> "Tata Steel R&D. They want battery researchers. They want patent landscapes. They want to know: who is collaboration-ready?"

**[Run Query]**: *"Show me battery research groups with open industry collaboration"*

**Talking points:**
- "Notice they don't see government funding amounts. Sovereign firewall."
- "But they see collaboration history, technology readiness levels, and patent families"

**[Response arrives]**

> "IIT Gandhinagar Solid-State Battery Group. 3 industry partnerships. 8 patents. 2 open collaboration slots. Contact: Dr. Patel."

---

## PHASE 3: THE SOVEREIGN AI STACK (5 minutes)

### Layer 1 — Data Sovereignty (90 seconds)

**[Show database schema or `nrg_research.db` structure]**

> "All data lives on Indian infrastructure. Right now, SQLite — we'll migrate to PostgreSQL. But the principle is: no AWS, no GCP, no Azure for production. Bare metal in Indian data centers. DPDP Act 2023 compliant."

**[Show `src/data/schema/`]**

> "12 normalized tables. Researchers, publications, grants, patents, funding records, collaborations. Every foreign key is enforceable. No orphan data."

### Layer 2 — Access Sovereignty (90 seconds)

**[Show `src/auth/rbac_policy.yaml` or equivalent]**

> "Three tiers, but the policy engine is extensible. Want a 'visiting scholar' tier that can only read public papers for 30 days? One YAML entry. Want a 'RTI officer' tier that can query but not export? One YAML entry."

**[Show JWT token decoded]**

> "The token itself carries the tier: `tier: 2`, `scope: full_tier_access`, `groups: [government]`. The API doesn't trust the client — it re-validates every request against the policy engine."

### Layer 3 — AI Sovereignty (2 minutes)

**[Show `src/config/llm_config.py` — SovereignLLMMesh]**

> "This is the Sovereign LLM Mesh. Six providers. Health-weighted routing. Circuit breakers."

> "Primary: Minimax — Chinese provider, but our data doesn't leave our server. We send prompts, get responses. No training data leakage."

> "Fallback: NVIDIA — American, but again, API-only. No data retention."

> "If both cloud providers fail — and they do, about 30% of the time in our tests — we fall back to local LLM. llama.cpp running Gemma 2B on this MacBook. 30 seconds instead of 12, but it works offline."

> "If even that fails — rule-based ASCII tables. Zero downtime. Guaranteed."

**[Show the cascade in code]**

```python
cloud LLM → local LLM → rule-based
```

> "We call this the 'sovereign cascade'. India cannot depend on foreign AI infrastructure. We must have local fallbacks that work without internet."

### Layer 4 — Audit Sovereignty (90 seconds)

**[Show `.audit/chain.jsonl` or audit log]**

> "387,886 audit events. Every login, every query, every LLM call, every database read."

> "Merkle tree structure. Each event hashes the previous event's hash. Tamper one event, every subsequent hash changes. We detect corruption in O(1)."

**[Show `src/audit/` code]**

> "This isn't logging. This is non-repudiation. In court, we can prove that Dr. Sharma queried battery research at 2:47 PM on April 25. We can prove the response she received. We can prove nobody modified it afterward."

---

## PHASE 4: Q&A HANDLING (3 minutes)

### Expected Question: "Why not just use Google Scholar?"

> "Google Scholar indexes papers. It doesn't know that DST-SERB funded this research. It doesn't know that Tata Steel is the industry partner. It doesn't know the researcher's tier or what they're authorized to see. NRG is not a search engine. It's a sovereign intelligence layer."

### Expected Question: "What about privacy?"

> "DPDP Act 2023, Section 12: consent for research purposes. Every researcher in this database has given explicit consent. They can withdraw it — and their data disappears from all queries within 24 hours. The audit chain keeps the event that they withdrew, but not their data."

### Expected Question: "Can this scale?"

> "Right now: 5,615 researchers, 12,000 publications, SQLite, single server. Production target: 500,000 researchers, 2 million publications, PostgreSQL with read replicas, Qdrant cluster for vectors, Redis for caching. The architecture is designed for horizontal scaling."

### Expected Question: "Who maintains this?"

> "Open-source. MIT license. Hosted on GitHub. But the sovereign instance — the one with real government data — runs on Indian infrastructure, maintained by a consortium of IITs and IISc. Not a startup. Not a foreign company. Indian academia maintaining Indian academic data."

---

## POST-DEMO: LEAVE-BEHIND

Give them:
1. `NRG_PITCH_DECK.md` (from `pitch/`)
2. `DEMO_SCRIPT_PROFESSOR_WALKTHROUGH.md` (5-min version)
3. GitHub repo link
4. Your contact

---

## TIMING CHEAT SHEET

| Phase | Time | Cumulative |
|-------|------|------------|
| Opening problem statement | 2 min | 2 min |
| Three tiers live demo | 5 min | 7 min |
| Sovereign AI stack deep dive | 5 min | 12 min |
| Q&A | 3 min | 15 min |
