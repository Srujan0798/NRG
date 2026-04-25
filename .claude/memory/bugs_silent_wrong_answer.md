---
name: Silent wrong-answer is the biggest failure mode
description: A SQL query that parses, executes, and returns plausible-but-wrong rows is worse than a query that errors — the synthesizer formats it confidently and the user trusts it. Engine must detect anomaly and refuse to ship.
type: feedback
---

NRG's most dangerous failure mode is not "system errors" or "system shows no results" — it is **the system confidently returns a wrong-but-plausible answer with full audit citation**. The user has no way to know the answer is wrong until they cross-check externally, by which time the damage to trust is done.

Two independent external audits (Grok 2026-04-25, Claude-as-Principal-Engineer 2026-04-26) named this as the **single biggest risk**:
- Grok: "Latent Text-to-SQL failure patterns will surface on 600 GB volume or ambiguous questions, producing empty/wrong results that destroy trust in the first 60 seconds."
- Claude: "The system will confidently provide a wrong answer to an ambiguous or cross-domain question, and nobody in the room will know it's wrong until later."

**Mechanism:** the LLM emits SQL that *parses* and *executes*. The DB returns rows. The synthesizer formats them into prose. The verifier currently checks citation faithfulness only — not result plausibility. Five concrete classes of silent failure already documented in the Dhairya audit:
1. JOIN on the wrong column (Q7 — joined patents_details.institute when the correct key was combined_ipo_patent_data.applicants).
2. CAST of TEXT-typed column to INT silently zeros rows that don't match the expected format (total_credit_score "X:Y").
3. GROUP BY losing dimension — aggregate has correct shape, wrong values.
4. Synonym mismatch on a value column ("TRL 9" vs "Level 9") — returns empty.
5. Cross-domain follow-up loses active_domain and queries the wrong table (Q10, Q12).

**Why:** Sanitiser unit tests, Dhairya 43/43 regression, and red-team tests do not catch this class — they prove the engine CAN emit good SQL on the patterns we tested, not that it REFUSES to ship a wrong answer when the LLM stumbles on a new pattern.

**How to apply:**
- Treat any "DONE" claim on a Text-to-SQL change suspiciously unless an anomaly-detection layer is wired into the verifier and proven on adversarial cases. See LB-7 (`protocols/52_LB7_SEMANTIC_SQL_SELF_CORRECTION.md`).
- The `answer_confidence` field in /query response is mandatory after LB-7 lands. Frontend must render a clarification prompt for `low_clarify` instead of an answer.
- Acceptable behaviour when the engine is unsure: ask the user a clarifying question, or return "I cannot answer this with the data I have — here is what I tried and why it failed". Unacceptable: render a confident wrong answer with citation.
- New external audits will likely name this risk again. Point them at LB-7 evidence first; if the audit still names it as open, the implementation is incomplete regardless of test counts.

**Source:** Two external audits 2026-04-25 / 2026-04-26 — promoted to permanent rule 2026-04-26.
