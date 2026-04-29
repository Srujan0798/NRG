---
name: Source Verification Discipline
description: Cited claims must expose source type, freshness, independent confirmation, confidence, and disputed status before they are treated as verified answers
type: feedback
---

NRG answers can cite SQL rows, internal knowledge, public references, or future
external sources. Any cited claim must be inspectable enough that a reviewer can
see why the answer should be trusted.

**Rule:**

1. Every major claim needs a traceable source: SQL row/source table, official
   source, academic source, industry source, or named secondary source.
2. Classify source reliability before trusting the claim:
   - Primary: official documents, government reports, academic papers, source
     database rows, or original records.
   - Strong secondary: industry whitepapers, established news, named expert
     analysis, or company filings.
   - Context only: company marketing pages, technical blogs, community posts, or
     forums. These can support context but should not carry an important claim
     alone.
   - Caution: anonymous, undated, old, unverifiable, or copied material.
3. Score confidence from evidence, not tone:
   - High: official/primary source or multiple independent credible sources.
   - Medium: credible source with partial confirmation or minor uncertainty.
   - Low: single source, old source, anecdotal source, or unresolved conflict.
4. Track freshness. Current policy, funding, people, rankings, market, and
   institutional facts require recent verification. Historical facts should be
   labelled as historical.
5. Flag disputed claims instead of smoothing conflicts. If sources disagree,
   state the disagreement and avoid one-sided certainty.
6. Prefer source diversity for external claims. No single secondary source
   should carry an important conclusion alone.
7. Verification metadata should include source ID or URL, title, publisher or
   author when available, language, source type, reliability class, source date
   or fetched-at date, evidence type, independent confirmation count,
   confidence, and disputed/uncertain status.
8. For multilingual sources, keep the source language visible and avoid hiding
   uncertainty introduced by translation or transliteration.
9. If the source chain is weak, the answer must downgrade confidence or ask for
   clarification rather than presenting a polished but unsupported answer.

**Why:** Deep research prompts are too broad for the NRG app, but the source
verification logic is central. A professor's assistant will trust a concise
answer only if citations are traceable and weak claims are visibly marked.

**How to apply:**

- Backend answer contracts should carry verification metadata alongside
  citations.
- Source proof UI should expose confidence and disputed/uncertain labels without
  turning the result screen into a long research document.
- Acceptance should reject cited claims that lack source type, reliability
  class, freshness, language when relevant, or a clear confidence reason.

**Source:** MiniMax `deep-research-10x` and `deep-research-agent` reviewed
2026-04-29; kept as source verification discipline, not as a standalone broad
research skill.
