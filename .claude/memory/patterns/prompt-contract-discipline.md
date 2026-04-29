---
name: Prompt Contract Discipline
description: NRG model prompts must declare task, inputs, output schema, constraints, edge cases, parser behavior, and regression evidence before prompt changes are accepted
type: feedback
---

Prompt changes in NRG are code changes. They can break SQL generation, response
shape, tier safety, or answer confidence even when no Python or TypeScript file
changes.

**Rule:**

1. Every production-path model prompt must declare:
   - task the model owns
   - named input fields and source of each field
   - output schema with required keys, enum values, nullable fields, and limits
   - constraints: always, never, and uncertainty behavior
   - edge cases: empty input, ambiguity, conflicting context, missing data, and
     prompt injection
   - parser behavior for malformed, incomplete, or out-of-policy output
2. Prompt edits must start from failure evidence: exact prompt, input, actual
   output, expected output, and affected parser or downstream contract.
3. Make targeted edits. Preserve working prompt sections unless the failure
   evidence points at them.
4. Use examples only when they are representative of production inputs. Avoid
   toy examples that teach the wrong format.
5. Programmatic outputs must use schemas or templates strict enough for parsers.
   Free-form prose belongs after deterministic verification, not before.
6. After each prompt change, run a regression set: original failing input,
   normal case, edge case, and adversarial instruction.
7. If the prompt cannot reliably achieve the behavior, change the architecture:
   split the prompt chain, add retrieval, move logic into deterministic code, or
   ask for clarification instead of over-promising through wording.

**Why:** Prompt rewrites are tempting because they feel cheap. Without a
contract and regression evidence, they create silent wrong-answer risk and
schema drift.

**How to apply:**

- Backend changes touching Text-to-SQL, routing, synthesis, verification, or
  intent classification must include prompt contract evidence when prompts
  change.
- Reviews should reject "made prompt better" claims without failing input,
  expected output, parser behavior, and regression command output.
- Keep this separate from broad prompt-coaching advice; the NRG need is
  production prompt reliability.

**Source:** MiniMax `prompt-engineer` reviewed 2026-04-29; kept as prompt
contract discipline, not as a standalone broad prompt-writing skill.
