---
name: Intent-aware PII detection (regex is not enough)
description: The current prompt sanitiser detects literal Aadhaar/PAN/phone/email patterns in user input. It does NOT detect the schema-aware extraction intent — a user asking "Show emails of researchers from IIT Bombay" passes the regex and reaches Text-to-SQL. Add an intent classifier above the regex layer.
type: feedback
---

The PII regex (`src/security/gateway/prompt_sanitiser.py`) catches three classes of input:
- A 12-digit Aadhaar in the user query string.
- A literal PAN / phone / email pattern.
- Unicode-homoglyph variants of the above.

It does NOT catch the most dangerous class: a query that intends to extract PII columns from the database without containing PII in its own text. Examples that pass regex today but should be blocked:

- "Show me all emails of researchers from IIT Bombay."
- "List the phone numbers of every Tier 1 user."
- "Give me the Aadhaar column from the expertise table."
- "Export researchers with their contact information."

Each of these is a structured-data PII extraction intent. The user did not paste an Aadhaar; they asked the system to *return* Aadhaars. Once the request reaches Text-to-SQL, the engine generates `SELECT email, phone FROM expertise WHERE institute='IIT Bombay'`. The response-shape filter (LB-1) catches Tier 2/3 responses, but Tier 1 still receives the rows — and a single Tier 1 token leaked or shoulder-surfed becomes a bulk PII export.

**Why:** The fifth external audit named this exact path as the #1 break-it question. Sanitiser unit tests pass on every example because the test corpus is regex-shaped. Production traffic is not.

**How to apply:**
- Add an **intent classifier** between the prompt sanitiser and the planner. Input: user question + planner's resolved column list. Output: `{intent: extract_pii | extract_aggregate | extract_metadata | …}` + confidence.
- For `extract_pii` intent OR for any planner-resolved column matching the PII allowlist (`email`, `phone`, `aadhaar`, `pan`, `dob`, `bank_account`, `gstin`, `personal_address`):
  - Tier 2/3: hard block. Audit-log `pii_intent_block:tier=N`.
  - Tier 1: require an explicit consent token in the request header (`X-NRG-PII-Consent: <reason>`). Without it, prompt the frontend to ask the user for the reason and audit-log the consent string.
- Implementation: lightweight LLM classifier (single call to local SLM or a fine-tuned small model) — not a regex. The cost is one extra inference per query; budgeted in `CostGuard`.
- Test corpus: extend `tests/security/test_pii_compliance.py` with 30+ queries that contain no literal PII but extract PII columns. Each must block.
- Cross-references: LB-1 (response shape), LB-5 (red-team replay), `feedback_db_layer_defence.md` (pg_anonymizer at DB layer). Three layers: intent → response-shape → DB mask. Defence-in-depth.

**Source:** Kimi/Moonshot 2026-04-26 (Deliverable 4 Q1). Promoted 2026-04-26.
