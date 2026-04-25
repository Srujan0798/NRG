# NRG Demo Script — 3-Minute Sovereign AI Demo

> **Timing:** Exactly 3 minutes. Rehearse to ±5s.
> **Audience:** Government/sponsor. Senior but non-technical.
> **Goal:** "This works, it's sovereign, it's ready."

---

## Setup — 15 seconds
**Before demo starts:**
```bash
# Terminal 1 — API
kubectl port-forward svc/api 8000:8000 &
# OR if local:
.venv/bin/python -m uvicorn src.api.main:app --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```
Open: http://localhost:3000

---

## SCENE 1: Login + Multi-Tier — 45 seconds

**[0:00]** Open browser at http://localhost:3000
- Show the login screen with 3 persona tiles

**[0:05]** "NRG serves three tiers — Researcher, Government, Industry. Each sees only what they're cleared for."

Click **Tier 1 — Researcher** → Login as `researcher_user` / `researcher-pass`

**[0:15]** Dashboard loads. Point to researcher-focused UI (left nav, search bar, stats panels).

**[0:25]** "Tier 1 sees full researcher details — name, institution, h-index, contact."

Click persona switcher (top-right avatar) → **Tier 2 — Government**

**[0:35]** Login as `gov_user` / `government-pass`

**[0:40]** "Tier 2 sees only aggregated statistics. No individual names. Fully anonymized per DPDP-2023."

Click persona switcher → **Tier 3 — Industry**

**[0:45]** Login as `industry_user` / `industry-pass`

**[0:50]** "Tier 3 sees institution names and research areas — no personal data, no contact info."

**[0:55]** Switch back to Tier 1 Researcher for the query demo.

---

## SCENE 2: Natural Language Query — 60 seconds

**[1:00]** Clear query box. Type:

```
find robotics researchers in Gujarat
```

**[1:05]** Press Enter. Show streaming response appearing.

**[1:15]** "Plain English. No SQL. The system writes the query, executes it, and returns a cited answer — in seconds."

**[1:20]** Point to the answer format: structured results with citation superscripts `[1][2]`.

**[1:30]** "Every claim is backed by source data. Let's verify."

Click citation **[1]**.

**[1:40]** Drawer opens showing:
- Paper/publication title
- Year and venue
- Author names
- Excerpt from source

**[1:45]** Close drawer.

**[1:50]** "That's C3 — Citation Accuracy. Every answer is verifiable."

---

## SCENE 3: Multi-Hop Query — 45 seconds

**[1:50]** Clear box. Type:

```
Compare AI research output between Gujarat and Karnataka over the last 5 years
```

**[1:55]** Submit. Show that it runs TWO parallel sub-queries (Gujarat + Karnataka) and synthesizes a comparison.

**[2:05]** "This is a multi-hop query — two states, five years, aggregated. Our Two-Brain planner decomposes it, races both branches, then synthesizes a combined answer."

**[2:10]** Show the comparison table/chart in the answer.

**[2:15]** "That's the architecture working — Planner → Router → Executor → Synthesizer."

---

## SCENE 4: Audit Chain Verification — 30 seconds

**[2:20]** Open new tab or navigate to `/audit/verify`

**[2:25]** "Every query is logged. Every log is chained with HMAC-SHA256. The chain is immutable and can be cryptographically verified."

Show: `Chain valid: True, Events: [count], Last hash: [hash]`

**[2:35]** "That's C2 — Audit Integrity. Tamper-evident, non-repudiation."

---

## CLOSE — 15 seconds

**[2:40]**

"Sovereign AI for Indian research."

"600 GB corpus. Fully on Indian soil."

"DPDP-2023 compliant. Audit-chain sealed."

"NRG — ready for national deployment."

**[2:50]** Stop recording.

---

## Expected Outcomes Checklist

| Check | Pass Criteria |
|-------|-------------|
| Login (T1/T2/T3) | All 3 tiers login without error |
| Query response | < 5s for simple query |
| Citations | ≥1 citation shown per answer |
| Multi-hop | Two sub-queries shown in answer |
| Tier separation | T2/T3 answers anonymized |
| Audit verify | `chain valid: True` shown |
| No 404s | Zero broken UI elements |

---

## Backup Triggers (if demo fails)

| Symptom | Fix |
|---------|-----|
| Login 500 | Restart API: `kubectl rollout restart deploy/api` |
| Query timeout | Check Qdrant: `localhost:6333/dashboard` |
| Citations empty | Verify DB has data: `sqlite3 nrg_research.db "SELECT COUNT(*) FROM publications"` |
| Graph blank | Check vector index: `scripts/vector_drift_check.py` |
| Chain invalid | Run: `python scripts/audit_rebuild.py --rebuild` |
