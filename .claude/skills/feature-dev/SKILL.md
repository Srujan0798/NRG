---
name: feature-dev
description: End-to-end feature development — codebase exploration, architecture design with trade-offs, parallel agent review, and implementation. Use when implementing any new feature. Runs parallel code-explorer and code-architect agents to understand and design before touching code.
model-agnostic: true
sub-skills: explore · design · implement · review
---

# Feature Dev

Seven phases. Each phase has a gate. No skipping.

---

## Phase 1 — Capture Intent

1. Understand the request. If unclear, ask:
   - What problem does this solve?
   - What should it do?
   - Any constraints or requirements?
2. Summarize and confirm with user before proceeding.

**For NRG — ask before Phase 2:**
- Which tier(s) does this touch? (T1/T2/T3)
- Does it touch PII columns?
- Does it change the audit chain?
- What's the evidence requirement?

---

## Phase 2 — Codebase Exploration

Launch 2–3 parallel code-explorer agents, each targeting a different aspect:
- "Find features similar to [feature] and trace their implementation"
- "Map the architecture and abstractions for [feature area]"
- "Analyze the current [relevant module], trace through the code fully"

After agents return: **read the key files they identify** before moving on. Don't skip this.

Present findings summary.

---

## Phase 3 — Clarifying Questions

**Do not skip this phase.**

From the codebase findings, identify: edge cases, error handling, integration points, scope boundaries, performance needs, backward compatibility.

Present all questions in one list. Wait for answers before designing.

If user says "whatever you think is best" — provide recommendation and get explicit confirmation.

---

## Phase 4 — Architecture Design

Launch 2–3 parallel code-architect agents with different focuses:
- **Minimal**: smallest change, maximum reuse of existing code
- **Clean**: maintainability, elegant abstractions
- **Pragmatic**: speed + quality balance

Present to user:
- Summary of each approach
- Trade-offs comparison
- Your recommendation with reasoning

**Ask user which approach to use.** Do not implement until chosen.

**For NRG mini-spec (required before implementing auth/RBAC/audit/schema changes):**
```
FEATURE: [name]
CHANGES:
  - src/api/[file].py: [what changes]
  - tests/[path]/test_[file].py: [new tests]
ACCEPTANCE CRITERIA:
  - [ ] [testable criterion]
RBAC IMPACT: [tiers affected, response shape changes]
EVIDENCE REQUIRED: [what proof of completion looks like]
```

---

## Phase 5 — Implementation

**Do not start without explicit user approval.**

1. Read all relevant files from earlier phases
2. Implement following the chosen architecture
3. Follow codebase conventions strictly
4. Write tests first (TDD) — see `.agents/skills/test-driven-development/SKILL.md`
5. Run affected test suite — no regressions

**For NRG:** Every implementation must:
- Not break the 6 Quality Bar constraints
- Pass `forbidden_vocab_check.sh` if touching any `.md` files
- Include evidence file if it closes a K-* protocol item

---

## Phase 6 — Quality Review

Launch 3 parallel review agents:
- **Simplicity/DRY**: duplication, over-engineering, unnecessary abstractions
- **Correctness**: bugs, edge cases, error handling, silent failures
- **Conventions**: project patterns, naming, RBAC enforcement, audit logging

Present findings grouped by severity:
- Critical (must fix before merge)
- Important (should fix)
- Suggestions (optional)

Ask user what to address. Do not silently discard critical issues.

---

## Phase 7 — Summary

Mark all todos complete. Document:
- What was built
- Key decisions made
- Files modified
- Evidence committed to `evidence/YYYY-MM-DD/`
- Next steps

---

## For NRG Feature Types

| Feature type | Extra gate |
|---|---|
| New API endpoint | Tier isolation curl test — T1/T2/T3 must return different shapes |
| Schema change | `pytest tests/data/test_schema_parity.py` green |
| Auth/security | `pytest tests/security/` green + adversarial test that FAILS without the fix |
| Frontend component | 3-tier dashboard render check + 375px mobile |
| Data pipeline | Row count validation + idempotency re-run test |

---

## Anti-Patterns

- Starting implementation before Phase 3 questions are answered
- Skipping the parallel explorer agents and guessing at architecture
- Implementing before user approves the architecture choice
- Claiming DONE without evidence file
