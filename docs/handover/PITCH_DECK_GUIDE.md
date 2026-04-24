# Pitch Deck Guide — NRG

## Converting NRG_PITCH_DECK.md to PDF/PPT + Customization for Different Audiences

**Version:** 1.0
**Date:** 2026-04-24
**Classification:** Internal — Communications

---

## 1. Converting to PDF

### Option A: Markdown → PDF (Recommended)

Use a Pandoc-based workflow for highest quality:

```bash
# Install pandoc if not present
brew install pandoc  # macOS
# or: sudo apt install pandoc  # Ubuntu

# Install required LaTeX packages (for PDF engine)
# macOS:
brew install --cask mactex

# Convert with custom template
pandoc pitch/NRG_PITCH_DECK.md \
  --from=markdown \
  --to=pdf \
  --output=pitch/NRG_PITCH_DECK.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V colorlinks=true \
  -V linkcolor=blue \
  --standalone
```

**Note:** The pitch deck uses ASCII-art diagrams in code blocks. For PDF output, these render as monospace preformatted text. They are designed to be readable in terminal/markdown format.

### Option B: Markdown → HTML → PDF

If LaTeX is unavailable:

```bash
pandoc pitch/NRG_PITCH_DECK.md --from=markdown --to=html --standalone --css=style.css -o pitch/NRG_PITCH_DECK.html

# Then print to PDF via browser:
# Chrome: Ctrl+P → Save as PDF
# Firefox: Ctrl+P → Save as PDF
```

### Option C: Google Slides Import

1. Copy each slide's ASCII diagram into a text box in Google Slides
2. Use a monospace font (Courier New) for the diagram sections
3. Keep the text-based format for the body
4. Add visual elements (shapes, icons) via Google Slides UI
5. Recommended: use the **Slides → Download as PPTX** after editing

---

## 2. Converting to PowerPoint (PPT)

### Manual Conversion (Recommended for Accuracy)

1. Create a new PowerPoint presentation
2. For each slide in `NRG_PITCH_DECK.md`:
   - Copy the ASCII box diagram to a PowerPoint text box
   - Use a monospace font (Consolas or Courier New)
   - Set text box to fixed size matching slide
3. Add transitions and animations as desired

### Automated (Pandoc)

```bash
pandoc pitch/NRG_PITCH_DECK.md \
  --from=markdown \
  --to=pptx \
  --output=pitch/NRG_PITCH_DECK.pptx
```

Note: Pandoc's PPTX output is basic. For production-grade slides, manual conversion or Google Slides import is recommended.

### Slide Structure Reference

| Slide # | Title | Content Type | Priority |
|---------|-------|--------------|----------|
| 1 | Title | Statement + tagline | Opening |
| 2 | The Problem | Bullet list | Core |
| 3 | The Opportunity | Bullet list + numbers | Core |
| 4 | The Solution | Architecture diagram | Core |
| 5 | 5-Layer Architecture | Layer diagram | Technical |
| 6 | 6-Node Pipeline | Flow diagram | Technical |
| 7 | Security Model | Security layers | Core |
| 8 | The 3 Personas | Comparison table | Core |
| 9 | Demo | Walkthrough | Core |
| 10 | Compliance | Checklist | Auditors |
| 11 | Data Sovereignty | Statement box | Core |
| 12 | Technology Stack | Table | Technical |
| 13 | Roadmap | Phase breakdown | Core |
| 14 | The Endgame | Architecture diagram | Vision |
| 15 | Impact Metrics | Numbers | Closing |

---

## 3. Audience Customization Notes

### 3.1 IIT-GN Faculty/Leadership

**Presentation length:** 20-25 minutes
**Tone:** Technical depth, research credibility

**Emphasis adjustments:**
- Slide 14 (Endgame/Fine-tuned Model): **Expand** — this is the vision that matters to researchers
- Slide 4 (Solution Overview): Include more technical architecture detail
- Slide 6 (6-Node Pipeline): Show the DAG planner in more detail
- Add: Current research collaborations and publications using NRG

**Skip or minimize:**
- Basic DPDP explanation (they know this)
- Simple security concepts

**Key message:** "NRG is built on solid research principles — LangGraph, RAG, fine-tuned models. This is the future of research infrastructure."

---

### 3.2 Ministry of Education / MHRD Officials

**Presentation length:** 15-20 minutes
**Tone:** Strategic, outcome-focused, national impact

**Emphasis adjustments:**
- Slide 3 (Opportunity): **Expand** — lead with the ₹400 Crore opportunity
- Slide 11 (Data Sovereignty): **Expand** — critical for government audiences
- Slide 13 (Roadmap): Show clear phases with funding milestones
- Add: Alignment with IndiaAI Mission and ANRF funding

**Skip or minimize:**
- Technical architecture details (6-node pipeline)
- Fine-tuned model technical explanations
- Deep technology stack (Kong, Qdrant, etc.)

**Key message:** "India needs sovereign AI infrastructure for its research data. NRG delivers this — ₹400 Crore unlocks national-scale deployment."

---

### 3.3 NIC (National Informatics Centre) Engineers

**Presentation length:** 30-40 minutes
**Tone:** Technical, implementation-focused, compliance-aware

**Emphasis adjustments:**
- Slide 5 (5-Layer Architecture): **Expand** — all layers
- Slide 12 (Technology Stack): **Expand** — full details
- Slide 7 (Security Model): Show full security layer breakdown
- Slide 10 (DPDP Compliance): Include clause-by-clause mapping
- Add: Integration points with existing NIC systems

**Skip or minimize:**
- High-level problem statement (they know it)
- Ministry-level strategic framing

**Key message:** "NRG is deployable on your infrastructure. Here's the architecture, the API contracts, the data intake protocol, and the operations runbook."

---

### 3.4 MeitY (Ministry of Electronics & IT)

**Presentation length:** 20-25 minutes
**Tone:** Security-first, compliance-focused, sovereign infrastructure

**Emphasis adjustments:**
- Slide 11 (Data Sovereignty): **Expand** — architecturally incapable of data exfiltration
- Slide 7 (Security Model): **Expand** — all 5 layers, DPDP compliance
- Slide 10 (DPDP Compliance): Full clause-by-clause attestation
- Slide 4 (Solution Overview): Emphasize Kong API Gateway, DLP capabilities

**Skip or minimize:**
- Fine-tuned model technical deep-dive
- Research collaboration graph specifics

**Key message:** "NRG is built with sovereign security at every layer. DPDP-compliant, architecturallyincapable of data leakage, audit-trailed end-to-end."

---

## 4. Presentation Best Practices

### General
- Start with Slide 1 (Title) — sets the tone
- Use speaker notes for all technical details you don't say aloud
- Keep one slide visible while discussing (not flipping through)
- Pause after each major section — allow Q&A

### Handling Q&A
- Slide 8 (3 Personas): Common question about data access levels
- Slide 11 (Data Sovereignty): Common question about cloud LLM usage
- Slide 10 (DPDP Compliance): Common question about Right to Grievance

### Timing Budget
| Section | Suggested Time |
|---------|----------------|
| Title + Problem | 2-3 min |
| Opportunity | 1-2 min |
| Solution Overview | 2-3 min |
| Architecture | 3-4 min |
| Security + Compliance | 3-4 min |
| Demo walkthrough | 3-5 min |
| Roadmap + Endgame | 2-3 min |
| Q&A / Discussion | 5-10 min |
| **Total** | **20-30 min** |

---

## 5. Quick Reference Card

Print this as a single-page reference before presenting:

```
NRG PITCH DECK — QUICK REFERENCE

CONVERTING:
  Markdown → PDF:  pandoc pitch/NRG_PITCH_DECK.md --to=pdf -o pitch/NRG_PITCH_DECK.pdf
  Markdown → PPTX:  pandoc pitch/NRG_PITCH_DECK.md --to=pptx -o pitch/NRG_PITCH_DECK.pptx

CUSTOMIZATION:
  IIT-GN:    More technical depth (endgame, architecture)
  Ministry:  Lead with ₹400Cr opportunity, sovereignty
  NIC:       Full technical stack, integration points
  MeitY:     Security + compliance emphasis

TIMING: 20-30 minutes (allow extra for Q&A)
```

---

*Document version: 1.0*
*Last updated: 2026-04-24*
*For questions: comms@nrg.iitgn.ac.in*