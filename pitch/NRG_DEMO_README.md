# NRG Demo Video — Filming Instructions

## Purpose

Produce a 3-minute demo video showcasing the National Research Graph platform for stakeholder audiences (IIT-GN, Ministry, NIC, MeitY).

**Critical:** Must be filmed on **sovereign staging environment** — never on local development setup.

---

## Pre-Filming Checklist

### Environment
- [ ] Deploy to sovereign staging server (`staging.nrg.iitgn.ac.in`)
- [ ] Verify all services running: `curl http://staging.nrg.iitgn.ac.in:8000/health/all`
- [ ] Confirm audit chain integrity: `curl http://staging.nrg.iitgn.ac.in:8000/audit/verify`
- [ ] Clear any test data; use realistic demo data
- [ ] Disable rate limiting for filming duration

### Cast (3 Personas)
| Persona | Login | Role | What to Demo |
|---------|-------|------|--------------|
| **Researcher** | `researcher_user` | Tier 1 | Full profile search, collaboration graph, publication records |
| **Government** | `govt_user` | Tier 2 | Aggregated stats, state-level trends, funding allocation view |
| **Industry** | `industry_user` | Tier 3 | Anonymized researcher names + research areas only |

### Test Queries to Prepare
```text
1. "Find AI researchers in Gujarat with h-index above 30"
2. "Which institutions got the most funding in 2025?"
3. "Show me potential collaborators for quantum computing research"
4. "Compare robotics research output between Gujarat and Karnataka"
5. "Who filed the most patents in semiconductor domain?"
```

---

## Video Script (3 Minutes Total)

### MINUTE 1: RESEARCHER PERSONA (0:00 – 1:00)

**Opening shot:** Browser at login page. VO: "This is the National Research Graph — India's sovereign AI platform for research discovery."

**Action 1:** Log in as `researcher_user`. VO: "Researchers get full access — names, publications, contact information, lab details."

**Action 2:** Type query: `"AI researchers in Gujarat"`. VO: "A researcher asks a question in plain English..."

**Action 3:** Show results. VO: "...and gets back verified, cited results. Every claim is traceable."

**Action 4:** Click a citation. VO: "Click any result to see the exact source — this paper, this dataset, this funding record."

**Action 5:** Switch to Graph View. VO: "The collaboration graph shows who works with whom — essential for finding research partners."

**Action 6:** Show Export button. VO: "Export to CSV, PDF, or Citation Manager."

**Transition:** Fade to Government dashboard login.

---

### MINUTE 2: GOVERNMENT PERSONA (1:00 – 2:00)

**Opening shot:** Login as `govt_user`. VO: "Government users see aggregated statistics — no individual-level data."

**Action 1:** Show dashboard overview. VO: "The government dashboard shows state-level research capacity at a glance."

**Action 2:** Type query: `"Compare funding allocation across states"`. VO: "Policy question: where is funding being allocated?"

**Action 3:** Show comparison table with bar chart. VO: "Gujarat, Maharashtra, Karnataka — with trend lines over 5 years."

**Action 4:** Click into a specific state's detail. VO: "Drill down into any state to see institution-level breakdown."

**Action 5:** Show Audit tab. VO: "Every query is logged in the tamper-proof audit chain — accountability built in."

**Action 6:** Highlight DPDP compliance badge. VO: "Full DPDP 2023 compliance — consent, purpose limitation, right to erasure."

**Transition:** Fade to Industry dashboard login.

---

### MINUTE 3: INDUSTRY PERSONA + SECURITY (2:00 – 3:00)

**Opening shot:** Login as `industry_user`. VO: "Industry partners see researcher names and research areas only — no personal data."

**Action 1:** Type query: `"Who can solve our semiconductor R&D problem?"`. VO: "An industry user asks: who has the expertise we need?"

**Action 2:** Show anonymized results. VO: "Names and areas only — fully DPDP-compliant. No email, no phone, no PII."

**Action 3:** Show the data sovereignty statement. VO: "Critically: no data leaves Indian servers. This is sovereign infrastructure."

**Action 4:** Show architecture diagram (from pitch deck). VO: "The 5-layer architecture ensures data never leaves the local boundary."

**Action 5:** Final shot: IIT-GN + MeitY logos together. VO: "Built at IIT Gandhinagar, deployed on government infrastructure. This is India's research OS."

**Closing:** Title card with contact info.

---

## Subtitle Requirements

### English Subtitles
- Required for all dialogue
- Font: OpenSans or similar sans-serif, minimum 24px equivalent
- Position: Bottom center, with sufficient contrast
- Timing: Sync to VO, appear 100ms before speech, disappear 200ms after
- Include speaker labels for VO sections

### Hindi Subtitles
- Required for Ministry/NIC/MeitY audiences
- Use accurate Hindi translations (not transliteration)
- Technical terms: use established Hindi equivalents where available
- Position: Same as English (below English subtitle or toggleable)

### Accessibility
- Include SDH (Subtitles for Deaf and Hard of hearing) version
- Add sound effect descriptions in brackets: [audit beep], [citation click], [graph render]
- Ensure color contrast ratio ≥ 4.5:1 for subtitle text

---

## Audio/Narration Guidelines

### VO Script Principles
1. **Keep it conversational** — not a corporate narration
2. **Explain the "why"** — not just "what you see"
3. **Stay factual** — no marketing superlatives
4. **3 personas, 3 distinct tones:**
   - Researcher: curious, discovery-focused ("Let me find...")
   - Government: analytical, policy-focused ("What does the data show?")
   - Industry: pragmatic, business-focused ("Who can solve our problem?")

### Narration Timing
| Segment | Duration | Allow Time For |
|---------|----------|----------------|
| Researcher demo | ~60s | User actions + results render |
| Government demo | ~60s | Dashboard load + chart render |
| Industry + Security | ~60s | Architecture diagram transitions |

### Audio Quality
- Background music: subtle, non-distracting (instrumental, low volume)
- No audio spikes during UI transitions
- Maintain consistent volume across all 3 minutes
- For Hindi VO: use professional Hindi voice-over artist

---

## Filming Setup Notes

### Camera/Recording
- Resolution: 1080p minimum, 4K preferred
- Frame rate: 30fps for screen recording, 60fps if mixing camera + screen
- Use a dedicated camera for presenter if including human in frame
- Screen recording software: OBS Studio (recommended, free)

### Browser Setup
- Use Chrome or Firefox in incognito/private mode
- Clear cache before filming
- Disable all extensions
- Set browser zoom to 100%
- Use a clean, uncluttered desktop background

### Staging Environment State
- Ensure demo data includes:
  - At least 50 researchers across 5 institutions
  - Publications, funding records, collaboration data
  - Realistic institution names (IIT Gandhinagar, IIT Bombay, etc.)
- Pre-warm the system: run 2-3 queries before filming to avoid cold-start delays

---

## Post-Production Notes

### Editing Checklist
- [ ] Trim all pauses > 2 seconds
- [ ] Ensure subtitle sync is accurate
- [ ] Add intro/title card (10s max)
- [ ] Add outro with contact info (5s max)
- [ ] Verify audio levels consistent throughout
- [ ] Generate Hindi subtitle track (SRT format)
- [ ] Export in MP4 (H.264) for universal compatibility

### Export Settings
- Resolution: 1920x1080 (1080p)
- Bitrate: 8-12 Mbps for HD
- Codec: H.264 (avc1)
- Audio: AAC 128kbps minimum
- Container: MP4

### Versioning
- `NRG_DEMO_v1.0_EN.mp4` — English version
- `NRG_DEMO_v1.0_HI.mp4` — Hindi version
- Store both on secure server with IIT-GN access controls

---

*Document version: 1.0*
*Last updated: 2026-04-24*
*For questions: comms@nrg.iitgn.ac.in*