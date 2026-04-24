# NRG UAT Results — Handover Test Template

## User Acceptance Testing for IIT-GN Handover

**Version:** 1.0  
**Date:** 2026-04-24  
**Classification:** Internal — UAT  
**Purpose:** To be filled during live UAT session with IIT-GN participants  

---

## UAT Session Information

| Field | Value |
|-------|-------|
| **Scheduled Date** | [To be scheduled] |
| **Duration** | 1 hour |
| **Location** | IIT Gandhinagar or virtual |
| **Facilitator** | NRG Development Team |
| **Notetaker** | [IIT-GN representative] |

---

## Participant Roster

| # | Persona | Name | Role | Tier |
|---|---------|------|------|------|
| 1 | **Professor** | [Name] | IIT-GN Research Lead | Tier 1 |
| 2 | **Ministry Liaison** | [Name] | MeitY/DST Representative | Tier 2 |
| 3 | **Industry Partner** | [Name] | R&D Industry Executive | Tier 3 |

---

## Test Methodology

### Pre-Seeded Queries by Persona

Each persona receives **10 pre-seeded queries** to execute. These queries should be:
- Realistic use cases for their role
- Covering the full range of NRG capabilities
- Including edge cases and multi-hop queries

### Evaluation Criteria

| Criterion | Description | Score (1-5) |
|-----------|-------------|--------------|
| **Time to Answer** | How quickly did the system respond? | 1= >10s, 5= <1s |
| **Quality Score** | Was the answer correct and complete? | 1=wrong, 5=perfect |
| **Citation Accuracy** | Were citations correct and sufficient? | 1=none, 5=excellent |
| **UI Friction** | How easy was it to use? | 1=confusing, 5=seamless |

### Success Threshold

- **Minimum:** 8/10 queries pass (80% success rate)
- **Target:** 9/10 queries pass (90% success rate)
- **Superior:** 10/10 queries pass (100% success rate)

---

## Persona 1: Professor (Tier 1 Researcher)

### Profile

- **Background:** IIT-GN professor in Computer Science
- **Goal:** Find collaborators, track publications, analyze research trends
- **Access Level:** Full researcher data including personal contact info

### Pre-Seeded Queries

| # | Query | Expected Behavior | Time (s) | Quality | Citations | Notes |
|---|-------|-------------------|----------|---------|-----------|-------|
| 1 | "Find robotics researchers in Gujarat" | List of researchers with details | | | | |
| 2 | "Who has published the most on machine learning in the last 5 years?" | Ranked list with counts | | | | |
| 3 | "Show me researchers working on hydrogen fuel cells" | List with affiliation and h-index | | | | |
| 4 | "Compare AI research output between Gujarat and Karnataka over the last 5 years" | Multi-hop: two states, 5 years, aggregated comparison | | | | |
| 5 | "Find my profile and show my publications" | Own data retrieval | | | | |
| 6 | "Which institutions have the highest collaboration rate?" | Aggregated institutional stats | | | | |
| 7 | "Show me labs working on quantum computing" | Lab list with capabilities | | | | |
| 8 | "What is the funding trend for renewable energy research?" | Time-series funding analysis | | | | |
| 9 | "Find researchers who have patents in semiconductor design" | Researcher + patent linkage | | | | |
| 10 | "Show the knowledge graph for deep learning" | Graph visualization | | | | |

### UAT Notes

```
Observations:

Query 1:
- 
-

Query 2:
-
-

[Continue for each query]
```

### Overall Assessment: Professor

| Metric | Result |
|--------|--------|
| Queries Passed | /10 |
| Average Time to Answer | seconds |
| Average Quality Score | /5 |
| Average Citation Accuracy | /5 |
| Average UI Friction Score | /5 |
| **Overall Rating** | /5 |

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Professor | | | ☐ |
| NRG Facilitator | | | ☐ |

---

## Persona 2: Ministry Liaison (Tier 2 Government)

### Profile

- **Background:** MeitY or DST official responsible for research funding allocation
- **Goal:** Analyze state-wise research capacity, identify funding gaps, track national trends
- **Access Level:** Aggregated statistics, anonymized summaries, no personal data

### Pre-Seeded Queries

| # | Query | Expected Behavior | Time (s) | Quality | Citations | Notes |
|---|-------|-------------------|----------|---------|-----------|-------|
| 1 | "Show state-wise research funding for the last 3 years" | Aggregated funding by state | | | | |
| 2 | "Which states have the most publications in AI?" | State ranking | | | | |
| 3 | "What percentage of research is in healthcare vs engineering?" | Domain distribution | | | | |
| 4 | "Show the growth trend of IIT publications over 10 years" | Time-series chart | | | | |
| 5 | "Which institutions have the highest patents filed?" | Institutional patent ranking | | | | |
| 6 | "Compare funding allocation between government and private institutions" | Segmented analysis | | | | |
| 7 | "What is the research output per crore of funding?" | ROI analysis | | | | |
| 8 | "Show the geographic distribution of renewable energy research" | State map visualization | | | | |
| 9 | "Which research areas have grown the fastest in 5 years?" | Trend analysis | | | | |
| 10 | "Generate a summary report of national research capacity" | Multi-section report | | | | |

### UAT Notes

```
Observations:

Query 1:
-

[Continue for each query]
```

### Overall Assessment: Ministry Liaison

| Metric | Result |
|--------|--------|
| Queries Passed | /10 |
| Average Time to Answer | seconds |
| Average Quality Score | /5 |
| Average Citation Accuracy | /5 |
| Average UI Friction Score | /5 |
| **Overall Rating** | /5 |

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Ministry Liaison | | | ☐ |
| NRG Facilitator | | | ☐ |

---

## Persona 3: Industry Partner (Tier 3 Industry)

### Profile

- **Background:** R&D director at a mid-size Indian tech company
- **Goal:** Find potential research partners, identify technology experts, scout innovation
- **Access Level:** Names and research areas only — no personal data, no detailed stats

### Pre-Seeded Queries

| # | Query | Expected Behavior | Time (s) | Quality | Citations | Notes |
|---|-------|-------------------|----------|---------|-----------|-------|
| 1 | "Who works on electric vehicle battery technology?" | Researcher names + areas | | | | |
| 2 | "Find institutions with semiconductor research capability" | Institution names + focus | | | | |
| 3 | "Who are the top experts in machine learning?" | Names + research areas | | | | |
| 4 | "Show research groups working on quantum computing" | Group/institution names | | | | |
| 5 | "Which institutions collaborate on robotics research?" | Collaboration network (no personal data) | | | | |
| 6 | "Find researchers in graphene-related technologies" | Research area matches | | | | |
| 7 | "Who has expertise in chip design and verification?" | Technical expertise mapping | | | | |
| 8 | "Show the top 10 research institutions in India by area" | Institutional ranking | | | | |
| 9 | "Which researchers publish on 5G and next-gen communications?" | Domain expertise | | | | |
| 10 | "Find industry-academia collaboration examples in AI" | Collaboration patterns | | | | |

### UAT Notes

```
Observations:

Query 1:
-

[Continue for each query]
```

### Overall Assessment: Industry Partner

| Metric | Result |
|--------|--------|
| Queries Passed | /10 |
| Average Time to Answer | seconds |
| Average Quality Score | /5 |
| Average Citation Accuracy | /5 |
| Average UI Friction Score | /5 |
| **Overall Rating** | /5 |

### Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Industry Partner | | | ☐ |
| NRG Facilitator | | | ☐ |

---

## Summary Results

### Overall UAT Results

| Persona | Queries Passed | Avg Time | Avg Quality | Avg Citations | Avg UI |
|---------|---------------|----------|-------------|---------------|--------|
| Professor (Tier 1) | /10 | | /5 | /5 | /5 |
| Ministry (Tier 2) | /10 | | /5 | /5 | /5 |
| Industry (Tier 3) | /10 | | /5 | /5 | /5 |
| **OVERALL** | /30 | | /5 | /5 | /5 |

### Pass/Fail Determination

| Threshold | Result |
|-----------|--------|
| ≥24/30 queries pass (80%) | 🟢 PASS — Proceed to production |
| <24/30 queries pass | 🟡 CONDITIONAL — Fix critical issues, re-test |
| <18/30 queries pass (60%) | 🔴 FAIL — Major rework required |

### Critical Issues Found

| Issue | Severity | Persona Affected | Description |
|-------|----------|------------------|-------------|
| [Issue 1] | P0/P1/P2 | | |
| [Issue 2] | | | |
| [Issue 3] | | | |

### Recommendations

```
1. [Recommendation 1]

2. [Recommendation 2]

3. [Recommendation 3]
```

---

## Final Sign-Off

| Role | Name | Date | Decision | Signature |
|------|------|------|----------|-----------|
| Professor | | | ☐ APPROVE ☐ CONDITIONAL ☐ REJECT | |
| Ministry Liaison | | | ☐ APPROVE ☐ CONDITIONAL ☐ REJECT | |
| Industry Partner | | | ☐ APPROVE ☐ CONDITIONAL ☐ REJECT | |
| NRG Development Lead | | | ☐ APPROVE ☐ CONDITIONAL ☐ REJECT | |

---

## Post-UAT Action Items

| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

*Document version: 1.0*  
*Last updated: 2026-04-24*  
*Template for UAT session — to be completed during live testing*