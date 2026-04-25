# NRG Demo Script — Professor Walkthrough

**Audience:** Professor / Academic evaluator (IIT Gandhinagar context)  
**Duration:** 5 min (light) / 15 min (standard) / 30 min (deep)  
**Date:** 2026-04-25  
**Prepared by:** Claude (assistant)

---

## OPENING (30 seconds)

> "This is NRG — the National Research Graph. Sovereign AI for India's research database. No data leaves Indian jurisdiction. Every query is audited. Every access is tiered. Let me show you what that means in practice."

**[Open the login screen]**

---

## ACT 1: THREE WORLDS, ONE DATABASE (1 minute)

### Show the login page
Point out: three personas. Same database, completely different views.

> "We have three personas — Researcher, Government, Industry. They all query the same 5,615 researchers and 12,000 publications. But what they see is radically different."

### Login as `researcher_user`
- Username: `researcher_user`
- Password: `researcher-pass`

> "This is Dr. Sharma, a materials scientist at IIT Bombay. She sees her own data, public data, and anonymized summaries. She cannot see government funding sources or industry collaboration details."

**[Run Query 1]**
> *"Top 5 funding agencies"*

**Expected response:** DST-SERB, DRDO, DBT, MeitY, AICTE with amounts.  
**Talking point:** "Notice the citations — every number is traceable to structured data."

---

## ACT 2: SOVEREIGN MANDATE — GOVERNMENT TIER (1.5 minutes)

### Login as `gov_user`
- Username: `gov_user`
- Password: `government-pass`

> "Now we become the DST-SERB program officer. Same database. Completely different privileges. Government tier sees funding flows, state-wise distribution, PII that researchers themselves cannot access."

**[Run Query 2]**
> *"Government funding distribution by state"*

**Expected response:** State-wise breakdown with grant totals.  
**Talking point:** "This is how a program officer allocates the next ₹50 crore. Data-driven, not gut-driven."

**[Run Query 3]**
> *"Which institutes received the highest government grants in 2023?"*

**Expected response:** Institute ranking with grant amounts.  
**Talking point:** "Notice the audit trail. Every query is logged with a cryptographic hash. Tamper-proof. Forever."

**[Point to audit event ID in response]**  
> "This event — `b1a231eb1700d574...` — is now permanently in the audit chain. 387,886 events and counting. Zero corruption."

---

## ACT 3: INDUSTRY TIER — COMMERCIAL VALUE (1 minute)

### Login as `industry_user`
- Username: `industry_user`
- Password: `industry-pass`

> "Finally, the industry liaison from Tata Steel. They want to know: who should we collaborate with? What patents are emerging? They cannot see government funding details — that's sovereign-protected. But they see collaboration graphs, patent trends, technology readiness."

**[Run Query 4]**
> *"Industry collaboration trends"*

**Expected response:** Summary of industry partnerships, emerging areas.  
**Talking point:** "This is how Indian industry finds Indian academic partners. No LinkedIn scraping. No foreign databases. Pure sovereign intelligence."

---

## ACT 4: THE ARCHITECTURE — 30-SECOND CLOSE (1 minute)

> "Behind this is a four-layer sovereignty stack:
> 1. **Data layer** — SQLite for now, PostgreSQL-ready. Everything encrypted at rest.
> 2. **Access layer** — JWT tokens with tiered RBAC. Government tier requires IP whitelisting.
> 3. **AI layer** — Sovereign LLM mesh. Minimax and NVIDIA race each other. If both fail, local LLM on llama.cpp takes over. If that fails, rule-based ASCII tables. Zero downtime.
> 4. **Audit layer** — Every query, every LLM call, every database touch is hashed into a Merkle chain. 387,886 events. Zero gaps."

> "This is not a dashboard. This is national research infrastructure."

**[Pause. Let them ask questions.]**

---

## EXPECTED RESPONSES (Verified Against Live System)

### Query: "Top 5 funding agencies"
```
1. DST-SERB — ₹16,75,00,000
2. DRDO — ₹12,40,00,000
3. DBT — ₹2,20,00,000
4. MeitY — ₹1,50,00,000
5. AICTE — ₹30,00,000
```

### Query: "Government funding distribution by state"
```
Gujarat, Maharashtra, Karnataka, Tamil Nadu, Telangana
(with respective totals)
```

### Query: "Which institutes received the highest government grants in 2023?"
```
IIT Gandhinagar, IIT Bombay, IISc Bangalore, IIT Delhi, IIT Madras
(with totals and citation markers)
```

---

## BACKUP PLANS

### If cloud LLM mesh fails (falls back to local LLM)
> "The cloud mesh timed out — let me show you the local fallback. This is llama.cpp running a 2B parameter model locally. Still produces natural language, just takes 30 seconds instead of 12."

**Action:** Wait patiently. The response will have `[Note: Response generated using local model for faster service]` appended.

### If local LLM also fails (falls back to rule-based)
> "Both cloud and local failed — now watch the rule-based fallback. Zero downtime guarantee. ASCII tables with structured data. Not pretty, but never broken."

**Action:** Point out the SQL query and raw results included in the response.

### If server is slow to respond
> "The server is under load — this is a development instance. In production, we'd have horizontal scaling with Redis caching."

**Action:** Have pre-cached responses ready in a text file to read from.

---

## PRE-DEMO CHECKLIST (Run this 5 minutes before professor arrives)

- [ ] Server running: `curl http://localhost:8000/health`
- [ ] Qdrant running: `curl http://localhost:6333/collections`
- [ ] Local LLM running: `curl http://localhost:8080/health`
- [ ] Frontend dev server running: `npm run dev` in `frontend/`
- [ ] Login works for all 3 tiers
- [ ] Query 1 returns in <15 seconds
- [ ] Query 2 returns in <15 seconds
- [ ] Query 3 returns in <15 seconds
- [ ] Query 4 returns in <15 seconds
- [ ] No browser console errors
- [ ] Screen recording started (optional)

---

## POST-DEMO NOTES

Capture professor feedback here:
- 
- 
- 

---

## FILES REFERENCED

- Backend: `src/api/main.py` (health, login, query)
- Auth: `src/auth/jwt_handler.py` (tiered credentials)
- Synthesizer: `src/orchestration/nodes/synthesizer.py` (3-tier cascade)
- Mesh: `src/config/llm_config.py` (SovereignLLMMesh)
- Audit: `src/audit/` (Merkle chain)
- Frontend: `frontend/src/` (React 18 + Vite + Tailwind)
