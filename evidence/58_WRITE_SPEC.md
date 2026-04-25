# Write Spec — Feature Specification
**Date:** 2026-04-25
**Skill:** `.claude/skills/write-spec/SKILL.md`

---

## Applying Write Spec to NRG's Next Feature

### Example: Text-to-SQL Accuracy Improvement

Since Text-to-SQL is the highest-priority gap (7/17 → 17/17), let's write a spec for it.

---

## Feature: Text-to-SQL Accuracy Improvement to 17/17

### Problem Statement

NRG's Text-to-SQL pipeline currently achieves only 7/17 correct on Dhairya's benchmark (41%). This means researchers querying the database get wrong or incomplete results more than half the time. Wrong SQL queries erode trust in the system and defeat the purpose of natural language database access.

**Who experiences this:** All 3 persona types (researcher, government, industry) when they ask complex analytical questions.
**Cost of not solving:** System unusable for its core purpose; demo fails professor validation.

---

### Goals

1. **Achieve 17/17 correct** on Dhairya's benchmark queries (100% accuracy)
2. **Reduce average response time** from 7.2s to under 5s
3. **Maintain zero PII leakage** through SQL injection vectors
4. **Preserve audit chain integrity** — every query must be logged
5. **Pass external AI audit** — independent validation of accuracy

---

### Non-Goals

1. **Schema expansion to 58 tables** — out of scope for this sprint (separate initiative)
2. **RAG pipeline improvements** — Text-to-SQL is separate from vector search
3. **Frontend UI changes** — query interface is adequate
4. **LLM model replacement** — current models are sufficient with better prompts

---

### User Stories

**Researcher Persona:**
- "As a researcher, I want to ask 'What patents were filed in the last quarter by institutions in Karnataka?' so that I can get accurate SQL results without learning SQL syntax"
- "As a researcher, I want to see citations in my results so I can verify the data source"

**Government Persona:**
- "As a government analyst, I want to ask 'What is the total FDI investment across all states for 2024?' so I get correctly aggregated data"

**Industry Persona:**
- "As an industry analyst, I want to ask 'What startups were recognized in the biotech sector?' so I can build competitive intelligence reports"

---

### Requirements

**Must-Have (P0):**
- [ ] Improve schema hints to cover all 17 Dhairya query patterns
- [ ] Add CTE templates for complex aggregations (GROUP BY with HAVING)
- [ ] Implement completeness validator to catch missing columns
- [ ] Fix 5 wrong query patterns (identified in SQL_IMPROVEMENT_PLAN.md)
- [ ] Add query context awareness (table relationships, foreign keys)

**Nice-to-Have (P1):**
- [ ] Self-correction loop — run generated SQL through validator before returning
- [ ] Explain SQL in plain language alongside results
- [ ] Query history to learn from user's query patterns

**Future Considerations (P2):**
- [ ] Support for PostgreSQL 58-table schema (depends on dev environment update)
- [ ] Multi-turn clarification when query is ambiguous
- [ ] Visual SQL builder for complex queries

---

### Success Metrics

**Leading Indicators:**
- Text-to-SQL accuracy: 7/17 → 17/17 (measure per sprint)
- Response time: 7.2s → <5s (measure per query)
- Validator catch rate: % of bad SQL caught before user sees it

**Lagging Indicators:**
- User satisfaction (if feedback system added)
- Error rate in production queries
- Support tickets about wrong data

---

### Open Questions

| Question | Who Answers |
|----------|-------------|
| Should we optimize for Dhairya's specific queries or generalize? | Engineering + Professor |
| How do we validate against production schema when dev has only 18 tables? | DevOps |
| What is the acceptable response time budget for complex queries? | Product |

---

### Timeline Considerations

- **Hard deadline:** Before next external audit / demo
- **Dependencies:** Schema hints update, CTE template library
- **Phasing:** Phase 1 (fix 5 wrong patterns) → Phase 2 (improve response time) → Phase 3 (validate 17/17)

---

## Skill Application Evidence

This document applies the write-spec skill to create a feature specification for NRG's highest-priority gap.

**Evidence of skill application:**
- Problem statement grounded in data (7/17 benchmark)
- 5 goals with measurable outcomes
- 4 non-goals to prevent scope creep
- User stories for all 3 personas
- P0/P1/P2 requirements with acceptance criteria
- Leading and lagging success metrics
- Open questions with tagged owners

**The spec follows the PRD structure from SKILL.md Section 83-280.**