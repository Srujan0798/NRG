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
| 1 | "How many IIT Gandhinagar publications were published in 2023, grouped by research area?" | Count and grouping by institution, year, and research area | | | | |
| 2 | "Which researchers at IIT Gandhinagar published on hydrogen catalysis between 2020 and 2024, and what are their email contacts?" | Tier 1 researcher details with citations and contact fields | | | | |
| 3 | "Show the top 10 Computer Science researchers by publication count since 2021, including institution, h-index, and recent paper titles." | Ranked researcher list with joined publication evidence | | | | |
| 4 | "Find researchers in Gujarat working on robotics who also have patents or funded projects." | Cross-table researcher, patent, and project linkage | | | | |
| 5 | "Which labs collaborate most often with researchers publishing in machine learning?" | Lab and researcher collaboration network summary | | | | |
| 6 | "Compare publication growth for IIT Gandhinagar, IIT Bombay, and IIT Madras from 2019 to 2024." | Multi-institution time-series comparison | | | | |
| 7 | "List researchers whose funding increased after they started publishing in renewable energy topics." | Joined funding and publication trend analysis | | | | |
| 8 | "Show co-author networks for quantum computing researchers and identify the most connected collaborator." | Collaboration graph with ranked connectivity | | | | |
| 9 | "Which institutions have researchers working at TRL 6 or above in semiconductor or chip design?" | Institution and TRL-stage join with researcher details | | | | |
| 10 | "For hydrogen research, show publications, active researchers, grants, patents, and likely collaboration opportunities." | Complex multi-hop synthesis across publications, people, funding, patents, and institutions | | | | |

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
| 1 | "Which states had the highest AI publication growth from 2020 to 2024?" | State-level aggregate trends only | | | | |
| 2 | "Compare total government innovation grant funding by institution type and year." | Aggregated funding by institution class and year | | | | |
| 3 | "Which institutes convert grants into patents most efficiently, grouped by state?" | Institution/state aggregate conversion ratios, no researcher PII | | | | |
| 4 | "Show the top research areas by national publication output and funding trend for the last five years." | National aggregate trend summary | | | | |
| 5 | "Which ministries or agencies appear most often in funded research collaborations?" | Agency collaboration counts without individual profiles | | | | |
| 6 | "Compare IIT, NIT, and private-university research output per crore of funding." | Institution-type ROI comparison | | | | |
| 7 | "Which states have strong renewable energy research but low patent commercialization?" | Aggregate state gap analysis | | | | |
| 8 | "Show aggregate TRL distribution by institute type for market-ready technologies." | TRL-stage histogram by institution class | | | | |
| 9 | "Identify national collaboration clusters between institutions in AI, healthcare, and clean energy." | Institution-level collaboration clusters only | | | | |
| 10 | "Generate a policy summary of underfunded high-output research areas without showing individual researcher details." | Policy-ready summary with anonymized aggregates | | | | |

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
| 1 | "Which institutions publicly publish the most work on electric vehicle battery technology?" | Public institution and topic summary only | | | | |
| 2 | "Find public collaboration opportunities in semiconductor design based on published papers and patents only." | Public publications and patent metadata only | | | | |
| 3 | "Which research groups publish on 5G or next-generation communications?" | Public group/institution names and research areas | | | | |
| 4 | "Show institutions with public patents or publications related to graphene applications." | Public patent/publication evidence only | | | | |
| 5 | "Which IITs have published work in robotics, and what topics do they focus on?" | Published topic summary by institution | | | | |
| 6 | "List public research areas where industry-academia collaboration is visible from publications or patents." | Public-domain collaboration patterns | | | | |
| 7 | "Find published papers since 2021 on hydrogen fuel cells and their affiliated institutions." | Publication metadata and institution affiliations | | | | |
| 8 | "Which institutions appear strongest in AI safety or trustworthy AI using public publication evidence?" | Public publication strength signal | | | | |
| 9 | "Show market-ready technology areas using only public patent and publication metadata." | Public metadata-based opportunity summary | | | | |
| 10 | "Summarize potential public-domain partners for quantum computing collaboration without grant or personal-contact data." | Tier 3-safe partner summary with restricted fields | | | | |

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
