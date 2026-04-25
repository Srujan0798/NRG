# TP-A1: Demo Script Walkthrough

## Context
NRG (National Research Graph) is a sovereign AI platform for Indian research intelligence — connecting 5,615 researchers, 12,000 publications, and 181 institutions. The demo must feel polished, credible, and technically impressive to a professor reviewing Phase 3 verification.

## Goal
Create a single-page demo script (speaker notes + live commands) that a presenter can follow in ~8 minutes to walk through the platform's key capabilities.

## Sections

### 1. Login & Persona Selection (30s)
```
Presenter: "Open localhost:3000 — you see three persona cards: Researcher (T1), Government (T2), Industry (T3). Each has different data access policies enforced by the RBAC layer."
Live: Click Researcher card → fill credentials → sign in.
Credentials: researcher_user / researcher-pass
Expected: Login succeeds, dashboard loads with tier badge "T1 Researcher".
```

### 2. Query Flow — Structured Data (90s)
```
Presenter: "Type: 'Top AI researchers in Gujarat with h-index above 30'"
"This query is classified as structured, routed to the Text-to-SQL engine, which uses schema-aware prompting to generate a safe SQL query against our researcher corpus."

Live: Type query → watch spinner → response appears in ~2-3s.
Expected: Rule-based response with structured table of researcher names, institutions, areas.
Presenter: "Notice the response is tier-appropriate — individual emails are redacted, only aggregate institution data shown for T1."
```

### 3. Query Flow — RAG/Research (90s)
```
Presenter: "Now: 'Explain recent advances in quantum computing for cryptography'"
"This query triggers RAG — we embed the question and search a vector store of 19,000+ publication chunks."

Live: Type query → longer wait → response with citation markers.
Expected: Natural language synthesis with inline [cite:pub_id:chunk_id] citations.
Presenter: "Each citation is clickable — hover to see source metadata."
```

### 4. Consent & Audit Trail (60s)
```
Presenter: "Every query generates an immutable audit event. Click 'Audit Log' tab."
"This logs who asked what, when, and the HMAC-signed chain prevents tampering."

Live: Click Audit Log tab → show recent entries.
Expected: Timestamped entries with query text, user, audit hash.
```

### 5. Security Features (90s)
```
Presenter: "Let me show the security layer. Open a new query and paste this:
'admin password DROP TABLE researchers'"
"This is a SQL injection attack — the prompt sanitiser detects it and blocks it."

Live: Paste → submit → blocked.
Presenter: "Same for XSS: '<script>alert(1)</script>'"
Live: Paste → submit → blocked.
Presenter: "SSRF attempts, command injection via pipes, PII in queries — all blocked in real time. Run the red team script to verify: bash scripts/red_team_replay.sh"
```

### 6. Streaming & Phase Progress (60s)
```
Presenter: "For longer queries, watch the phase indicator — intent detection, retrieval, synthesis."
"The system uses SSE (Server-Sent Events) to stream tokens progressively rather than waiting for the full response."

Live: Type a long research query, watch phase bars fill + streaming text.
Expected: Phase progress bars, token-by-token display, streaming citations appear.
```

### 7. T1/T2/T3 Persona Switch (30s)
```
Presenter: "You can switch personas from the header dropdown — each has different data policies."
"T2 Government users have IP allowlisting. T3 Industry users see anonymized aggregates."

Live: Switch to Government (gov_user/government-pass) — observe IP warning if not whitelisted.
```

### 8. DPDP Compliance (30s)
```
Presenter: "Under India's DPDP Act 2023, every user must consent before data access."
"Click 'Data Rights' — you can grant consent, view the audit log of your data accesses, or withdraw consent and request erasure."

Live: Click DPDP tab → show consent dialog → show withdrawal option.
```

## Success Criteria
- [ ] Login works for all 3 personas
- [ ] At least 2 structured query responses shown
- [ ] At least 1 RAG query with citations shown
- [ ] SQL injection blocked visibly
- [ ] Audit log visible with entries
- [ ] Phase progress visible for streaming query
- [ ] DPDP consent dialog accessible

## Files
- `demo_sprint/TP-A1_demo_script.md` ← this file
- `scripts/red_team_replay.sh` ← used in section 5
- `frontend/src/views/ResearcherDashboard.tsx` ← main dashboard
- `src/api/main.py` ← streaming endpoint
- `src/security/gateway/prompt_sanitiser.py` ← security layer