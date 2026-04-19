# Synthesis Decision

**Status**: Accepted for Phase 1 PoC  
**Canonical source**: `Core_Idea_Clean.md`  
**Updated**: 2026-04-19

## Decision

NRG allows cloud LLM synthesis only through an explicit, minimized, sanitized evidence packet. Local SLM remains the offline/sovereign option, and rule-based synthesis remains the deterministic fallback.

Default behavior:

```text
CLOUD_SYNTHESIS_ALLOWED=false
```

When the flag is false, the synthesizer must not call a cloud LLM for either pre-verification or synthesis. When the flag is true, every cloud attempt must be auditable and must include only minimized evidence.

## Allowed Evidence Packet

Cloud synthesis may receive:

- User query.
- Bounded excerpts from retrieved evidence.
- Non-sensitive source identifiers.
- Title/year/topic-style metadata.
- Evidence counts and redaction counts.

Cloud synthesis must not receive:

- Raw DB dumps.
- Full documents or unrestricted abstracts.
- Emails, phone numbers, addresses, IDs, API keys, private keys, or secrets.
- Full schemas unrelated to the current query.
- Generated operational artifacts.

## Audit Requirements

Every cloud synthesis attempt records:

- Mode.
- Model/provider.
- Evidence counts.
- Redaction/minimization metadata where available.
- Whether `cloud_synthesis_used` was true.

## Fallback Order

1. Cloud LLM, only when `CLOUD_SYNTHESIS_ALLOWED=true`.
2. Local SLM, when available.
3. Rule-based synthesis.

This decision supersedes older local-only or production-complete claims. Any future move to fine-tuned local-only synthesis should be written as a new ADR after it is implemented and tested.
