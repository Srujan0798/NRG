# NRG Demo Script

## 10-Minute Sponsor Demo

### Setup (30 seconds)

```bash
cd /Users/srujansai/Desktop/NRG
bash scripts/launch_dashboard.sh
```

---

### Segment 1: Login (1 minute)

**Narrative:** "NRG serves three personas with tier-appropriate access."

**Actions:**
1. Open http://localhost:3000
2. Show persona selector (Researcher, Government, Industry)
3. Login as `researcher_user` / `researcher-pass`
4. **Expected:** Dashboard loads with research-focused UI

---

### Segment 2: Natural Language Query (2 minutes)

**Narrative:** "Researchers ask questions in plain English."

**Actions:**
1. Type: "find robotics researchers in Gujarat"
2. Submit query
3. **Expected:** 
   - Response appears with formatted answer
   - Citations shown as superscripts
   - Provenance badge shows "synth=local_llama"

---

### Segment 3: Citations (2 minutes)

**Narrative:** "Every claim is backed by source evidence."

**Actions:**
1. Click first citation `[cite:...]`
2. **Expected:** Drawer opens showing:
   - Paper title and year
   - Author names
   - Chunk excerpt
3. Close drawer

---

### Segment 4: Graph View (2 minutes)

**Narrative:** "Visualize research networks and collaborations."

**Actions:**
1. Type: "machine learning" in topic field
2. Click "Visualize"
3. **Expected:** Graph renders with nodes (papers, authors, institutions)
4. Pan and zoom to show responsiveness
5. Click a node to filter answer panel

---

### Segment 5: Government Tier Demo (1.5 minutes)

**Narrative:** "Government sees only aggregated data."

**Actions:**
1. Logout
2. Login as `gov_user` / `gov-pass`
3. **Expected:** Dashboard shows aggregate statistics
4. Query: "total researchers by state"
5. **Expected:** Chart view, no individual researcher details

---

### Segment 6: Audit Verification (1 minute)

**Narrative:** "Every action is logged with tamper-proof chain."

**Actions:**
1. Login as admin
2. Navigate to /audit/verify
3. **Expected:** Shows `ok: true`, chain integrity verified
4. Show last sealed timestamp

---

### Close (30 seconds)

**Summary:**
- "Sovereign AI for Indian research"
- "600 GB corpus, fully compliant"
- "Ready for national deployment"

---

## Expected Outcomes

- Zero 404s
- All responses < 10 seconds
- Citations visible in all answers
- Graph renders non-empty
- Audit chain verifies
